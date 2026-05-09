from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    city_id = fields.Many2one(
        comodel_name='res.city',
        string='Kabupaten / Kota',
        domain="[('state_id', '=?', state_id)]",
    )
    district_id = fields.Many2one(
        comodel_name='res.district',
        string='District',
        domain="[('city_id', '=?', city_id)]",
    )
    village_id = fields.Many2one(
        comodel_name='res.village',
        string='Desa / Kelurahan',
        domain="[('district_id', '=?', district_id)]",
    )

    @api.onchange('city_id')
    def _onchange_city_id(self):
        self.district_id = False
        self.village_id = False

    @api.onchange('district_id')
    def _onchange_district_id(self):
        self.village_id = False

    @api.onchange('village_id')
    def _onchange_village_id(self):
        self.zip = self.village_id.zip
