from odoo import models, fields, api
from odoo.osv import expression
from datetime import timedelta, datetime

class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def get_role_dashboard_data(self):
        # Determine if user has the new Operations Manager role
        is_manager = self.env.user.has_group('dashboard_operation.group_operation_manager')
        
        today_date = fields.Date.context_today(self)
        date_3_days = today_date + timedelta(days=3)
        date_7_days = today_date + timedelta(days=7)

        # Define base domain: Only open tasks.
        # In modern Odoo, we can often rely on stage_id.is_closed or the state field.
        # We will use stage_id.is_closed = False as a safe standard way to get open tasks.
        base_domain = [('project_id', '!=', False)]
        
        # Odoo 19 uses state field as well, but state can be '1_done' etc. 
        # For safety, let's just avoid tasks in '1_done', '1_canceled'.
        base_domain = expression.AND([base_domain, [('state', 'not in', ['1_done', '1_canceled', '03_approved', '04_waiting_normal', '1_done'])]])
        
        # It's better to just exclude closed stages
        base_domain = expression.AND([[('project_id', '!=', False)], [('stage_id.fold', '=', False)]])

        if not is_manager:
            base_domain = expression.AND([base_domain, [('user_ids', 'in', [self.env.user.id])]])

        fields_to_read = ['name', 'date_deadline', 'project_id', 'user_ids', 'stage_id', 'state', 'priority']
        if 'subtask_count' in self._fields:
            fields_to_read.extend(['subtask_count', 'closed_subtask_count'])
            
        tasks = self.search_read(base_domain, fields_to_read)

        overdue_tasks = []
        today_tasks = []
        in_3_days_tasks = []
        in_7_days_tasks = []

        project_grouping = {}
        assignee_grouping = {}
        status_grouping = {}

        for task in tasks:
            # Categorize by date
            if task['date_deadline']:
                deadline = task['date_deadline']
                # If date_deadline is datetime, we need date. Odoo search_read returns date or datetime strings.
                # Actually, date_deadline is a Date field in standard Odoo.
                if isinstance(deadline, str):
                    deadline = fields.Date.from_string(deadline)
                
                if isinstance(deadline, datetime):
                    deadline = deadline.date()
                
                if deadline < today_date:
                    overdue_tasks.append(task)
                elif deadline == today_date:
                    today_tasks.append(task)
                elif today_date < deadline <= date_3_days:
                    in_3_days_tasks.append(task)
                elif date_3_days < deadline <= date_7_days:
                    in_7_days_tasks.append(task)

            # Groupings (Applicable to both Manager and User workloads)
            # Project
            proj_id = task['project_id'][0] if task['project_id'] else 0
            proj_name = task['project_id'][1] if task['project_id'] else 'No Project'
            if proj_id not in project_grouping:
                project_grouping[proj_id] = {'name': proj_name, 'count': 0, 'task_ids': []}
            project_grouping[proj_id]['count'] += 1
            project_grouping[proj_id]['task_ids'].append(task['id'])

            import re
            
            # Status (Now using 'state')
            state_key = task.get('state')
            # Basic mapping for Odoo standard project.task states and custom states
            state_map = {
                '01_in_progress': 'In Progress',
                '02_changes_requested': 'Changes Requested',
                '03_approved': 'Approved',
                '04_waiting_normal': 'Waiting',
                '05_pending': 'Pending',
                '06_waiting_validation': 'Waiting Validation',
                '1_done': 'Done',
                '1_canceled': 'Canceled',
                False: 'No State',
                None: 'No State'
            }
            
            if state_key in state_map:
                state_name = state_map[state_key]
            else:
                # Fallback: remove leading numbers and underscores (e.g., '05_pending' -> 'Pending')
                fallback_name = str(state_key).replace('_', ' ')
                fallback_name = re.sub(r'^\d+\s*', '', fallback_name).title()
                state_name = fallback_name

            color_map = {
                '01_in_progress': 'bg-info text-dark',
                '02_changes_requested': 'bg-purple text-white',
                '03_approved': 'bg-success',
                '04_waiting_normal': 'bg-info text-dark',
                '05_pending': 'bg-warning text-dark',
                '06_waiting_validation': 'bg-warning text-dark',
                '1_done': 'bg-success',
                '1_canceled': 'bg-danger',
            }
            state_color = color_map.get(state_key, 'bg-secondary')

            if state_name not in status_grouping:
                status_grouping[state_name] = {'name': state_name, 'count': 0, 'task_ids': [], 'color': state_color}
            status_grouping[state_name]['count'] += 1
            status_grouping[state_name]['task_ids'].append(task['id'])

        # We can do a read to get user names for assignees if we need it (Manager only)
        if is_manager and tasks:
            user_ids = list(set([u for t in tasks for u in t.get('user_ids', [])]))
            users = self.env['res.users'].browse(user_ids).read(['name'])
            user_map = {u['id']: u['name'] for u in users}
            for task in tasks:
                for uid in task.get('user_ids', []):
                    if uid not in assignee_grouping:
                        assignee_grouping[uid] = {'name': user_map.get(uid, 'Unknown'), 'count': 0, 'task_ids': []}
                    assignee_grouping[uid]['count'] += 1
                    assignee_grouping[uid]['task_ids'].append(task['id'])

        # Build urgent tasks list (max 10)
        urgent_combined = overdue_tasks + today_tasks
        urgent_list = []
        for t in urgent_combined[:10]:
            raw_prio = t.get('priority', '0')
            try:
                prio_val = int(raw_prio)
            except:
                prio_val = 0
            
            progress = 0.0
            if t.get('subtask_count'):
                progress = (t.get('closed_subtask_count', 0) / t.get('subtask_count')) * 100
                
            urgent_list.append({
                'id': t['id'],
                'name': t['name'],
                'deadline': str(t['date_deadline']) if t['date_deadline'] else '',
                'project_name': t['project_id'][1] if t['project_id'] else 'No Project',
                'priority_val': prio_val,
                'progress': round(progress),
                'has_subtasks': bool(t.get('subtask_count', 0))
            })

        return {
            'is_manager': is_manager,
            'metrics': {
                'total_open': len(tasks),
                'overdue': len(overdue_tasks),
                'overdue_ids': [t['id'] for t in overdue_tasks],
                'today': len(today_tasks),
                'today_ids': [t['id'] for t in today_tasks],
                'in_3_days': len(in_3_days_tasks),
                'in_3_days_ids': [t['id'] for t in in_3_days_tasks],
                'in_7_days': len(in_7_days_tasks),
                'in_7_days_ids': [t['id'] for t in in_7_days_tasks],
            },
            'groupings': {
                'projects': list(project_grouping.values()),
                'assignees': list(assignee_grouping.values()),
                'statuses': list(status_grouping.values()),
            },
            'urgent_tasks': urgent_list
        }
