from odoo import fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    suggested_product_line_ids = fields.One2many('crm.lead.suggested.product', 'lead_id', string='Suggested Products')
