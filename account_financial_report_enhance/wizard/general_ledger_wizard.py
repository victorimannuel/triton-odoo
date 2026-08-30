from odoo import api, models, fields


class GeneralLedgerReportWizard(models.TransientModel):
    _inherit = "general.ledger.report.wizard"

    grouped_by = fields.Selection(
        selection=[("none", "None"), ("partners", "Partners"), ("taxes", "Taxes")],
        default="none",
        required=True,
    )

    def _only_one_unaffected_earnings_account(self):
        companies = self.env["res.company"].search([("id", "child_of", self.company_id.id or self.env.company.id)])
        count = self.env["account.account"].search_count(
            [
                ("account_type", "=", "equity_unaffected"),
                ("company_ids", "in", companies.ids),
            ]
        )
        return count == 1

    @api.onchange("company_id")
    def onchange_company_id(self):
        res = super().onchange_company_id()
        if self.company_id and res and "domain" in res:
            companies = self.env["res.company"].search([("id", "child_of", self.company_id.id)])
            
            if "account_ids" in res["domain"]:
                new_domain = []
                for d in res["domain"]["account_ids"]:
                    if isinstance(d, tuple) and d[0] == "company_ids":
                        new_domain.append(("company_ids", "in", companies.ids))
                    else:
                        new_domain.append(d)
                res["domain"]["account_ids"] = new_domain
                
            if "account_journal_ids" in res["domain"]:
                new_domain = []
                for d in res["domain"]["account_journal_ids"]:
                    if isinstance(d, tuple) and d[0] == "company_id":
                        new_domain.append(("company_id", "in", companies.ids))
                    else:
                        new_domain.append(d)
                res["domain"]["account_journal_ids"] = new_domain
                
            if "cost_center_ids" in res["domain"]:
                new_domain = []
                for d in res["domain"]["cost_center_ids"]:
                    if isinstance(d, tuple) and d[0] == "company_id":
                        new_domain.append(("company_id", "in", companies.ids))
                    else:
                        new_domain.append(d)
                res["domain"]["cost_center_ids"] = new_domain
                
            if "date_range_id" in res["domain"]:
                new_domain = []
                for d in res["domain"]["date_range_id"]:
                    if isinstance(d, tuple) and d[0] == "company_id":
                        new_domain.append(("company_id", "in", companies.ids))
                    else:
                        new_domain.append(d)
                res["domain"]["date_range_id"] = new_domain
                
        return res

    @api.onchange("receivable_accounts_only", "payable_accounts_only")
    def onchange_type_accounts_only(self):
        super().onchange_type_accounts_only()
        if (self.receivable_accounts_only or self.payable_accounts_only) and self.company_id:
            companies = self.env["res.company"].search([("id", "child_of", self.company_id.id)])
            domain = [("company_ids", "in", companies.ids)]
            if self.receivable_accounts_only and self.payable_accounts_only:
                domain += [
                    ("account_type", "in", ("asset_receivable", "liability_payable"))
                ]
            elif self.receivable_accounts_only:
                domain += [("account_type", "=", "asset_receivable")]
            elif self.payable_accounts_only:
                domain += [("account_type", "=", "liability_payable")]
            self.account_ids = self.env["account.account"].search(domain)

    @api.depends("company_id")
    def _compute_unaffected_earnings_account(self):
        for record in self:
            if record.company_id:
                companies = self.env["res.company"].search([("id", "child_of", record.company_id.id)])
                record.unaffected_earnings_account = self.env["account.account"].search(
                    [
                        ("account_type", "=", "equity_unaffected"),
                        ("company_ids", "in", companies.ids),
                    ],
                    limit=1,
                )
            else:
                record.unaffected_earnings_account = False
