from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    asset_domain = [
        '|',
        ('path', 'like', '/_custom/%web_colors/static/src/scss/colors%'),
        ('path', 'like', '/web_colors/static/src/scss/colors%'),
    ]
    attachment_domain = [
        '|',
        ('url', 'like', '/_custom/%web_colors/static/src/scss/colors%'),
        ('url', 'like', '/web_colors/static/src/scss/colors%'),
    ]
    env['ir.asset'].search(asset_domain).unlink()
    env['ir.attachment'].search(attachment_domain).unlink()
    env.registry.clear_cache('assets')
