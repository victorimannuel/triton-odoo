from odoo import api, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    def create(self, vals_list):
        """Override create to auto-assign tasks based on rules."""
        tasks = super().create(vals_list)
        tasks._apply_assignment_rules('create')
        return tasks

    def write(self, vals):
        """Override write to auto-assign on stage change."""
        old_stage_map = {}
        if 'stage_id' in vals:
            old_stage_map = {task.id: task.stage_id.id for task in self}

        result = super().write(vals)

        if 'stage_id' in vals:
            for task in self:
                if task.stage_id.id != old_stage_map.get(task.id):
                    task._apply_assignment_rules('stage_change')

        return result

    def _apply_assignment_rules(self, trigger):
        """Find matching rules and apply assignment."""
        Rule = self.env['task.assignment.rule']
        Log = self.env['task.assignment.log']

        for task in self:
            if trigger == 'create':
                rules = Rule.search([
                    ('apply_on_create', '=', True),
                    ('active', '=', True),
                ], order='priority ASC')
            elif trigger == 'stage_change':
                rules = Rule.search([
                    ('apply_on_stage_change', '=', True),
                    ('active', '=', True),
                ], order='priority ASC')
            else:
                continue

            if not rules:
                continue

            matched_rule = rules._match_rules(task)

            if not matched_rule:
                continue

            user_id = False

            if matched_rule.strategy == 'team_lead':
                user_id = task.project_id.user_id.id if task.project_id else False
            else:
                user_id = matched_rule._get_candidate_user()

            if not user_id:
                continue

            previous_user_ids = task.user_ids.ids or []

            task.sudo().write({'user_ids': [(6, 0, [user_id])]})

            log_vals = {
                'task_id': task.id,
                'rule_id': matched_rule.id,
                'assigned_user_id': user_id,
                'trigger': trigger,
            }
            if previous_user_ids:
                log_vals['previous_user_id'] = previous_user_ids[0]

            Log.sudo().create(log_vals)


class TaskAssignmentRule(models.Model):
    """Extend task.assignment.rule with rule-matching logic."""

    _inherit = 'task.assignment.rule'

    def _match_rules(self, task):
        """Find the first rule in self that matches the given task."""
        for rule in self:
            # Check project_ids filter
            if rule.project_ids:
                if task.project_id.id not in rule.project_ids.ids:
                    continue

            # Check stage_id filter
            if rule.stage_id:
                if task.stage_id.id != rule.stage_id.id:
                    continue

            # Check tag_id filter
            if rule.tag_id:
                task_tag_ids = task.tag_ids.ids
                if rule.tag_id.id not in task_tag_ids:
                    continue

            return rule

        return self.env['task.assignment.rule']