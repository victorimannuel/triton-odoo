from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    #----------------------------------------------------------
    # Fields
    #----------------------------------------------------------

    sidebar_image = fields.Binary(
        related='company_id.sidebar_image',
        readonly=False
    )

    theme_color_sidebar_text = fields.Char(
        related='company_id.theme_color_sidebar_text',
        readonly=False,
    )

    theme_color_sidebar_active = fields.Char(
        related='company_id.theme_color_sidebar_active',
        readonly=False,
    )

    theme_color_sidebar_active_text = fields.Char(
        related='company_id.theme_color_sidebar_active_text',
        readonly=False,
    )

    theme_color_sidebar_background = fields.Char(
        related='company_id.theme_color_sidebar_background',
        readonly=False,
    )
