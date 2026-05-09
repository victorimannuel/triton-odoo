from odoo import fields, models


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    city_ids = fields.One2many(
        comodel_name='res.city',
        inverse_name='state_id',
        string='Cities',
        readonly=True,
    )
