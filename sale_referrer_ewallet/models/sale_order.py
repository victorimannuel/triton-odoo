from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    referrer_partner_id = fields.Many2one('res.partner', string='Referrer', help="Partner who referred this sale.")
    
    referral_commission_percentage = fields.Float(
        string='Commission %',
        default=lambda self: float(self.env['ir.config_parameter'].sudo().get_param('sale_referrer_ewallet.commission_percentage', default=5.0))
    )
    referral_credit_amount = fields.Float(
        string='Credit Amount',
        compute='_compute_referral_credit_amount',
        store=True,
        readonly=False,
        help="Fixed amount of credit to grant to the referrer."
    )

    @api.depends('amount_untaxed', 'referral_commission_percentage', 'referrer_partner_id')
    def _compute_referral_credit_amount(self):
        for order in self:
            if order.referrer_partner_id:
                order.referral_credit_amount = order.amount_untaxed * (order.referral_commission_percentage / 100.0)
            else:
                order.referral_credit_amount = 0.0

    @api.constrains('referrer_partner_id', 'partner_id')
    def _check_referrer_not_customer(self):
        for order in self:
            if order.referrer_partner_id and order.referrer_partner_id == order.partner_id:
                raise ValidationError(_("The customer cannot be their own referrer."))

    def action_open_apply_credit_wizard(self):
        self.ensure_one()
        return {
            'name': 'Apply Credit',
            'type': 'ir.actions.act_window',
            'res_model': 'apply.referrer.credit.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.id},
        }

    def action_confirm(self):
        res = super().action_confirm()
        wallet_tx_model = self.env['sale.referrer.wallet.transaction']
        ICP = self.env['ir.config_parameter'].sudo()
        journal_id = int(ICP.get_param('sale_referrer_ewallet.referrer_journal_id') or 0)
        expense_account_id = int(ICP.get_param('sale_referrer_ewallet.referrer_expense_account_id') or 0)
        liability_account_id = int(ICP.get_param('sale_referrer_ewallet.referrer_liability_account_id') or 0)

        for order in self:
            # 1. Consume wallet credit (spend)
            credit_product = self.env.ref('sale_referrer_ewallet.product_product_referrer_credit', raise_if_not_found=False)
            if credit_product:
                redemption_lines = order.order_line.filtered(lambda l: l.product_id == credit_product and l.price_unit < 0)
                total_redemption = sum(abs(l.price_unit * l.product_uom_qty) for l in redemption_lines)
                if total_redemption > 0:
                    if order.partner_id.referrer_credit_balance < total_redemption:
                        raise ValidationError(_("Insufficient credit balance to confirm this order. Please adjust the credit amount."))

                    spend_reference = f"spend:{order.id}"
                    existing_spend = wallet_tx_model.search([('reference', '=', spend_reference)], limit=1)
                    if not existing_spend:
                        wallet_tx_model.create({
                            'partner_id': order.partner_id.id,
                            'sale_order_id': order.id,
                            'amount': -total_redemption,
                            'transaction_type': 'spend',
                            'state': 'posted',
                            'reference': spend_reference,
                        })

            # 2. Grant wallet credit (earn)
            if order.referrer_partner_id and order.referral_credit_amount > 0:
                earn_reference = f"earn_so:{order.id}"
                existing_earn = wallet_tx_model.search([('reference', '=', earn_reference)], limit=1)
                if not existing_earn:
                    move_id = False
                    if journal_id and expense_account_id and liability_account_id:
                        move_vals = {
                            'journal_id': journal_id,
                            'date': fields.Date.today(),
                            'ref': _('Referrer Commission: %s') % order.name,
                            'move_type': 'entry',
                            'line_ids': [
                                (0, 0, {
                                    'name': _('Commission Expense'),
                                    'account_id': expense_account_id,
                                    'debit': order.referral_credit_amount,
                                    'credit': 0.0,
                                }),
                                (0, 0, {
                                    'name': _('Commission Payable to %s') % order.referrer_partner_id.name,
                                    'account_id': liability_account_id,
                                    'partner_id': order.referrer_partner_id.id,
                                    'debit': 0.0,
                                    'credit': order.referral_credit_amount,
                                }),
                            ]
                        }
                        ac_move = self.env['account.move'].create(move_vals)
                        ac_move.action_post()
                        move_id = ac_move.id

                    wallet_tx_model.create({
                        'partner_id': order.referrer_partner_id.id,
                        'sale_order_id': order.id,
                        'amount': order.referral_credit_amount,
                        'transaction_type': 'earn',
                        'state': 'posted',
                        'accounting_move_id': move_id,
                        'reference': earn_reference,
                    })
        return res

    def action_cancel(self):
        res = super().action_cancel()
        wallet_tx_model = self.env['sale.referrer.wallet.transaction']
        ICP = self.env['ir.config_parameter'].sudo()
        journal_id = int(ICP.get_param('sale_referrer_ewallet.referrer_journal_id') or 0)
        expense_account_id = int(ICP.get_param('sale_referrer_ewallet.referrer_expense_account_id') or 0)
        liability_account_id = int(ICP.get_param('sale_referrer_ewallet.referrer_liability_account_id') or 0)

        for order in self:
            # Reverse spend
            spend_tx = wallet_tx_model.search([
                ('sale_order_id', '=', order.id),
                ('transaction_type', '=', 'spend'),
                ('state', '=', 'posted'),
            ], limit=1)
            if spend_tx:
                reference = f"spend_reverse:{order.id}"
                existing_reverse = wallet_tx_model.search([('reference', '=', reference)], limit=1)
                if not existing_reverse:
                    wallet_tx_model.create({
                            'partner_id': spend_tx.partner_id.id,
                            'sale_order_id': order.id,
                            'amount': abs(spend_tx.amount),
                            'transaction_type': 'adjustment',
                            'state': 'posted',
                            'reversal_of_id': spend_tx.id,
                            'reference': reference,
                    })

            # Reverse earn
            earn_tx = wallet_tx_model.search([
                ('sale_order_id', '=', order.id),
                ('transaction_type', '=', 'earn'),
                ('state', '=', 'posted'),
            ], limit=1)
            if earn_tx:
                reference = f"earn_reverse:{order.id}"
                existing_reverse = wallet_tx_model.search([('reference', '=', reference)], limit=1)
                if not existing_reverse:
                    move_id = False
                    if journal_id and expense_account_id and liability_account_id:
                        move_vals = {
                            'journal_id': journal_id,
                            'date': fields.Date.today(),
                            'ref': _('Referrer Commission Reversal: %s') % order.name,
                            'move_type': 'entry',
                            'line_ids': [
                                (0, 0, {
                                    'name': _('Commission Expense Reversal'),
                                    'account_id': expense_account_id,
                                    'debit': 0.0,
                                    'credit': earn_tx.amount,
                                }),
                                (0, 0, {
                                    'name': _('Commission Payable Reversal'),
                                    'account_id': liability_account_id,
                                    'partner_id': earn_tx.partner_id.id,
                                    'debit': earn_tx.amount,
                                    'credit': 0.0,
                                }),
                            ]
                        }
                        ac_move = self.env['account.move'].create(move_vals)
                        ac_move.action_post()
                        move_id = ac_move.id

                    wallet_tx_model.create({
                            'partner_id': earn_tx.partner_id.id,
                            'sale_order_id': order.id,
                            'amount': -earn_tx.amount,
                            'transaction_type': 'adjustment',
                            'state': 'posted',
                            'accounting_move_id': move_id,
                            'reversal_of_id': earn_tx.id,
                            'reference': reference,
                    })
        return res

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.referrer_partner_id:
            invoice_vals['referrer_partner_id'] = self.referrer_partner_id.id
        return invoice_vals
