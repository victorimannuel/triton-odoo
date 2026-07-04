{
    'name': 'CRM Sale Autofill',
    'version': '19.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Autofill quotation lines from CRM opportunity hints',
    'author': 'Victor',
    'depends': ['crm', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
