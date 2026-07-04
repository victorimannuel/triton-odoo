from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def get_dashboard_sale_data(self):
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        month_start_dt = datetime.combine(month_start, time.min)
        next_month_dt = datetime.combine(next_month, time.min)
        year_start = today.replace(month=1, day=1)
        year_start_dt = datetime.combine(year_start, time.min)

        quotation_domain = [("state", "in", ["draft", "sent"])]
        sale_domain = [("state", "in", ["sale", "done"])]
        lead_domain = [("type", "=", "opportunity")]
        won_domain = [("type", "=", "opportunity"), ("stage_id.is_won", "=", True)]
        lost_domain = [("type", "=", "opportunity"), ("active", "=", False), ("probability", "=", 0)]

        quotation_count = self.search_count(quotation_domain)
        sale_count = self.search_count(sale_domain)
        won_count = self.env["crm.lead"].with_context(active_test=False).search_count(won_domain)
        lost_count = self.env["crm.lead"].with_context(active_test=False).search_count(lost_domain)
        pipeline_count = self.env["crm.lead"].search_count(lead_domain)

        win_rate = (won_count / (won_count + lost_count) * 100) if (won_count + lost_count) > 0 else 0.0

        monthly_orders = self.search_count([
            ("date_order", ">=", fields.Datetime.to_string(month_start_dt)),
            ("date_order", "<", fields.Datetime.to_string(next_month_dt)),
            ("state", "in", ["sale", "done"])
        ])
        monthly_revenue_data = self.read_group(
            domain=[
                ("state", "in", ["sale", "done"]),
                ("date_order", ">=", fields.Datetime.to_string(month_start_dt)),
                ("date_order", "<", fields.Datetime.to_string(next_month_dt)),
            ],
            fields=["amount_total:sum"],
            groupby=[],
            lazy=False,
        )
        monthly_revenue = monthly_revenue_data[0]["amount_total"] if monthly_revenue_data and monthly_revenue_data[0].get("amount_total") else 0.0

        ytd_revenue_data = self.read_group(
            domain=[
                ("state", "in", ["sale", "done"]),
                ("date_order", ">=", fields.Datetime.to_string(year_start_dt)),
            ],
            fields=["amount_total:sum"],
            groupby=[],
            lazy=False,
        )
        ytd_revenue = ytd_revenue_data[0]["amount_total"] if ytd_revenue_data and ytd_revenue_data[0].get("amount_total") else 0.0

        average_deal_size = ytd_revenue / sale_count if sale_count > 0 else 0.0

        quotation_total_data = self.read_group(
            domain=quotation_domain,
            fields=["amount_total:sum"],
            groupby=[],
            lazy=False,
        )
        quotation_total = quotation_total_data[0]["amount_total"] if quotation_total_data and quotation_total_data[0].get("amount_total") else 0.0

        pipeline_total_data = self.env["crm.lead"].read_group(
            domain=lead_domain,
            fields=["expected_revenue:sum"],
            groupby=[],
            lazy=False,
        )
        pipeline_total = pipeline_total_data[0]["expected_revenue"] if pipeline_total_data and pipeline_total_data[0].get("expected_revenue") else 0.0

        # Trends (Last 6 months)
        six_months_ago = (month_start - relativedelta(months=5))
        trend_domain = [
            ("state", "in", ["sale", "done"]),
            ("date_order", ">=", fields.Datetime.to_string(datetime.combine(six_months_ago, time.min))),
        ]
        trend_data = self.read_group(
            domain=trend_domain,
            fields=["amount_total:sum"],
            groupby=["date_order:month"],
            lazy=False,
        )
        
        # Ensure we have 6 months even if no data
        trend_series = []
        current_m = six_months_ago
        month_dict = {res.get("date_order:month"): res.get("amount_total", 0.0) for res in trend_data}
        for i in range(6):
            m_str = current_m.strftime("%B %Y")
            trend_series.append({
                "month": m_str,
                "revenue": month_dict.get(m_str, 0.0)
            })
            current_m = current_m + relativedelta(months=1)

        # Top 5 Products YTD
        top_products_data = self.env["sale.order.line"].read_group(
            domain=[
                ("order_id.state", "in", ["sale", "done"]),
                ("order_id.date_order", ">=", fields.Datetime.to_string(year_start_dt)),
                ("product_id", "!=", False)
            ],
            fields=["price_subtotal:sum"],
            groupby=["product_id"],
            orderby="price_subtotal desc",
            limit=5,
            lazy=False,
        )
        top_products = [
            {
                "product_id": res["product_id"][0],
                "product_name": res["product_id"][1],
                "revenue": res["price_subtotal"]
            }
            for res in top_products_data
        ]

        # Top 5 Salespersons YTD
        top_salespersons_data = self.read_group(
            domain=[
                ("state", "in", ["sale", "done"]),
                ("date_order", ">=", fields.Datetime.to_string(year_start_dt)),
                ("user_id", "!=", False)
            ],
            fields=["amount_total:sum"],
            groupby=["user_id"],
            orderby="amount_total desc",
            limit=5,
            lazy=False,
        )
        top_salespersons = [
            {
                "user_id": res["user_id"][0],
                "user_name": res["user_id"][1],
                "revenue": res["amount_total"]
            }
            for res in top_salespersons_data
        ]

        # Top 5 Customers YTD
        top_customers_data = self.read_group(
            domain=[
                ("state", "in", ["sale", "done"]),
                ("date_order", ">=", fields.Datetime.to_string(year_start_dt)),
                ("partner_id", "!=", False)
            ],
            fields=["amount_total:sum"],
            groupby=["partner_id"],
            orderby="amount_total desc",
            limit=5,
            lazy=False,
        )
        top_customers = [
            {
                "partner_id": res["partner_id"][0],
                "partner_name": res["partner_id"][1],
                "revenue": res["amount_total"]
            }
            for res in top_customers_data
        ]

        top_quotations = self.search_read(
            quotation_domain,
            ["name", "partner_id", "amount_total", "date_order", "user_id", "state"],
            limit=5,
            order="date_order desc",
        )
        top_leads = self.env["crm.lead"].search_read(
            lead_domain,
            ["name", "partner_name", "expected_revenue", "stage_id", "user_id", "type"],
            limit=5,
            order="create_date desc",
        )

        def _partner_name(row):
            return row["partner_id"][1] if row.get("partner_id") else row.get("partner_name") or "-"

        def _user_name(row):
            return row["user_id"][1] if row.get("user_id") else "-"

        return {
            "metrics": {
                "quotations": quotation_count,
                "sales_orders": sale_count,
                "pipeline": pipeline_count,
                "won": won_count,
                "win_rate": round(win_rate, 1),
                "monthly_orders": monthly_orders,
                "quotation_total": quotation_total,
                "pipeline_total": pipeline_total,
                "monthly_revenue": monthly_revenue,
                "ytd_revenue": ytd_revenue,
                "average_deal_size": average_deal_size,
            },
            "trend_series": trend_series,
            "top_products": top_products,
            "top_salespersons": top_salespersons,
            "top_customers": top_customers,
            "top_quotations": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "partner": _partner_name(row),
                    "amount": row["amount_total"],
                    "user": _user_name(row),
                    "state": row["state"],
                }
                for row in top_quotations
            ],
            "top_leads": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "partner": row.get("partner_name") or "-",
                    "amount": row.get("expected_revenue") or 0.0,
                    "user": row["user_id"][1] if row.get("user_id") else "-",
                    "stage": row["stage_id"][1] if row.get("stage_id") else "-",
                }
                for row in top_leads
            ],
            "links": {
                "quotations": quotation_domain,
                "sales_orders": sale_domain,
                "pipeline": lead_domain,
                "won": won_domain,
            },
        }
