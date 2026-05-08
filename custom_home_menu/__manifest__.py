{
    'name': 'Custom Home Menu',
    'version': '19.0.1.0.0',
    'category': 'Web',
    'summary': 'Custom full-page grid layout for home menu (Community Edition)',
    'description': """
        This module replaces the default Odoo home menu dropdown with a 
        full-page grid layout showing app icons on a configurable background.
    """,
    'author': 'Binary Bears',
    'depends': ['web', 'base_setup'],
    'data': [
        'views/res_config_settings.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_home_menu/static/src/js/custom_home_menu.js',
            'custom_home_menu/static/src/scss/custom_home_menu.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'OPL-1',
    'price': 0.00,
    'currency': 'USD',
    'images': ['static/description/screenshot_main.png'],
}
