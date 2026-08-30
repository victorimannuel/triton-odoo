{
    'name': 'Invoice: Transfer to Another Company',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Transfer draft invoices to another company from the list view',
    'author': 'Victor',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_move_change_company_wizard_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
