from odoo import api, fields, models


class FinancialStatementWizard(models.TransientModel):
    _name = "custom.financial.statement.wizard"
    _description = "Custom Financial Statement Wizard"

    report_type = fields.Selection(
        [("pl", "Profit and Loss"), ("bs", "Balance Sheet")],
        required=True,
        default="pl",
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    date_from = fields.Date(default=lambda self: fields.Date.start_of(fields.Date.today(), "year"))
    date_to = fields.Date(required=True, default=fields.Date.today)
    target_move = fields.Selection(
        [("posted", "All Posted Entries"), ("all", "All Entries")],
        required=True,
        default="posted",
    )

    def action_print_html(self):
        self.ensure_one()
        report_name = (
            "account_custom_financial_statements.report_profit_loss"
            if self.report_type == "pl"
            else "account_custom_financial_statements.report_balance_sheet"
        )
        return self.env.ref(report_name).report_action(self)

    def action_print_pdf(self):
        self.ensure_one()
        report_name = (
            "account_custom_financial_statements.report_profit_loss_pdf"
            if self.report_type == "pl"
            else "account_custom_financial_statements.report_balance_sheet_pdf"
        )
        return self.env.ref(report_name).report_action(self)

    def action_view_dashboard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "account_custom_financial_statements.dashboard",
            "name": "Interactive Dashboard",
            "params": {
                "wizard_id": self.id,
            },
        }

    @api.model
    def get_dashboard_data(self, wizard_id):
        docs = self.browse(wizard_id)
        docs.ensure_one()
        service = self.env["custom.financial.statement.service"]
        
        if docs.report_type == "pl":
            payload = service.get_profit_and_loss(
                company_id=docs.company_id.id,
                date_from=docs.date_from,
                date_to=docs.date_to,
                target_move=docs.target_move,
            )
        else:
            payload = service.get_balance_sheet(
                company_id=docs.company_id.id,
                date_to=docs.date_to,
                target_move=docs.target_move,
            )
            
        return {
            "report_type": docs.report_type,
            "company_name": docs.company_id.display_name,
            "date_from": str(docs.date_from) if docs.date_from else "",
            "date_to": str(docs.date_to) if docs.date_to else "",
            "currency_symbol": docs.company_id.currency_id.symbol,
            "currency_position": docs.company_id.currency_id.position,
            "data": payload,
        }
