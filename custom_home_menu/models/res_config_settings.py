from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    custom_home_menu_background_color = fields.Char(
        related='company_id.custom_home_menu_background_color',
        readonly=False,
    )
