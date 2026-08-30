{
    'name': 'OCA Financial Reports Enhance',
    'version': '19.0.1.0.0',
    'summary': 'Enhances OCA financial reports: GL grand totals, collapsible account sections, and more',
    'category': 'Accounting/Accounting',
    'author': 'Triton',
    'license': 'LGPL-3',
    'depends': ['account_financial_report'],
    'data': [
        'report/general_ledger_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'account_financial_report_enhance/static/src/css/gl_enhance.css',
        ],
    },
    'installable': True,
    'application': False,
}
