import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleReferrerWalletTransaction(models.Model):
    _name = 'sale.referrer.wallet.transaction'
    _description = 'Referrer Wallet Transaction'
    _order = 'create_date desc, id desc'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, index=True, readonly=True)
    source_invoice_id = fields.Many2one('account.move', string='Source Invoice', readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', readonly=True)
    accounting_move_id = fields.Many2one('account.move', string='Accounting Entry', readonly=True)
    reversal_of_id = fields.Many2one(
        'sale.referrer.wallet.transaction',
        string='Reversal Of',
        readonly=True,
        index=True,
    )
    amount = fields.Float(string='Amount', required=True, readonly=True, digits='Account')
    transaction_type = fields.Selection([
        ('earn', 'Earned'),
        ('spend', 'Spent'),
        ('refund_reversal', 'Refund Reversal'),
        ('adjustment', 'Adjustment'),
    ], string='Type', required=True, readonly=True)
    state = fields.Selection([
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='posted', required=True, readonly=True)
    reference = fields.Char(string='Reference', readonly=True, index=True)
    odoo_ewallet_sync_state = fields.Selection([
        ('not_configured', 'Not Configured'),
        ('skipped', 'Skipped'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
    ], string='Odoo eWallet Sync', readonly=True, default='not_configured')
    odoo_ewallet_sync_note = fields.Char(string='Odoo eWallet Sync Note', readonly=True)

    _sql_constraints = [
        ('sale_referrer_wallet_transaction_reference_uniq', 'unique(reference)', 'Reference must be unique.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            transaction_type = vals.get('transaction_type')
            amount = vals.get('amount', 0.0)
            if transaction_type in ('spend', 'refund_reversal') and amount > 0:
                raise ValidationError(_("Spend or refund reversal transactions must use negative amounts."))
            if transaction_type in ('earn', 'adjustment') and amount < 0 and not vals.get('reversal_of_id'):
                raise ValidationError(_("Earn/adjustment transactions must use positive amounts unless they reverse another transaction."))
        records = super().create(vals_list)
        records.filtered(lambda rec: rec.state == 'posted')._sync_to_odoo_ewallet()
        return records

    def unlink(self):
        raise ValidationError(_("You cannot delete wallet transactions. Create an adjustment transaction instead."))

    def _sync_to_odoo_ewallet(self):
        if not self:
            return

        icp = self.env['ir.config_parameter'].sudo()


        LoyaltyCard = self.env.get('loyalty.card')
        LoyaltyProgram = self.env.get('loyalty.program')
        if not LoyaltyCard or not LoyaltyProgram:
            self.sudo().write({
                'odoo_ewallet_sync_state': 'skipped',
                'odoo_ewallet_sync_note': 'Loyalty models not available',
            })
            return

        program_id = int(icp.get_param('sale_referrer_ewallet.referrer_odoo_ewallet_program_id') or 0)
        program = LoyaltyProgram.browse(program_id).exists() if program_id else False

        balance_field = 'points' if 'points' in LoyaltyCard._fields else (
            'balance' if 'balance' in LoyaltyCard._fields else False
        )
        if not balance_field:
            self.sudo().write({
                'odoo_ewallet_sync_state': 'skipped',
                'odoo_ewallet_sync_note': 'No balance field on loyalty.card',
            })
            return

        for tx in self:
            try:
                domain = [('partner_id', '=', tx.partner_id.id)]
                if program and 'program_id' in LoyaltyCard._fields:
                    domain.append(('program_id', '=', program.id))

                card = LoyaltyCard.search(domain, limit=1)
                if not card:
                    create_vals = {'partner_id': tx.partner_id.id}
                    if program and 'program_id' in LoyaltyCard._fields:
                        create_vals['program_id'] = program.id
                    if 'code' in LoyaltyCard._fields:
                        create_vals['code'] = tx.reference or f"REFERRER-{tx.id}"
                    card = LoyaltyCard.sudo().create(create_vals)

                current_balance = card[balance_field] or 0.0
                card.sudo().write({balance_field: current_balance + tx.amount})
                tx.sudo().write({
                    'odoo_ewallet_sync_state': 'synced',
                    'odoo_ewallet_sync_note': f'Synced to loyalty.card {card.id}',
                })
            except Exception as exc:  # pylint: disable=broad-except
                _logger.exception('Failed to sync referrer wallet transaction %s to Odoo eWallet', tx.id)
                tx.sudo().write({
                    'odoo_ewallet_sync_state': 'failed',
                    'odoo_ewallet_sync_note': str(exc)[:255],
                })
