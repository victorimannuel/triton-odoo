{
    "name": "Dashboard Sale",
    "version": "19.0.1.0.0",
    "summary": "Sales and CRM overview dashboard for management",
    "category": "Sales/Sales",
    "author": "TRITON",
    "license": "LGPL-3",
    "depends": ["web", "sale_management", "crm"],
    "data": [
        "security/security.xml",
        "views/dashboard_sale_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "dashboard_sale/static/src/js/dashboard_sale_action.js",
            "dashboard_sale/static/src/xml/dashboard_sale_templates.xml",
            "dashboard_sale/static/src/scss/dashboard_sale.scss",
        ],
    },
    "installable": True,
    "application": True,
}
