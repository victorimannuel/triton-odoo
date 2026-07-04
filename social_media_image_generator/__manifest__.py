{
    'name': 'Social Media Image Generator',
    'version': '1.0.0',
    'summary': 'Generate social media images directly from Odoo',
    'description': """
        Generate professional social media images directly from Odoo.
        Supports multiple templates: Announcement, Tips, Quote, Event, Custom.
        Export to Instagram (Post/Story), Facebook, LinkedIn formats.
    """,
    'author': 'Triton',
    'website': '',
    'category': 'Marketing',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/wizard_view.xml',
        'views/menu.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}