{
    'name': 'Indonesia - Region Localization (API)',
    'summary': 'Indonesia region master data with API sync',
    'version': '19.0.1.0.0',
    'category': 'Localization',
    'author': 'JTB',
    'license': 'LGPL-3',
    'depends': ['contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_country_state_views.xml',
        'views/res_city_views.xml',
        'views/res_district_views.xml',
        'views/res_village_views.xml',
        'views/res_config_settings.xml',
    ],
    'installable': True,
    'application': False,
}
