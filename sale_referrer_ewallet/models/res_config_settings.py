from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    referrer_commission_percentage = fields.Float(string='Referrer Commission %', config_parameter='sale_referrer_ewallet.commission_percentage', default=5.0)
    
    referrer_journal_id = fields.Many2one('account.journal', string='Referrer Commission Journal', config_parameter='sale_referrer_ewallet.referrer_journal_id')
    referrer_expense_account_id = fields.Many2one('account.account', string='Commission Expense Account', config_parameter='sale_referrer_ewallet.referrer_expense_account_id')
    referrer_liability_account_id = fields.Many2one('account.account', string='Commission Liability Account', config_parameter='sale_referrer_ewallet.referrer_liability_account_id')
    
    referrer_odoo_ewallet_program_id = fields.Many2one(
        'loyalty.program',
        string='Odoo eWallet Program',
        domain=[('program_type', '=', 'ewallet')],
        config_parameter='sale_referrer_ewallet.referrer_odoo_ewallet_program_id',
        help='Loyalty program (Type = eWallet) used to sync transactions automatically.',
    )

    def set_values(self):
        super().set_values()
        # Auto-configure the redemption product to use the liability account
        if self.referrer_liability_account_id:
             product = self.env.ref('sale_referrer_ewallet.product_product_referrer_credit', raise_if_not_found=False)
             if product:
                 product.sudo().write({'property_account_income_id': self.referrer_liability_account_id.id})
