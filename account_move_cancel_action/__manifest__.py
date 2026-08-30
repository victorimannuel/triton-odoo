{
    'name': 'Account Move Cancel Action',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Adds actions to cancel and delete journal entries safely.',
    'description': """
        Adds list view actions to easily cancel, or cancel and delete, multiple journal entries
        with a confirmation dialog to prevent accidental operations.
    """,
    'author': 'Triton Odoo',
    'website': 'https://github.com/triton-odoo',
    'license': 'AGPL-3',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_move_cancel_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
