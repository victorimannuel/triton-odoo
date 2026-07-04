{
    'name': 'Project Task Auto Assign',
    'version': '19.0.1.0.0',
    'category': 'Project',
    'summary': 'Automatically assign tasks based on configurable rules',
    'description': """
        Project Task Auto Assign
        ========================
        Automatically assign project tasks to users based on configurable
        assignment rules. Supports multiple strategies:
        - Specific user assignment
        - Round-robin load balancing
        - Least-loaded user selection
        - Team lead assignment
    """,
    'author': 'Triton Odoo',
    'website': 'https://www.triton-odoo.com',
    'depends': ['project'],
    'data': [
        'security/ir.model.access.csv',
        'views/assignment_rule_views.xml',
        'views/assignment_log_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}