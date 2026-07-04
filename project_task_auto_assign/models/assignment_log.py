from odoo import api, fields, models, _


class TaskAssignmentLog(models.Model):
    _name = 'task.assignment.log'
    _description = 'Task Assignment Log'
    _order = 'create_date DESC'

    task_id = fields.Many2one(
        'project.task',
        string='Task',
        required=True,
        ondelete='cascade',
    )
    rule_id = fields.Many2one(
        'task.assignment.rule',
        string='Assignment Rule',
        required=True,
        ondelete='restrict',
    )
    strategy = fields.Selection(
        related='rule_id.strategy',
        string='Strategy',
        store=True,
    )
    assigned_user_id = fields.Many2one(
        'res.users',
        string='Assigned User',
        required=True,
    )
    previous_user_id = fields.Many2one(
        'res.users',
        string='Previous User',
    )
    trigger = fields.Selection(
        [
            ('create', 'On Create'),
            ('stage_change', 'On Stage Change'),
        ],
        string='Trigger',
        required=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='task_id.company_id',
        store=True,
    )