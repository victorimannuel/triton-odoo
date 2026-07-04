from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    referrer_credit_balance = fields.Float(string='Referrer Credit Balance', compute='_compute_referrer_credit_balance', digits='Account')
    referrer_wallet_transaction_ids = fields.One2many(
        'sale.referrer.wallet.transaction',
        'partner_id',
        string='Referrer Wallet Transactions',
    )

    @api.depends('referrer_wallet_transaction_ids.amount', 'referrer_wallet_transaction_ids.state')
    def _compute_referrer_credit_balance(self):
        for partner in self:
            balance = sum(
                partner.referrer_wallet_transaction_ids.filtered(lambda l: l.state == 'posted').mapped('amount')
            )
            partner.referrer_credit_balance = balance

    def action_view_referrer_ledger(self):
        self.ensure_one()
        return {
            'name': 'Referrer Credits',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.referrer.wallet.transaction',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
