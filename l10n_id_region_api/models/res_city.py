from odoo import fields, models


class ResCity(models.Model):
    _name = 'res.city'
    _description = 'Kabupaten / Kota'
    _order = 'name'

    name = fields.Char(string='Kabupaten / Kota', required=True, index=True)
    code = fields.Char(string='Code', required=True, index=True)
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Provinsi',
        ondelete='cascade',
        required=True,
        index=True,
    )
    active = fields.Boolean(default=True)
    district_ids = fields.One2many(
        comodel_name='res.district',
        inverse_name='city_id',
        string='Districts',
        readonly=True,
    )

    _sql_constraints = [
        ('res_city_code_uniq', 'unique(code)', 'City code must be unique.'),
    ]
