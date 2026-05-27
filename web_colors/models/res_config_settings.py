from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    color_brand_light = fields.Char(
        related='company_id.color_brand_light',
        readonly=False,
    )

    color_primary_light = fields.Char(
        related='company_id.color_primary_light',
        readonly=False,
    )

    color_success_light = fields.Char(
        related='company_id.color_success_light',
        readonly=False,
    )

    color_info_light = fields.Char(
        related='company_id.color_info_light',
        readonly=False,
    )

    color_warning_light = fields.Char(
        related='company_id.color_warning_light',
        readonly=False,
    )

    color_danger_light = fields.Char(
        related='company_id.color_danger_light',
        readonly=False,
    )

    color_brand_dark = fields.Char(
        related='company_id.color_brand_dark',
        readonly=False,
    )

    color_primary_dark = fields.Char(
        related='company_id.color_primary_dark',
        readonly=False,
    )

    color_success_dark = fields.Char(
        related='company_id.color_success_dark',
        readonly=False,
    )

    color_info_dark = fields.Char(
        related='company_id.color_info_dark',
        readonly=False,
    )

    color_warning_dark = fields.Char(
        related='company_id.color_warning_dark',
        readonly=False,
    )

    color_danger_dark = fields.Char(
        related='company_id.color_danger_dark',
        readonly=False,
    )
