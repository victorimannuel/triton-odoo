{
    'name': 'Web Colors',
    'summary': 'Company-specific branding colors for Odoo',
    'description': '''
        Provides company-dependent light and dark branding colors without
        rewriting shared asset bundles.
    ''',
    'version': '19.0.1.0.1',
    'category': 'Tools/UI',
    'license': 'LGPL-3',
    'depends': [
        'web',
        'base_setup',
    ],
    'data': [
        'templates/webclient.xml',
        'views/res_config_settings.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'web_colors/static/src/js/web_colors.js',
            'web_colors/static/src/scss/web_colors_runtime.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
