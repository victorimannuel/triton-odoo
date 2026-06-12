{
    "name": "Dashboard Operation",
    "version": "19.0.1.0.0",
    "summary": "Central operation dashboard for tasks and cross-app tracking",
    "category": "Operations",
    "author": "TRITON",
    "license": "LGPL-3",
    "depends": ["project", "web", "spreadsheet_dashboard"],
    "data": [
        "security/dashboard_operation_security.xml",
        "views/dashboard_operation_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "dashboard_operation/static/src/js/dashboard_operation_action.js",
            "dashboard_operation/static/src/xml/dashboard_operation_templates.xml",
            "dashboard_operation/static/src/scss/dashboard_operation.scss",
        ],
    },
    "installable": True,
    "application": True,
}
