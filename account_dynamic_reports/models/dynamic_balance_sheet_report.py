# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swetha Anand (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import io
import json
import datetime
import xlsxwriter
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.date_utils import get_month, get_fiscal_year, get_quarter, \
    subtract


class ProfitLossReport(models.TransientModel):
    """For creating Profit and Loss and Balance sheet report."""
    _name = 'dynamic.balance.sheet.report'
    _description = 'Profit Loss Report'

    company_id = fields.Many2one('res.company', required=True,
                                 default=lambda self: self.env.company,
                                 help='Select the company to which this'
                                      'record belongs.')
    journal_ids = fields.Many2many('account.journal',
                                   string='Journals', required=True,
                                   default=[],
                                   help='Select one or more journals.')
    account_ids = fields.Many2many("account.account", string="Accounts",
                                   help='Select one or more accounts.')
    analytic_ids = fields.Many2many(
        "account.analytic.account", string="Analytic Accounts",
        help="Analytic accounts associated with the current record.")
    target_move = fields.Selection([('posted', 'Posted'), ('draft', 'Draft')],
                                   string='Target Move', required=True,
                                   default='posted',
                                   help='Select the target move status.')
    date_from = fields.Date(string="Start date",
                            help="Specify the start date.")
    date_to = fields.Date(string="End date", help="Specify the end date.")

    @api.model_create_multi
    def create(self, vals):
        """Create one or more records of ProfitLossReport.
        :param vals: A dictionary or a list of dictionaries containing the field values for the records to be created.
        :return: A recordset of the created ProfitLossReport records."""
        return super(ProfitLossReport, self).create({})

    @api.model
    def view_report(self, option, comparison, comparison_type):
        datas = []
        account_types = {
            'income': 'income',
            'income_other': 'income_other',
            'expense': 'expense',
            'expense_depreciation': 'expense_depreciation',
            'expense_direct_cost': 'expense_direct_cost',
            'asset_receivable': 'asset_receivable',
            'asset_cash': 'asset_cash',
            'asset_current': 'asset_current',
            'asset_non_current': 'asset_non_current',
            'asset_prepayments': 'asset_prepayments',
            'asset_fixed': 'asset_fixed',
            'liability_payable': 'liability_payable',
            'liability_credit_card': 'liability_credit_card',
            'liability_current': 'liability_current',
            'liability_non_current': 'liability_non_current',
            'equity': 'equity',
            'equity_unaffected': 'equity_unaffected',
        }
        financial_report_id = self.browse(option)
        account_model = self.env['account.account']
        accounts_by_type = {
            account_type: account_model.search([('account_type', '=', account_type)])
            for account_type in account_types.values()
        }
        current_year = fields.Date.today().year
        current_date = fields.Date.today()
        if financial_report_id.target_move == 'draft':
            target_move = ['posted', 'draft']
        else:
            target_move = ['posted']
        if comparison:
            for count in range(0, int(comparison) + 1):
                if comparison_type == "month":
                    account_move_lines = self.env['account.move.line'].search(
                        [(
                            'parent_state', 'in', target_move),
                            ('date', '<=', (current_date - datetime.timedelta(
                                days=30 * count)).strftime('%Y-%m-12'))])
                elif comparison_type == "year":
                    account_move_lines = self.env['account.move.line'].search(
                        [(
                            'parent_state', 'in', target_move),
                            ('date', '<=', f'{current_year - count}-12-31')])
                lists = [{'id': rec.id, 'value': [int(i) for i in
                                                  rec.analytic_distribution.keys()]}
                         for rec in account_move_lines if
                         rec.analytic_distribution]
                if financial_report_id.analytic_ids:
                    account_move_lines = account_move_lines.filtered(lambda
                                                                         rec: rec.id in [
                        lst['id'] for lst in lists if lst['value'] and any(
                            i in financial_report_id.analytic_ids.mapped('id')
                            for i in lst['value'])])
                account_move_lines = account_move_lines.filtered(lambda
                                                                     a: not financial_report_id.journal_ids or a.journal_id in financial_report_id.journal_ids)
                account_move_lines = account_move_lines.filtered(lambda
                                                                     a: not financial_report_id.account_ids or a.account_id in financial_report_id.account_ids)
                account_move_lines = account_move_lines.filtered(lambda
                                                                     a: not financial_report_id.date_to or a.date <= financial_report_id.date_to)
                account_entries = self._get_entries_by_type(
                    account_move_lines,
                    accounts_by_type,
                    account_types.values(),
                )
                total_income = sum(
                    float(entry['amount'].replace(',', '')) for account_type
                    in
                    ['income', 'income_other'] for entry in
                    account_entries[account_type][0]) - sum(
                    float(entry['amount'].replace(',', '')) for entry in
                    account_entries['expense_direct_cost'][0])
                total_expense = sum(
                    float(entry['amount'].replace(',', '')) for account_type
                    in
                    ['expense', 'expense_depreciation'] for entry in
                    account_entries[account_type][0])
                total_current_asset = sum(
                    float(entry['amount'].replace(',', '')) for account_type
                    in
                    ['asset_receivable', 'asset_current', 'asset_cash',
                     'asset_prepayments'] for entry in
                    account_entries[account_type][0])
                total_assets = total_current_asset + sum(
                    float(entry['amount'].replace(',', '')) for account_type
                    in
                    ['asset_fixed', 'asset_non_current'] for entry in
                    account_entries[account_type][0])
                total_current_liability = sum(
                    float(entry['amount'].replace(',', '')) for account_type
                    in
                    ['liability_current', 'liability_payable'] for entry in
                    account_entries[account_type][0])
                total_liability = total_current_liability + sum(
                    float(entry['amount'].replace(',', '')) for account_type
                    in
                    ['liability_non_current'] for entry in
                    account_entries[account_type][0])
                total_unallocated_earning = (
                                                    total_income - total_expense) + sum(
                    float(entry['amount'].replace(',', '')) for account_type
                    in
                    ['equity_unaffected'] for entry in
                    account_entries[account_type][0])
                total_equity = total_unallocated_earning + sum(
                    float(entry['amount'].replace(',', '')) for account_type
                    in
                    ['equity'] for entry in
                    account_entries[account_type][0])
                total = total_liability + total_equity
                data = {
                    'total': total_income - total_expense,
                    'total_expense': "{:,.2f}".format(total_expense),
                    'total_income': "{:,.2f}".format(total_income),
                    'total_current_asset': "{:,.2f}".format(
                        total_current_asset),
                    'total_assets': "{:,.2f}".format(total_assets),
                    'total_current_liability': "{:,.2f}".format(
                        total_current_liability),
                    'total_liability': "{:,.2f}".format(total_liability),
                    'total_earnings': "{:,.2f}".format(
                        total_income - total_expense),
                    'total_unallocated_earning': "{:,.2f}".format(
                        total_unallocated_earning),
                    'total_equity': "{:,.2f}".format(total_equity),
                    'total_balance': "{:,.2f}".format(total),
                    **account_entries}
                datas.append(data)
        else:
            current_year = fields.Date.today().year
            date_from = financial_report_id.date_from or f'{current_year}-01-01'
            date_to = financial_report_id.date_to or f'{current_year}-12-31'
            account_move_lines = self.env['account.move.line'].search(
                [('parent_state', 'in', target_move),
                 ('date', '<=', date_to)])
            lists = [{'id': rec.id,
                      'value': [int(i) for i in
                                rec.analytic_distribution.keys()]}
                     for rec in account_move_lines if
                     rec.analytic_distribution]
            if financial_report_id.analytic_ids:
                account_move_lines = account_move_lines.filtered(
                    lambda rec: rec.id in [lst['id'] for lst in lists if
                                           lst['value'] and any(
                                               i in financial_report_id.analytic_ids.mapped(
                                                   'id') for i in
                                               lst['value'])])
            account_move_lines = account_move_lines.filtered(lambda
                                                                 a: not financial_report_id.journal_ids or a.journal_id in financial_report_id.journal_ids)
            account_move_lines = account_move_lines.filtered(lambda
                                                                 a: not financial_report_id.account_ids or a.account_id in financial_report_id.account_ids)
            account_move_lines = account_move_lines.filtered(lambda
                                                                 a: not financial_report_id.date_to or a.date <= financial_report_id.date_to)
            account_entries = self._get_entries_by_type(
                account_move_lines,
                accounts_by_type,
                account_types.values(),
            )
            fiscal_year_start = fields.Date.to_date(date_to).replace(month=1, day=1)
            fiscal_year_lines = account_move_lines.filtered(
                lambda line: line.date >= fiscal_year_start
            )
            fiscal_account_types = ('income', 'income_other', 'expense_direct_cost',
                                    'expense', 'expense_depreciation',
                                    'equity_unaffected', 'equity')
            fiscal_entries = self._get_entries_by_type(
                fiscal_year_lines,
                accounts_by_type,
                fiscal_account_types,
            )
            current_year_unallocated = (
                sum(float(entry['amount'].replace(',', '')) for kind in
                    ('income', 'income_other') for entry in fiscal_entries[kind][0])
                - sum(float(entry['amount'].replace(',', '')) for kind in
                    ('expense_direct_cost', 'expense', 'expense_depreciation')
                    for entry in fiscal_entries[kind][0])
                + sum(float(entry['amount'].replace(',', '')) for entry in
                    fiscal_entries['equity_unaffected'][0])
            )
            current_year_retained = sum(
                float(entry['amount'].replace(',', ''))
                for entry in fiscal_entries['equity'][0]
            )
            current_year_retained_entries = fiscal_entries['equity'][0]
            total_retained = sum(
                float(entry['amount'].replace(',', ''))
                for entry in account_entries['equity'][0]
            )
            total_unaffected = (
                sum(float(entry['amount'].replace(',', '')) for kind in
                    ('income', 'income_other') for entry in account_entries[kind][0])
                - sum(float(entry['amount'].replace(',', '')) for kind in
                    ('expense_direct_cost', 'expense', 'expense_depreciation')
                    for entry in account_entries[kind][0])
                + sum(float(entry['amount'].replace(',', '')) for entry in
                    account_entries['equity_unaffected'][0])
            )
            previous_year_unallocated = total_unaffected - current_year_unallocated
            previous_year_retained = total_retained - current_year_retained
            previous_year_retained_entries = []
            for account_entry in account_entries['equity'][0]:
                account_name = account_entry['name']
                current_entry = next(
                    (entry for entry in current_year_retained_entries
                     if entry['name'] == account_name),
                    {'amount': '0.00'},
                )
                previous_amount = (
                    float(account_entry['amount'].replace(',', ''))
                    - float(current_entry['amount'].replace(',', ''))
                )
                previous_year_retained_entries.append({
                    'name': account_name,
                    'amount': "{:,.2f}".format(previous_amount),
                })
            total_income = sum(
                float(entry['amount'].replace(',', '')) for account_type in
                ['income', 'income_other'] for entry in
                account_entries[account_type][0]) - sum(
                float(entry['amount'].replace(',', '')) for entry in
                account_entries['expense_direct_cost'][0])
            total_expense = sum(
                float(entry['amount'].replace(',', '')) for account_type in
                ['expense', 'expense_depreciation'] for entry in
                account_entries[account_type][0])
            total_current_asset = sum(
                float(entry['amount'].replace(',', '')) for account_type in
                ['asset_receivable', 'asset_current', 'asset_cash',
                 'asset_prepayments'] for entry in
                account_entries[account_type][0])
            total_assets = total_current_asset + sum(
                float(entry['amount'].replace(',', '')) for account_type in
                ['asset_fixed', 'asset_non_current'] for entry in
                account_entries[account_type][0])
            total_current_liability = sum(
                float(entry['amount'].replace(',', '')) for account_type in
                ['liability_current', 'liability_payable'] for entry in
                account_entries[account_type][0])
            total_liability = total_current_liability + sum(
                float(entry['amount'].replace(',', '')) for account_type in
                ['liability_non_current'] for entry in
                account_entries[account_type][0])
            total_unallocated_earning = (total_income - total_expense) + sum(
                float(entry['amount'].replace(',', '')) for account_type in
                ['equity_unaffected'] for entry in
                account_entries[account_type][0])
            total_equity = total_unallocated_earning + sum(
                float(entry['amount'].replace(',', '')) for account_type in
                ['equity'] for entry in account_entries[account_type][0])
            total = total_liability + total_equity
            data = {
                'total': total_income - total_expense,
                'total_expense': "{:,.2f}".format(total_expense),
                'total_income': "{:,.2f}".format(total_income),
                'total_current_asset': "{:,.2f}".format(total_current_asset),
                'total_assets': "{:,.2f}".format(total_assets),
                'total_current_liability': "{:,.2f}".format(
                    total_current_liability),
                'total_liability': "{:,.2f}".format(total_liability),
                'total_earnings': "{:,.2f}".format(
                    total_income - total_expense),
                'total_unallocated_earning': "{:,.2f}".format(
                    total_unallocated_earning),
                'current_year_unallocated_earnings': "{:,.2f}".format(current_year_unallocated),
                'previous_year_unallocated_earnings': "{:,.2f}".format(previous_year_unallocated),
                'current_year_retained_earnings': "{:,.2f}".format(current_year_retained),
                'previous_year_retained_earnings': "{:,.2f}".format(previous_year_retained),
                'current_year_retained_accounts': current_year_retained_entries,
                'previous_year_retained_accounts': previous_year_retained_entries,
                'total_retained_earnings': "{:,.2f}".format(total_retained),
                'total_equity': "{:,.2f}".format(total_equity),
                'total_balance': "{:,.2f}".format(total),
                **account_entries}
            datas.append(data)
        filters = self._get_filter_data()
        return data, filters, datas

    def _get_entries_by_type(self, account_move_lines, accounts_by_type,
                             account_types):
        """Build report lines for several account types in one move-line pass."""
        credit_balance_types = {
            'income', 'income_other', 'liability_payable',
            'liability_current', 'liability_non_current', 'equity',
            'equity_unaffected',
        }
        account_type_by_id = {}
        amounts_by_type = {}
        for account_type in account_types:
            amounts_by_type[account_type] = {}
            for account in accounts_by_type[account_type]:
                account_type_by_id[account.id] = account_type
                amounts_by_type[account_type][account.id] = 0.0

        for line in account_move_lines:
            account_type = account_type_by_id.get(line.account_id.id)
            if not account_type:
                continue
            amount = line.debit - line.credit
            if account_type in credit_balance_types:
                amount = -amount
            amounts_by_type[account_type][line.account_id.id] += amount

        entries_by_type = {}
        for account_type in account_types:
            entries = []
            total = 0.0
            for account in accounts_by_type[account_type]:
                amount = amounts_by_type[account_type][account.id]
                entries.append({
                    'name': "{} - {}".format(account.code, account.name),
                    'amount': "{:,.2f}".format(amount),
                })
                total += amount
            entries_by_type[account_type] = entries, "{:,.2f}".format(total)
        return entries_by_type

    def _get_entries(self, account_move_lines, account_ids, account_type):
        return self._get_entries_by_type(
            account_move_lines,
            {account_type: account_ids},
            (account_type,),
        )[account_type]

    def filter(self, vals):
        """
            Update the filter criteria based on the provided values.
            :param vals: A dictionary containing the filter values to update.
            :return: The updated record.
            """
        filter = []
        today = fields.Date.today()
        if vals == 'month':
            vals = {
                'date_from': get_month(today)[0].strftime("%Y-%m-%d"),
                'date_to': get_month(today)[1].strftime("%Y-%m-%d"),
            }
        elif vals == 'quarter':
            vals = {
                'date_from': get_quarter(today)[0].strftime("%Y-%m-%d"),
                'date_to': get_quarter(today)[1].strftime("%Y-%m-%d"),
            }
        elif vals == 'year':
            vals = {
                'date_from': get_fiscal_year(today)[0].strftime("%Y-%m-%d"),
                'date_to': get_fiscal_year(today)[1].strftime("%Y-%m-%d"),
            }
        elif vals == 'last-month':
            last_month_date = subtract(today, months=1)
            vals = {
                'date_from': get_month(last_month_date)[0].strftime(
                    "%Y-%m-%d"),
                'date_to': get_month(last_month_date)[1].strftime("%Y-%m-%d"),
            }
        elif vals == 'last-quarter':
            last_quarter_date = subtract(today, months=3)
            vals = {
                'date_from': get_quarter(last_quarter_date)[0].strftime(
                    "%Y-%m-%d"),
                'date_to': get_quarter(last_quarter_date)[1].strftime(
                    "%Y-%m-%d"),
            }
        elif vals == 'last-year':
            last_year_date = subtract(today, years=1)
            vals = {
                'date_from': get_fiscal_year(last_year_date)[0].strftime(
                    "%Y-%m-%d"),
                'date_to': get_fiscal_year(last_year_date)[1].strftime(
                    "%Y-%m-%d"),
            }
        if 'date_from' in vals:
            self.write({'date_from': vals['date_from']})
        if 'date_to' in vals:
            self.write({'date_to': vals['date_to']})
        if 'journal_ids' in vals:
            if int(vals['journal_ids']) in self.journal_ids.mapped('id'):
                self.update({'journal_ids': [(3, int(vals['journal_ids']))]})
            else:
                self.write({'journal_ids': [(4, int(vals['journal_ids']))]})
            filter.append({'journal_ids': self.journal_ids.mapped('code')})
        if 'account_ids' in vals:
            if int(vals['account_ids']) in self.account_ids.mapped('id'):
                self.update(
                    {'account_ids': [(3, int(vals['account_ids']))]})
            else:
                self.write({'account_ids': [(4, int(vals['account_ids']))]})
            filter.append({'account_ids': self.account_ids.mapped('name')})
        if 'analytic_ids' in vals:
            if int(vals['analytic_ids']) in self.analytic_ids.mapped('id'):
                self.update(
                    {'analytic_ids': [(3, int(vals['analytic_ids']))]})
            else:
                self.write({'analytic_ids': [(4, int(vals['analytic_ids']))]})
            filter.append({'analytic_ids': self.analytic_ids.mapped('name')})
        if 'target' in vals:
            self.write({'target_move': vals['target']})
            filter.append({'target_move': self.target_move})
        return filter

    def _get_filter_data(self):
        """
            Retrieve the filter data for journals and accounts.

            :return: A dictionary containing the filter data.
            """
        journal_ids = self.env['account.journal'].search([])
        journal = [{'id': journal.id, 'name': journal.name} for journal in
                   journal_ids]

        account_ids = self.env['account.account'].search([])
        account = [{'id': account.id, 'name': account.name} for account in
                   account_ids]

        analytic_ids = self.env['account.analytic.account'].search([])
        analytic = [{'id': analytic.id, 'name': analytic.name} for analytic in
                    analytic_ids]

        filter = {
            'journal': journal,
            'account': account,
            'analytic': analytic
        }
        return filter

    @api.model
    def comparison_filter(self, options, count):
        today = fields.Date.today()
        if not count:
            raise ValidationError(_("Please select the count."))
        last_month_date_list = []
        for i in range(1, int(count) + 1):
            last_month_date = subtract(today, months=i)
            vals = {
                'date_from': get_month(last_month_date)[0].strftime(
                    "%Y-%m-%d"),
                'date_to': get_month(last_month_date)[1].strftime("%Y-%m-%d"),
            }
            last_month_date_list.append(vals)
        return last_month_date_list

    @api.model
    def comparison_filter_year(self, options, count):
        today = fields.Date.today()
        if not count:
            raise ValidationError(_("Please select the count."))
        last_year_date_list = []
        for i in range(1, int(count) + 1):
            last_year_date = subtract(today, years=i)
            vals = {
                'date_from': get_fiscal_year(last_year_date)[0].strftime(
                    "%Y-%m-%d"),
                'date_to': get_fiscal_year(last_year_date)[1].strftime(
                    "%Y-%m-%d"),
            }
            last_year_date_list.append(vals)
        return last_year_date_list

    @api.model
    def get_xlsx_report(self, data, response, report_name, report_action):
        """Generate and return an XLSX report based on the provided data.
            :param data: The report data in JSON format.
            :param report_name: Name of the report.
            :param response: The response object to write the generated report to.
            """
        data = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sub_heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})
        side_heading_sub = workbook.add_format(
            {'align': 'left', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})
        side_heading_sub.set_indent(1)
        # Filter formats
        filter_heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '9px', 'border': 1,
             'bg_color': '#D3D3D3'})
        filter_text = workbook.add_format(
            {'align': 'left', 'font_size': '9px', 'border': 1})
        txt_name = workbook.add_format({'font_size': '10px', 'border': 1})
        txt_name_left = workbook.add_format(
            {'align': 'left', 'font_size': '10px', 'border': 1})
        txt_name.set_indent(2)
        sheet.set_column(0, 0, 30)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)
        col = 0
        is_profit_and_loss = report_action == 'account_dynamic_reports.action_dynamic_profit_and_loss'
        current_row = 0
        if is_profit_and_loss:
            sheet.write('A3:b4', report_name, sub_heading)
            sheet.write(5, col, '', sub_heading)
            for date in data['year']:
                sheet.write(4, col + 1, date, sub_heading)
                sheet.write(5, col + 1, 'Balance', sub_heading)
                col += 1
            col = 0

            # Report Title
            sheet.merge_range(current_row, 0, current_row, 5, report_name, sub_heading)
            current_row += 1
        if data:
            if is_profit_and_loss:

                # --- FILTERS TABLE BELOW REPORT NAME ---
                # Filter table headers
                sheet.write(current_row, 0, 'Date Range', filter_heading)
                sheet.write(current_row, 1, 'Comparison', filter_heading)
                sheet.write(current_row, 2, 'Account', filter_heading)
                sheet.write(current_row, 3, 'Journal', filter_heading)
                sheet.write(current_row, 4, 'Analytic Account', filter_heading)
                sheet.write(current_row, 5, 'Target move', filter_heading)
                current_row += 1

                # Filter values
                # Date Range
                date_range = ''
                if data.get('date_from') and data.get('date_to'):
                    date_range = f"{data.get('date_from')} – {data.get('date_to')}"
                elif data.get('date_range'):
                    date_range = data.get('date_range')
                else:
                    date_range = 'All'
                sheet.write(current_row, 0, date_range, filter_text)

                # Comparison
                comparison = data.get('comparison', '-') if data.get('comparison') else '-'
                sheet.write(current_row, 1, comparison, filter_text)

                # Account
                account_ids = data.get('account_ids')
                account_text = ', '.join(map(str, account_ids)) if account_ids else 'All'
                sheet.write(current_row, 2, account_text,filter_text)

                # Journal
                journal_ids = data.get('journal_ids')
                journal_text = ', '.join(map(str, journal_ids)) if journal_ids else 'All'
                sheet.write(current_row, 3, journal_text,filter_text)

                # Analytic Account
                analytic_ids = data.get('analytic_ids')
                analytic_text = ', '.join(map(str, analytic_ids)) if analytic_ids else 'All'
                sheet.write(current_row, 4, analytic_text,filter_text)

                # Target move
                target_text = data.get('target', 'All') if data.get('target') else 'All'
                sheet.write(current_row, 5, target_text, filter_text)

                current_row += 2  # Leave a blank row

                # --- REPORT TITLE ---

                sheet.write(current_row, col, 'Net Profit', sub_heading)
                for datas in data['datas']:
                    sheet.write(current_row, col + 1, datas['total'], side_heading_sub)
                    current_row += 1
                    col += 1
                col = 0
                sheet.write(current_row, col, 'Income', side_heading_sub)
                sheet.write(current_row, col + 1, ' ', side_heading_sub)
                current_row += 1
                sheet.write(current_row, col, 'Operating Income', txt_name_left)
                for datas in data['datas']:
                    sheet.write(current_row, col + 1, datas['income'][1], txt_name)
                    current_row += 1
                    col += 1
                row = current_row
                index = 0
                for datas in data['datas']:
                    if index == 0:
                        for accounts in datas['income'][0]:
                            account_name = accounts['name']
                            account_value = 0
                            for datas in data['datas']:
                                for account in datas['income'][0]:
                                    if account_name == account['name'] and \
                                            account['amount'] != '0.00':
                                        account_value = 1
                            if account_value == 1:
                                row += 1
                                col = 0
                                sheet.write(row, col, accounts['name'],
                                            txt_name)
                                for datas in data['datas']:
                                    for account in datas['income'][0]:
                                        if account_name == account['name']:
                                            sheet.write(row, col + 1,
                                                        account['amount'],
                                                        txt_name)
                                            col += 1
                    index += 1
                row += 1
                col = 0
                sheet.write(row, col, 'Cost of Revenue', txt_name_left)
                for datas in data['datas']:
                    sheet.write(row, col + 1, datas['expense_direct_cost'][1],
                                txt_name)
                    col += 1
                index = 0
                for datas in data['datas']:
                    if index == 0:
                        for accounts in datas['expense_direct_cost'][0]:
                            account_name = accounts['name']
                            account_value = 0
                            for datas in data['datas']:
                                for account in datas['expense_direct_cost'][0]:
                                    if account_name == account['name'] and \
                                            account['amount'] != '0.00':
                                        account_value = 1
                            if account_value == 1:
                                row += 1
                                col = 0
                                sheet.write(row, col, accounts['name'],
                                            txt_name)
                                for datas in data['datas']:
                                    for account in \
                                            datas['expense_direct_cost'][0]:
                                        if account_name == account['name']:
                                            sheet.write(row, col + 1,
                                                        account['amount'],
                                                        txt_name)
                                            col += 1
                    index += 1
                row += 1
                col = 0
                sheet.write(row, col, 'Other Income', txt_name_left)
                for datas in data['datas']:
                    sheet.write(row, col + 1, datas['income_other'][1],
                                txt_name)
                    col += 1
                index = 0
                for datas in data['datas']:
                    if index == 0:
                        for accounts in datas['income_other'][0]:
                            account_name = accounts['name']
                            account_value = 0
                            for datas in data['datas']:
                                for account in datas['income_other'][0]:
                                    if account_name == account['name'] and \
                                            account['amount'] != '0.00':
                                        account_value = 1
                            if account_value == 1:
                                row += 1
                                col = 0
                                sheet.write(row, col, accounts['name'],
                                            txt_name)
                                for datas in data['datas']:
                                    for account in datas['income_other'][0]:
                                        if account_name == account['name']:
                                            sheet.write(row, col + 1,
                                                        account['amount'],
                                                        txt_name)
                                            col += 1
                    index += 1
                row += 1
                col = 0
                sheet.write(row, col, 'Total Income', side_heading_sub)
                for datas in data['datas']:
                    sheet.write(row, col + 1, datas['total_income'],
                                side_heading_sub)
                    col += 1
                row += 1
                col = 0
                sheet.write(row, col, 'Expense', side_heading_sub)
                sheet.write(row, col + 1, '', side_heading_sub)
                row += 1
                col = 0
                sheet.write(row, col, 'Expense', txt_name_left)
                for datas in data['datas']:
                    sheet.write(row, col + 1, datas['expense'][1], txt_name)
                    col += 1
                index = 0
                for datas in data['datas']:
                    if index == 0:
                        for accounts in datas['expense'][0]:
                            account_name = accounts['name']
                            account_value = 0
                            for datas in data['datas']:
                                for account in datas['expense'][0]:
                                    if account_name == account['name'] and \
                                            account['amount'] != '0.00':
                                        account_value = 1
                            if account_value == 1:
                                row += 1
                                col = 0
                                sheet.write(row, col, accounts['name'],
                                            txt_name)
                                for datas in data['datas']:
                                    for account in datas['expense'][0]:
                                        if account_name == account['name']:
                                            sheet.write(row, col + 1,
                                                        account['amount'],
                                                        txt_name)
                                            col += 1
                    index += 1
                row += 1
                col = 0
                sheet.write(row, col, 'Depreciation', txt_name_left)
                for datas in data['datas']:
                    sheet.write(row, col + 1, datas['expense_depreciation'][1],
                                txt_name)
                    col += 1
                index = 0
                for datas in data['datas']:
                    if index == 0:
                        for accounts in datas['expense_depreciation'][0]:
                            account_name = accounts['name']
                            account_value = 0
                            for datas in data['datas']:
                                for account in datas['expense_depreciation'][
                                    0]:
                                    if account_name == account['name'] and \
                                            account['amount'] != '0.00':
                                        account_value = 1
                            if account_value == 1:
                                row += 1
                                col = 0
                                sheet.write(row, col, accounts['name'],
                                            txt_name)
                                for datas in data['datas']:
                                    for account in \
                                            datas['expense_depreciation'][
                                                0]:
                                        if account_name == account['name']:
                                            sheet.write(row, col + 1,
                                                        account['amount'],
                                                        txt_name)
                                            col += 1
                    index += 1
                row += 1
                col = 0
                sheet.write(row, col, 'Total Expenses', side_heading_sub)
                for datas in data['datas']:
                    sheet.write(row, col + 1, datas['total_expense'],
                                side_heading_sub)
                    col += 1
            else:
                # Balance Sheet export uses the same row model as the web/PDF
                # renderer, keeping hierarchy, indentation, amount colors, and
                # section bands consistent across outputs.
                export_rows = data.get('export_rows') or []
                periods = data.get('year') or []
                company_name = data.get('companyName') or ''
                last_col = max(1, len(periods))

                title_fmt = workbook.add_format({
                    'bold': True, 'font_size': 12, 'align': 'left',
                    'valign': 'vcenter'
                })
                company_fmt = workbook.add_format({
                    'bold': True, 'font_size': 9, 'font_color': '#D0D3D8',
                    'align': 'left'
                })
                period_fmt = workbook.add_format({
                    'bold': True, 'font_size': 9, 'align': 'center',
                    'valign': 'vcenter', 'border': 1,
                    'border_color': '#D7DBE0'
                })
                period_label_fmt = workbook.add_format({
                    'bold': True, 'font_size': 9, 'align': 'right'
                })
                section_fmt = workbook.add_format({
                    'bold': True, 'font_size': 10, 'font_color': '#172B4D',
                    'bg_color': '#D6D8DB', 'align': 'left',
                    'valign': 'vcenter'
                })
                section_amount_fmt = workbook.add_format({
                    'bold': True, 'font_size': 10, 'font_color': '#172B4D',
                    'bg_color': '#D6D8DB', 'align': 'right',
                    'valign': 'vcenter', 'num_format': '#,##0.00'
                })
                label_formats = {}
                for level, indent in enumerate([0, 1, 2, 3, 4]):
                    label_formats[(level, False)] = workbook.add_format({
                        'font_size': 10, 'font_color': '#172B4D',
                        'bottom': 1, 'bottom_color': '#D9DDE3',
                        'align': 'left', 'valign': 'vcenter'
                    })
                    label_formats[(level, False)].set_indent(indent)
                    label_formats[(level, True)] = workbook.add_format({
                        'bold': True, 'font_size': 10, 'font_color': '#172B4D',
                        'bottom': 1, 'bottom_color': '#D9DDE3',
                        'align': 'left', 'valign': 'vcenter'
                    })
                    label_formats[(level, True)].set_indent(indent)
                amount_formats = {
                    ('normal', False): workbook.add_format({
                        'font_size': 10, 'align': 'right',
                        'bottom': 1, 'bottom_color': '#D9DDE3',
                        'num_format': '#,##0.00'
                    }),
                    ('normal', True): workbook.add_format({
                        'bold': True, 'font_size': 10, 'align': 'right',
                        'bottom': 1, 'bottom_color': '#D9DDE3',
                        'num_format': '#,##0.00'
                    }),
                    ('negative', False): workbook.add_format({
                        'font_size': 10, 'font_color': '#C0392B',
                        'align': 'right', 'bottom': 1,
                        'bottom_color': '#D9DDE3', 'num_format': '#,##0.00'
                    }),
                    ('negative', True): workbook.add_format({
                        'bold': True, 'font_size': 10, 'font_color': '#C0392B',
                        'align': 'right', 'bottom': 1,
                        'bottom_color': '#D9DDE3', 'num_format': '#,##0.00'
                    }),
                    ('zero', False): workbook.add_format({
                        'font_size': 10, 'font_color': '#C9D0D8',
                        'align': 'right', 'bottom': 1,
                        'bottom_color': '#D9DDE3', 'num_format': '#,##0.00'
                    }),
                    ('zero', True): workbook.add_format({
                        'bold': True, 'font_size': 10, 'font_color': '#C9D0D8',
                        'align': 'right', 'bottom': 1,
                        'bottom_color': '#D9DDE3', 'num_format': '#,##0.00'
                    }),
                }
                blank_fmt = workbook.add_format({
                    'bottom': 1, 'bottom_color': '#D9DDE3'
                })

                def parse_amount(value):
                    if value in (None, ''):
                        return None
                    try:
                        return float(str(value).replace(',', ''))
                    except (TypeError, ValueError):
                        return None

                def amount_kind(value):
                    number = parse_amount(value)
                    if number is None:
                        return 'normal'
                    if number < 0:
                        return 'negative'
                    if number == 0:
                        return 'zero'
                    return 'normal'

                def write_amount(row_no, col_no, value, row_type, bold):
                    if value in (None, ''):
                        fmt = section_amount_fmt if row_type in ('section', 'section_total') else blank_fmt
                        sheet.write(row_no, col_no, '', fmt)
                        return
                    number = parse_amount(value)
                    if row_type in ('section', 'section_total'):
                        fmt = section_amount_fmt
                    else:
                        fmt = amount_formats[(amount_kind(value), bool(bold))]
                    if number is None:
                        sheet.write(row_no, col_no, value, fmt)
                    else:
                        sheet.write_number(row_no, col_no, number, fmt)

                sheet.set_column(0, 0, 42)
                for idx in range(len(periods)):
                    sheet.set_column(idx + 1, idx + 1, 18)

                row = 0
                sheet.merge_range(row, 0, row, last_col, report_name, title_fmt)
                row += 1
                if company_name:
                    sheet.merge_range(row, 0, row, last_col, company_name, company_fmt)
                    row += 1
                row += 1
                sheet.write(row, 0, '', period_fmt)
                for idx, period in enumerate(periods):
                    sheet.write(row, idx + 1, period, period_fmt)
                row += 1
                sheet.write(row, 0, '', period_label_fmt)
                for idx, period in enumerate(periods):
                    sheet.write(row, idx + 1, 'Balance', period_label_fmt)
                row += 1

                if not export_rows:
                    sheet.write(row, 0, 'No Balance Sheet data available.', txt_name_left)
                for report_row in export_rows:
                    row_type = report_row.get('type') or 'line'
                    level = int(report_row.get('level') or 0)
                    bold = bool(report_row.get('bold') or row_type in (
                        'section', 'section_total', 'subsection', 'total',
                        'group_total', 'grand_total'
                    ))
                    if row_type in ('section', 'section_total') and row > 5:
                        row += 1
                    label_fmt = section_fmt if row_type in ('section', 'section_total') else label_formats[(min(level, 4), bold)]
                    sheet.set_row(row, 22 if row_type in ('section', 'section_total') else 21)
                    sheet.write(row, 0, report_row.get('label') or '', label_fmt)
                    values = report_row.get('values') or []
                    for idx in range(len(periods)):
                        value = values[idx] if idx < len(values) else ''
                        write_amount(row, idx + 1, value, row_type, bold)
                    row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
