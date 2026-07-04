from odoo import fields, models


class CrmLeadSuggestedProduct(models.Model):
    _name = 'crm.lead.suggested.product'
    _description = 'Suggested Product for Lead'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True, ondelete='cascade', index=True)
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Char(string='Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    price_unit = fields.Float(string='Unit Price')
