/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class FinancialDashboard extends Component {
    static template = "account_custom_financial_statements.FinancialDashboard";

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({
            data: null,
            loading: true,
            expanded: {},
        });

        onWillStart(async () => {
            const wizardId = this.props.action.params.wizard_id;
            if (wizardId) {
                const response = await this.orm.call(
                    "custom.financial.statement.wizard",
                    "get_dashboard_data",
                    [wizardId]
                );
                this.state.data = response;
            }
            this.state.loading = false;
        });
    }

    isExpanded(key) {
        return this.state.expanded[key] !== false;
    }

    toggleSection(key) {
        this.state.expanded[key] = !this.isExpanded(key);
    }

    async openLines(domainStr) {
        if (!domainStr) return;
        
        try {
            const domain = JSON.parse(domainStr);
            this.actionService.doAction({
                type: "ir.actions.act_window",
                name: "Journal Items",
                res_model: "account.move.line",
                view_mode: "list,form",
                views: [[false, "list"], [false, "form"]],
                domain: domain,
                target: "current",
                context: { search_default_group_by_account: 0 },
            });
        } catch (e) {
            console.error("Failed to open journal items", e);
        }
    }
}

registry.category("actions").add("account_custom_financial_statements.dashboard", FinancialDashboard);
