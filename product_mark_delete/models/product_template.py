from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    to_be_deleted = fields.Boolean(
        string="To Be Deleted",
        help="Mark this product if you want to bulk delete it later.",
    )
