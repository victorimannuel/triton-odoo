/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class DashboardSale extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null });

        onWillStart(async () => {
            this.state.data = await this.orm.call("sale.order", "get_dashboard_sale_data", []);
            if (this.state.data) {
                this.state.data.revenueShareChart = this.buildRevenueShareChart(this.state.data.top_products);
                this.state.data.dailyBalanceChart = this.buildTrendChart(this.state.data.trend_series);
            }
        });
    }

    formatCurrency(amount, currencyCode = "IDR") {
        const value = Number(amount || 0);
        return new Intl.NumberFormat(undefined, { style: "currency", currency: currencyCode, maximumFractionDigits: 0 }).format(value);
    }

    buildRevenueShareChart(topProducts) {
        if (!topProducts || !topProducts.length) return null;
        const palette = ["#2563eb", "#22c55e", "#f97316", "#7c3aed", "#e11d48", "#06b6d4", "#84cc16", "#f59e0b"];
        const total = topProducts.reduce((acc, p) => acc + p.revenue, 0);
        if (!total) return null;
        let cumulative = 0;
        const slices = topProducts.map((p, idx) => {
            const pct = (p.revenue / total) * 100;
            const start = cumulative;
            cumulative += pct;
            return {
                id: p.product_id,
                name: p.product_name,
                value: p.revenue,
                pct,
                color: palette[idx % palette.length],
                start,
                end: cumulative
            };
        });
        const gradient = slices.map((s) => `${s.color} ${s.start.toFixed(2)}% ${s.end.toFixed(2)}%`).join(", ");
        return { total, donutStyle: `conic-gradient(${gradient})`, slices };
    }

    buildTrendChart(trendSeries) {
        if (!trendSeries || !trendSeries.length) return null;
        const revenues = trendSeries.map(t => t.revenue);
        const min = Math.min(...revenues, 0);
        const max = Math.max(...revenues, 1);
        const range = Math.max(1, max - min);
        
        const chartBars = trendSeries.map(pt => ({
            month: pt.month,
            revenue: pt.revenue,
            heightPct: ((pt.revenue - min) / range) * 100
        }));
        
        return { chartBars, min, max };
    }

    openSaleOrders(domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Sales Orders",
            res_model: "sale.order",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain,
            target: "current",
        });
    }

    openLeads(domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "CRM Opportunities",
            res_model: "crm.lead",
            view_mode: "list,kanban,form",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            domain,
            target: "current",
        });
    }
}

DashboardSale.template = "dashboard_sale.DashboardMain";
registry.category("actions").add("dashboard_sale.dashboard", DashboardSale);
