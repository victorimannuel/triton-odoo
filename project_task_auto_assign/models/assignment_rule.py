from odoo import api, fields, models


class TaskAssignmentRule(models.Model):
    _name = 'task.assignment.rule'
    _description = 'Task Assignment Rule'
    _order = 'priority ASC, id DESC'

    name = fields.Char(string='Rule Name', required=True)
    active = fields.Boolean(string='Active', default=True)
    priority = fields.Integer(
        string='Priority',
        default=10,
        help='Lower number = higher priority (1 = highest)',
    )
    project_ids = fields.Many2many(
        'project.project',
        string='Projects',
        help='Leave empty to apply to all projects',
    )
    stage_id = fields.Many2one(
        'project.task.type',
        string='Stage',
        help='Optional: only apply when task is in this stage',
    )
    tag_id = fields.Many2one(
        'project.tags',
        string='Tag',
        help='Optional: only apply when task has this tag',
    )
    apply_on_create = fields.Boolean(
        string='Apply on Create',
        default=False,
        help='Apply this rule when a task is created',
    )
    apply_on_stage_change = fields.Boolean(
        string='Apply on Stage Change',
        default=False,
        help='Apply this rule when a task changes stage',
    )
    strategy = fields.Selection(
        [
            ('specific_user', 'Specific User'),
            ('round_robin', 'Round Robin'),
            ('least_loaded', 'Least Loaded'),
            ('team_lead', 'Team Lead'),
        ],
        string='Strategy',
        required=True,
        default='specific_user',
    )
    specific_user_id = fields.Many2one(
        'res.users',
        string='Specific User',
        domain="[('share', '=', False)]",
        help='User to assign when strategy is "Specific User"',
    )
    user_pool_ids = fields.Many2many(
        'res.users',
        'task_assignment_rule_users_rel',
        'rule_id',
        'user_id',
        string='User Pool',
        domain="[('share', '=', False)]",
        help='Pool of users for round-robin and least-loaded strategies',
    )
    last_assigned_index = fields.Integer(
        string='Last Assigned Index',
        default=0,
        help='Internal counter for round-robin tracking',
    )

    _sql_constraints = [
        (
            'check_priority_positive',
            'CHECK(priority > 0)',
            'Priority must be a positive integer.',
        ),
    ]

    def _get_candidate_user(self):
        """Return the user_id to assign based on the configured strategy."""
        self.ensure_one()

        if self.strategy == 'specific_user':
            return self.specific_user_id.id

        if self.strategy == 'team_lead':
            # Requires a project context — callers must pass project
            return False

        if self.strategy == 'round_robin':
            return self._round_robin_next()

        if self.strategy == 'least_loaded':
            return self._least_loaded_user()

        return False

    def _round_robin_next(self):
        """Return next user from pool using round-robin index."""
        self.ensure_one()
        pool = self.user_pool_ids
        if not pool:
            return False

        index = self.last_assigned_index
        user_id = pool[index].id
        next_index = (index + 1) % len(pool)
        self.sudo().write({'last_assigned_index': next_index})
        return user_id

    def _least_loaded_user(self):
        """Return the user from the pool with the fewest active tasks."""
        self.ensure_one()
        pool = self.user_pool_ids
        if not pool:
            return False

        Task = self.env['project.task']
        user_task_counts = []

        for user in pool:
            count = Task.search_count([
                ('user_ids', 'in', user.id),
                ('stage_id.fold', '=', False),
            ])
            user_task_counts.append((user.id, count))

        # Sort by task count ASC, return the user with fewest tasks
        user_task_counts.sort(key=lambda x: x[1])
        return user_task_counts[0][0] if user_task_counts else False