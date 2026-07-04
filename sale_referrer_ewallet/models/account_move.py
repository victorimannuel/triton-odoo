from odoo import models, fields, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    referrer_partner_id = fields.Many2one('res.partner', string='Referrer', readonly=True, states={'draft': [('readonly', False)]})
    referrer_wallet_transaction_ids = fields.One2many(
        'sale.referrer.wallet.transaction',
        'source_invoice_id',
        string='Referrer Wallet Transactions',
    )

