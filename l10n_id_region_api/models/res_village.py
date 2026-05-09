from odoo import fields, models


class ResVillage(models.Model):
    _name = 'res.village'
    _description = 'Desa / Kelurahan'
    _order = 'name'

    name = fields.Char(string='Desa / Kelurahan', required=True, index=True)
    code = fields.Char(string='Code', required=True, index=True)
    district_id = fields.Many2one(
        comodel_name='res.district',
        string='District',
        ondelete='cascade',
        required=True,
        index=True,
    )
    zip = fields.Char(string='Kode POS')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('res_village_code_uniq', 'unique(code)', 'Village code must be unique.'),
    ]
