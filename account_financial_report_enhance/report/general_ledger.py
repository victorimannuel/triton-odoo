from odoo import api, models

class GeneralLedgerReport(models.AbstractModel):
    _inherit = "report.account_financial_report.general_ledger"

    @api.model
    def _get_period_domain(
        self,
        account_ids,
        partner_ids,
        company_id,
        only_posted_moves,
        date_to,
        date_from,
        cost_center_ids,
    ):
        domain = super()._get_period_domain(
            account_ids,
            partner_ids,
            company_id,
            only_posted_moves,
            date_to,
            date_from,
            cost_center_ids,
        )
        if company_id:
            domain = [d for d in domain if not (isinstance(d, tuple) and d[0] == "company_id")]
            companies = self.env["res.company"].search([("id", "child_of", company_id)])
            domain.append(("company_id", "in", companies.ids))
        return domain

    def _get_acc_prt_accounts_ids(self, company_id, grouped_by):
        companies = self.env["res.company"].search([("id", "child_of", company_id)])
        accounts_domain = [
            ("company_ids", "in", companies.ids),
        ] + self._get_account_type_domain(grouped_by)
        acc_prt_accounts = self.env["account.account"].search(accounts_domain)
        return acc_prt_accounts.ids

    def _get_initial_balances_bs_ml_domain(
        self, account_ids, company_id, date_from, base_domain, grouped_by, acc_prt=False
    ):
        companies = self.env["res.company"].search([("id", "child_of", company_id)])
        accounts_domain = [
            ("company_ids", "in", companies.ids),
            ("include_initial_balance", "=", True),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = []
        domain += base_domain
        domain += [("date", "<", date_from)]
        accounts = self.env["account.account"].search(accounts_domain)
        domain += [("account_id", "in", accounts.ids)]
        if acc_prt:
            domain += self._get_account_type_domain(grouped_by)
        return domain

    def _get_initial_balances_pl_ml_domain(
        self, account_ids, company_id, date_from, fy_start_date, base_domain
    ):
        companies = self.env["res.company"].search([("id", "child_of", company_id)])
        accounts_domain = [
            ("company_ids", "in", companies.ids),
            ("include_initial_balance", "=", False),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = []
        domain += base_domain
        domain += [("date", "<", date_from), ("date", ">=", fy_start_date)]
        accounts = self.env["account.account"].search(accounts_domain)
        domain += [("account_id", "in", accounts.ids)]
        return domain

    def _get_initial_balance_fy_pl_ml_domain(
        self, account_ids, company_id, fy_start_date, base_domain
    ):
        companies = self.env["res.company"].search([("id", "child_of", company_id)])
        accounts_domain = [
            ("company_ids", "in", companies.ids),
            ("include_initial_balance", "=", False),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = []
        domain += base_domain
        domain += [("date", "<", fy_start_date)]
        accounts = (
            self.env["account.account"]
            .with_context(active_test=False)
            .search(accounts_domain)
        )
        domain += [("account_id", "in", accounts.ids)]
        return domain

    def _get_initial_balance_data(
        self,
        account_ids,
        partner_ids,
        company_id,
        date_from,
        foreign_currency,
        only_posted_moves,
        unaffected_earnings_account,
        fy_start_date,
        cost_center_ids,
        extra_domain,
        grouped_by,
    ):
        if account_ids:
            unaffected_earnings_account = False
        base_domain = []
        if company_id:
            companies = self.env["res.company"].search([("id", "child_of", company_id)])
            base_domain += [("company_id", "in", companies.ids)]
        if partner_ids:
            base_domain += [("partner_id", "in", partner_ids)]
        if only_posted_moves:
            base_domain += [("move_id.state", "=", "posted")]
        else:
            base_domain += [("move_id.state", "in", ["posted", "draft"])]
        if cost_center_ids:
            base_domain += [("analytic_account_ids", "in", cost_center_ids)]
        if extra_domain:
            base_domain += extra_domain
            
        gl_initial_acc = self._get_gl_initial_acc(
            account_ids, company_id, date_from, fy_start_date, base_domain, grouped_by
        )
        domain = self._get_initial_balances_bs_ml_domain(
            account_ids, company_id, date_from, base_domain, grouped_by, acc_prt=True
        )
        data = self._prepare_gen_ld_data(gl_initial_acc, domain, grouped_by)
        accounts_ids = list(data.keys())
        unaffected_id = unaffected_earnings_account
        if unaffected_id:
            if unaffected_id not in accounts_ids:
                accounts_ids.append(unaffected_id)
                data[unaffected_id] = self._initialize_data(foreign_currency)
                data[unaffected_id]["id"] = unaffected_id
                data[unaffected_id]["mame"] = ""
                data[unaffected_id][grouped_by] = False
            pl_initial_balance = self._get_pl_initial_balance(
                account_ids, company_id, fy_start_date, foreign_currency, base_domain
            )
            for key_bal in ["init_bal", "fin_bal"]:
                fields_balance = ["credit", "debit", "balance"]
                if foreign_currency:
                    fields_balance.append("bal_curr")
                for field_name in fields_balance:
                    data[unaffected_id][key_bal][field_name] += pl_initial_balance[
                        field_name
                    ]
        return data
