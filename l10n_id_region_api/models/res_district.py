from odoo import fields, models


class ResDistrict(models.Model):
    _name = 'res.district'
    _description = 'District'
    _order = 'name'

    name = fields.Char(string='District', required=True, index=True)
    code = fields.Char(string='Code', required=True, index=True)
    city_id = fields.Many2one(
        comodel_name='res.city',
        string='Kabupaten / Kota',
        ondelete='cascade',
        required=True,
        index=True,
    )
    active = fields.Boolean(default=True)
    village_ids = fields.One2many(
        comodel_name='res.village',
        inverse_name='district_id',
        string='Desa / Kelurahan',
        readonly=True,
    )

    _sql_constraints = [
        ('res_district_code_uniq', 'unique(code)', 'District code must be unique.'),
    ]
