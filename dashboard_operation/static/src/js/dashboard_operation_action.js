/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class DashboardOperation extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            data: null,
        });

        onWillStart(async () => {
            this.state.data = await this.orm.call("project.task", "get_role_dashboard_data", []);
        });
    }

    openTasks(filterType) {
        if (!this.state.data) return;

        let taskIds = [];
        if (filterType === 'overdue') taskIds = this.state.data.metrics.overdue_ids;
        else if (filterType === 'today') taskIds = this.state.data.metrics.today_ids;
        else if (filterType === '3days') taskIds = this.state.data.metrics.in_3_days_ids;
        else if (filterType === '7days') taskIds = this.state.data.metrics.in_7_days_ids;

        // Fallback domain if empty to prevent showing all tasks
        let domain = taskIds.length > 0 ? [['id', 'in', taskIds]] : [['id', '=', -1]];

        this.action.doAction({
            name: "Filtered Tasks",
            type: "ir.actions.act_window",
            res_model: "project.task",
            view_mode: "list,kanban,form",
            views: [[false, 'list'], [false, 'kanban'], [false, 'form']],
            domain: domain,
            context: { group_by: ['project_id', 'stage_id'] },
            target: "current",
        });
    }

    openGroupTasks(taskIds, groupBy = ['project_id', 'stage_id']) {
        if (!taskIds || taskIds.length === 0) return;

        let domain = [['id', 'in', taskIds]];

        this.action.doAction({
            name: "Group Tasks",
            type: "ir.actions.act_window",
            res_model: "project.task",
            view_mode: "list,kanban,form",
            views: [[false, 'list'], [false, 'kanban'], [false, 'form']],
            domain: domain,
            context: { group_by: groupBy },
            target: "current",
        });
    }

    openTask(taskId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "project.task",
            res_id: taskId,
            views: [[false, 'form']],
            target: "current",
        });
    }
}
DashboardOperation.template = "dashboard_operation.DashboardMain";
registry.category("actions").add("dashboard_operation.dashboard", DashboardOperation);
