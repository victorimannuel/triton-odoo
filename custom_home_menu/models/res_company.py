from odoo import fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    custom_home_menu_background_color = fields.Char(
        string='Home Menu Background Color',
        default='#e8d5f0',
    )
