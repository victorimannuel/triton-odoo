from odoo import fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    color_brand_light = fields.Char(
        string='Brand Light Color',
        default='#243742',
    )

    color_primary_light = fields.Char(
        string='Primary Light Color',
        default='#5D8DA8',
    )

    color_success_light = fields.Char(
        string='Success Light Color',
        default='#28A745',
    )

    color_info_light = fields.Char(
        string='Info Light Color',
        default='#17A2B8',
    )

    color_warning_light = fields.Char(
        string='Warning Light Color',
        default='#FFAC00',
    )

    color_danger_light = fields.Char(
        string='Danger Light Color',
        default='#DC3545',
    )

    color_brand_dark = fields.Char(
        string='Brand Dark Color',
        default='#243742',
    )

    color_primary_dark = fields.Char(
        string='Primary Dark Color',
        default='#5D8DA8',
    )

    color_success_dark = fields.Char(
        string='Success Dark Color',
        default='#1DC959',
    )

    color_info_dark = fields.Char(
        string='Info Dark Color',
        default='#6AB5FB',
    )

    color_warning_dark = fields.Char(
        string='Warning Dark Color',
        default='#FBB56A',
    )

    color_danger_dark = fields.Char(
        string='Danger Dark Color',
        default='#FF5757',
    )
