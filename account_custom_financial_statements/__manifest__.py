{
    "name": "Custom Financial Statements (Community)",
    "version": "19.0.1.0.0",
    "summary": "Profit and Loss and Balance Sheet for Odoo Community",
    "category": "Accounting/Accounting",
    "author": "Triton",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/financial_statement_wizard_views.xml",
        "report/financial_statement_templates.xml",
        "report/financial_statement_reports.xml",
        "views/financial_statement_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "account_custom_financial_statements/static/src/scss/financial_dashboard.scss",
            "account_custom_financial_statements/static/src/js/financial_dashboard.js",
            "account_custom_financial_statements/static/src/xml/financial_dashboard_templates.xml",
        ],
    },
    "installable": True,
    "application": False,
}
