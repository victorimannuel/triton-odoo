/** @odoo-module **/
const { Component } = owl;
const now = new Date();
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";
import { session } from "@web/session";
import { cookie } from "@web/core/browser/cookie";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";
const actionRegistry = registry.category("actions");

class BalanceSheet extends owl.Component {
    async setup() {
        super.setup(...arguments);
        this.initial_render = true;
        this.orm = useService('orm');
        this.action = useService('action');
        this.tbody = useRef('tbody');
        this.posted = useRef('posted');
        this.period = useRef('periods');
        this.period_year = useRef('period_year');
        this.draft = useRef('draft');
        this.state = useState({
            data: null,
            filter_data: null,
            year : [now.getFullYear()],
            comparison: false,
            comparison_type: null,
            title: '',
            companyName: null,
            asOfDate: null,
            export_rows: [],
        });
        this.wizard_id = await this.orm.call("dynamic.balance.sheet.report", "create", [{}]) | null;
        this.load_data(self.initial_render = true);
    }
    async load_data() {
    /**
     * Loads the data for the balance sheet report.
     */
        var self = this;
        var action_title = self.props.action.display_name;
        try {
            var self = this;
            let data = await self.orm.call("dynamic.balance.sheet.report", "view_report", [this.wizard_id,this.state.comparison,this.state.comparison_type]);
            self.state.data = data[0]
            self.state.datas = data[2]
            self.state.export_rows = self._buildBalanceSheetExportRows(self.state.datas || [])
            self.state.filter_data = data[1]
            const [reportOptions] = await this.orm.read(
                'dynamic.balance.sheet.report', [this.wizard_id], ['date_to']
            );
            const cutoffDate = reportOptions?.date_to || new Date().toISOString().slice(0, 10);
            self.state.asOfDate = new Intl.DateTimeFormat('en-GB', {
                day: '2-digit', month: 'short', year: 'numeric',
            }).format(new Date(cutoffDate + 'T00:00:00'));
            if (!self.state.comparison) {
                self.state.year = ['As of ' + self.state.asOfDate];
            }
            self.state.title = action_title
            // Odoo stores the checked multi-company selection in the cids
            // cookie (id-id-id); it also supplies the report RPC context.
            const cookieCompanyIds = (cookie.get('cids') || '')
                .split('-')
                .map((id) => Number(id))
                .filter(Boolean);
            const companies = session.user_companies || {};
            const sessionCompanyIds = session.user_context?.allowed_company_ids || [];
            const companyIds = cookieCompanyIds.length
                ? [...new Set(cookieCompanyIds)]
                : sessionCompanyIds.length
                    ? [...new Set(sessionCompanyIds)]
                    : [companies.current_company].filter(Boolean);
            if (companyIds.length) {
                const selectedCompanies = await this.orm.read('res.company', companyIds, ['name']);
                self.state.companyName = selectedCompanies.map((company) => company.name).join(', ');
            } else {
                const [company] = await this.orm.searchRead('res.company', [], ['name'], { limit: 1 });
                self.state.companyName = company?.name || null;
            }
            self._scheduleReportPolish();
        }
        catch (el) {
            window.location.href
        }
    }
    async show_gl(ev) {
    /**
        * Shows the General Ledger view by triggering an action.
        *
        * @param {Event} ev - The event object triggered by the action.
        * @returns {Promise} - A promise that resolves to the result of the action.
        */
        return this.action.doAction({
            type: 'ir.actions.client',
            name: 'General Ledger',
            tag: 'gen_l',
        });
    }
    async print_pdf(ev) {
        /**
        * Print PDF Method
        * This method is triggered when the "Print PDF" button is clicked.
        * It retrieves the report data and performs an action to generate and download a PDF report.
        */
        ev.preventDefault();
        var self = this;
        let data = await self.orm.call("dynamic.balance.sheet.report", "view_report", [this.wizard_id,this.state.comparison,this.state.comparison_type]);
        self.state.data = data[0]
        self.state.datas = data[2]
            self.state.export_rows = self._buildBalanceSheetExportRows(self.state.datas || [])
        return self.action.doAction({
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'account_dynamic_reports.balance_sheet',
            'report_file': 'account_dynamic_reports.balance_sheet',
            'data': {
                'data': self.state,
                'report_name': self.props.action.display_name
            },
            'display_name': self.props.action.display_name,
        });
    }
    async print_xlsx(ev) {
         /**
         * Generates and downloads an XLSX report based on the profit and loss data.
         *
         * @param {Event} ev - The event object triggered by the action.
         */
        var self = this;
        let data = await self.orm.call("dynamic.balance.sheet.report", "view_report", [this.wizard_id,this.state.comparison,this.state.comparison_type]);
        self.state.data = data[0]
        self.state.datas = data[2]
            self.state.export_rows = self._buildBalanceSheetExportRows(self.state.datas || [])
        var action = {
            'data': {
                'model': 'dynamic.balance.sheet.report',
                'data': JSON.stringify(self.state),
                'output_format': 'xlsx',
                'report_name': self.props.action.display_name,
                'report_action': self.props.action.xml_id,
            },
        };
        BlockUI;
        await download({
            url: '/xlsx_report',
            data: action.data,
            complete: () => unblockUI,
            error: (error) => self.call('crash_manager', 'rpc_error', error),
        });
    }
    async apply_journal(ev) {
     /**
        * Applies journal filtering based on the selected option in an event target.
        *
        * @param {Event} ev - The event object triggered by the action.
        */
        self = this
        if (ev.target.classList.contains("selected-filter")) {
            ev.target.classList.remove('selected-filter')
        }
        else {
            ev.target.classList.add('selected-filter')
        }
        this.filter = ({
            'journal_ids': ev.target.querySelector('span').textContent,
        })
        let res = await self.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter,]);
        ev.delegateTarget.querySelector('.code').innerHTML = res[0].journal_ids;
        self.initial_render = false;
        self.load_data(self.initial_render);
    }
    async apply_account(ev) {
     /**
        * Applies account filtering based on the selected option in an event target.
        *
        * @param {Event} ev - The event object triggered by the action.
        */
        self = this
        if (ev.target.classList.contains("selected-filter")) {
            ev.target.classList.remove('selected-filter')
        }
        else {
            ev.target.classList.add('selected-filter')
        }
        this.filter = ({
            'account_ids': ev.target.querySelector('span').textContent,
        })
        let res = await self.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter,]);
        ev.delegateTarget.querySelector('.account').innerHTML = res[0].account_ids;
        self.initial_render = false;
        self.load_data(self.initial_render);
    }
    async apply_analytic_accounts(ev) {
    /**
     * Applies analytic accounts filtering based on the selected option in an event target.
     *
     * @param {Event} ev - The event object triggered by the action.
     */
        self = this
        if (ev.target.classList.contains("selected-filter")) {
            ev.target.classList.remove('selected-filter')
        }
        else {
            ev.target.classList.add('selected-filter')
        }
        this.filter = ({
            'analytic_ids': ev.target.querySelector('span').textContent,
        })
        let res = await self.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter,]);
        ev.delegateTarget.querySelector('.analytic').innerHTML = res[0].analytic_ids;
        self.initial_render = false;
        self.load_data(self.initial_render);
    }
    async apply_entries(ev) {
    /**
     * Applies the selected entries filter and triggers data loading based on the selected filter class.
     * @param {Event} ev - The event object triggered by the entries filter selection.
     * @returns {Promise<void>} - A promise that resolves when the data is loaded.
     */
        self = this;
        ev.target.classList.add('selected-filter')
        if (ev.target.value == 'draft') {
            this.posted.el.classList.remove('selected-filter')
        } else {
            this.draft.el.classList.remove('selected-filter')
        }
        this.filter = ({
            'target': ev.target.value
        })
        let res = await self.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter,]);
        ev.delegateTarget.querySelector('.target').innerHTML = res[0].target_move;
        self.initial_render = false;
        self.load_data(self.initial_render);
    }
    async unfoldAll(ev) {
    /**
     * Unfolds or collapses all table rows based on the selected filter class.
     * @param {Event} ev - The event object triggered by the unfolding action.
     * @returns {void}
     */
        if (!ev.target.classList.contains("selected-filter")) {
            for (var length = 0; length < this.tbody.el.children.length; length++) {
                  this.tbody.el.children[length].classList.add('show')
            }
            ev.target.classList.add("selected-filter");
        } else {
            for (var length = 0; length < this.tbody.el.children.length; length++) {
                this.tbody.el.children[length].classList.remove('show')
            }
            ev.target.classList.remove("selected-filter");
        }
    }
    async apply_date(ev){
    /**
     * Applies the selected date filter and triggers data loading based on the selected filter value.
     * @param {Event} ev - The event object triggered by the date selection.
     * @returns {Promise<void>} - A promise that resolves when the data is loaded.
     */
        self = this
        if (ev.target.name === 'start_date') {
                this.filter = {
                    ...this.filter,
                    date_from: ev.target.value
                };
        } else if (ev.target.name === 'end_date') {
                this.filter = {
                    ...this.filter,
                    date_to: ev.target.value
                };
        } else if (ev.target.attributes["data-value"].value == 'month') {
                this.filter = ev.target.attributes["data-value"].value
        } else if (ev.target.attributes["data-value"].value == 'year') {
                this.filter = ev.target.attributes["data-value"].value
        } else if (ev.target.attributes["data-value"].value == 'quarter') {
            this.filter = ev.target.attributes["data-value"].value
        } else if (ev.target.attributes["data-value"].value == 'last-month') {
            this.filter = ev.target.attributes["data-value"].value
        } else if (ev.target.attributes["data-value"].value == 'last-year') {
            this.filter = ev.target.attributes["data-value"].value
        } else if (ev.target.attributes["data-value"].value == 'last-quarter') {
            this.filter = ev.target.attributes["data-value"].value
        }
        let res = await self.orm.call("dynamic.balance.sheet.report", "filter", [this.wizard_id, this.filter]);
        self.initial_render = false;
        self.load_data(self.initial_render);
        this.load_data(this.initial_render);
    }
    onPeriodChange(ev){
        this.period_year.el.value = ev.target.value
    }
    onPeriodYearChange(ev){
        this.period.el.value = ev.target.value
    }
    async applyComparisonPeriod(){
        this.state.comparison  = this.period.el.value
        this.state.comparison_type = "month"
        let monthNamesShort = [ "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" ]
        let res = await this.orm.call("dynamic.balance.sheet.report", "comparison_filter", [this.wizard_id, this.state.comparison]);
        this.state.year = [monthNamesShort[now.getMonth()]+'  ' + now.getFullYear()]
        for (var length = 0; length < res.length; length++) {
                const dateObject = new Date(res[length]['date_to']);
                this.state.year.push(monthNamesShort[dateObject.getMonth()]+'  ' + dateObject.getFullYear())
            }
        this.load_data(self.initial_render);
    }
    async applyComparisonYear(){
        this.state.comparison = this.period_year.el.value
        this.state.comparison_type = "year"
        let res = await this.orm.call("dynamic.balance.sheet.report", "comparison_filter_year", [this.wizard_id, this.state.comparison]);
        this.state.year = [now.getFullYear()]
        for (var length = 0; length < res.length; length++) {
                const dateObject = new Date(res[length]['date_to']);
                this.state.year.push(dateObject.getFullYear())
            }
        this.load_data(self.initial_render);
    }
    apply_comparison() {
        this.state.comparison = false
        this.state.comparison_type = null
        this.state.year = [now.getFullYear()]
    }

    _amountClass(value) {
        const text = String(value ?? '').trim();
        if (!text) {
            return '';
        }
        const numeric = Number(text.replace(/,/g, ''));
        if (!Number.isFinite(numeric)) {
            return '';
        }
        if (numeric < 0) {
            return 'o_tkg_bs_amount_negative';
        }
        if (numeric === 0) {
            return 'o_tkg_bs_amount_zero';
        }
        return '';
    }

    _makeExportRow(label, type, level, values, options = {}) {
        const normalizedValues = (values || []).map((value) => value ?? '');
        return {
            label,
            type,
            level,
            bold: Boolean(options.bold),
            values: normalizedValues,
            amount_classes: normalizedValues.map((value) => this._amountClass(value)),
        };
    }

    _getReportValue(dataset, key, index = 1) {
        const item = dataset?.[key];
        if (Array.isArray(item)) {
            return item[index] ?? '0.00';
        }
        return dataset?.[key] ?? '0.00';
    }

    _getAccountLines(dataset, key) {
        const item = dataset?.[key];
        if (Array.isArray(item)) {
            if (Array.isArray(item[0])) {
                return item[0];
            }
            return item;
        }
        return [];
    }

    _hasNonZeroAmount(account) {
        const value = String(account?.amount ?? '0.00').replace(/,/g, '');
        const numeric = Number(value);
        return Number.isFinite(numeric) && numeric !== 0;
    }

    _accountDetailRows(datas, key, level = 3) {
        const rows = [];
        const firstColumnAccounts = this._getAccountLines(datas?.[0], key);
        for (const account of firstColumnAccounts) {
            const accountName = account?.name;
            if (!accountName) {
                continue;
            }
            const shouldShow = datas.some((dataset) =>
                this._getAccountLines(dataset, key).some((line) =>
                    line?.name === accountName && this._hasNonZeroAmount(line)
                )
            );
            if (!shouldShow) {
                continue;
            }
            rows.push(this._makeExportRow(
                accountName,
                'detail',
                level,
                datas.map((dataset) => {
                    const line = this._getAccountLines(dataset, key).find((item) => item?.name === accountName);
                    return line?.amount ?? '0.00';
                })
            ));
        }
        return rows;
    }

    _pushAccountGroup(rows, datas, label, key, options = {}) {
        rows.push(this._makeExportRow(
            label,
            options.type || 'group',
            options.level ?? 2,
            datas.map((dataset) => this._getReportValue(dataset, key)),
            { bold: Boolean(options.bold) }
        ));
        rows.push(...this._accountDetailRows(datas, key, options.detailLevel ?? 3));
        if (options.totalLabel) {
            rows.push(this._makeExportRow(
                options.totalLabel,
                'group_total',
                options.totalLevel ?? 3,
                datas.map((dataset) => this._getReportValue(dataset, key)),
                { bold: true }
            ));
        }
    }

    _buildBalanceSheetExportRows(datas = []) {
        if (!Array.isArray(datas) || !datas.length) {
            return [];
        }
        const rows = [];
        const section = (label) => rows.push(this._makeExportRow(label, 'section', 0, datas.map(() => ''), { bold: true }));
        const sub = (label) => rows.push(this._makeExportRow(label, 'subsection', 1, datas.map(() => ''), { bold: true }));
        const line = (label, key, type = 'line', level = 2, bold = false) => rows.push(this._makeExportRow(
            label,
            type,
            level,
            datas.map((dataset) => this._getReportValue(dataset, key, undefined)),
            { bold }
        ));

        section('ASSETS');
        sub('Current Assets');
        this._pushAccountGroup(rows, datas, 'Bank and Cash Accounts', 'asset_cash', { totalLabel: 'Total Bank and Cash Accounts' });
        this._pushAccountGroup(rows, datas, 'Receivables', 'asset_receivable', { totalLabel: 'Total Receivables' });
        this._pushAccountGroup(rows, datas, 'Current Assets', 'asset_current', { totalLabel: 'Total Current Assets' });
        this._pushAccountGroup(rows, datas, 'Prepayments', 'asset_prepayments', { totalLabel: 'Total Prepayments' });
        line('Total Current Assets', 'total_current_asset', 'total', 2, true);
        this._pushAccountGroup(rows, datas, 'Plus Fixed Assets', 'asset_fixed', { totalLabel: 'Total Plus Fixed Assets' });
        this._pushAccountGroup(rows, datas, 'Plus Non-current Assets', 'asset_non_current', { totalLabel: 'Total Plus Non-current Assets' });
        line('Total ASSETS', 'total_assets', 'grand_total', 1, true);

        section('LIABILITIES');
        sub('Current Liabilities');
        this._pushAccountGroup(rows, datas, 'Current Liabilities', 'liability_current', { totalLabel: 'Total Current Liabilities' });
        this._pushAccountGroup(rows, datas, 'Payables', 'liability_payable', { totalLabel: 'Total Payables' });
        line('Total Current Liabilities', 'total_current_liability', 'total', 2, true);
        this._pushAccountGroup(rows, datas, 'Plus Non-current Liabilities', 'liability_non_current', { totalLabel: 'Total Plus Non-current Liabilities' });
        line('Total LIABILITIES', 'total_liability', 'grand_total', 1, true);

        section('EQUITY');
        sub('Unallocated Earnings');
        line('Current Year Unallocated Earnings', 'current_year_unallocated_earnings', 'line', 2, false);
        line('Previous Years Unallocated Earnings', 'previous_year_unallocated_earnings', 'line', 2, false);
        line('Total Unallocated Earnings', 'total_unallocated_earning', 'total', 2, true);
        sub('Retained Earnings');
        line('Current Year Retained Earnings', 'current_year_retained_earnings', 'group', 2, false);
        rows.push(...this._accountDetailRows(datas, 'current_year_retained_accounts', 3));
        line('Total Current Year Retained Earnings', 'current_year_retained_earnings', 'group_total', 3, true);
        line('Previous Years Retained Earnings', 'previous_year_retained_earnings', 'group', 2, false);
        rows.push(...this._accountDetailRows(datas, 'previous_year_retained_accounts', 3));
        line('Total Retained Earnings', 'total_retained_earnings', 'total', 2, true);
        line('Total EQUITY', 'total_equity', 'grand_total', 1, true);
        line('LIABILITIES + EQUITY', 'total_balance', 'section_total', 0, true);
        return rows;
    }

    _scheduleReportPolish() {
        window.setTimeout(() => this._polishRenderedReport(), 0);
    }

    _polishRenderedReport() {
        const root = this.tbody?.el?.closest('.o_tkg_balance_sheet');
        if (!root) {
            return;
        }
        root.querySelectorAll('.text-end span').forEach((node) => {
            node.classList.remove('o_tkg_bs_amount_negative', 'o_tkg_bs_amount_zero');
            const amountClass = this._amountClass(node.textContent);
            if (amountClass) {
                node.classList.add(amountClass);
            }
        });
        root.querySelectorAll('tbody tr').forEach((row) => {
            const toggler = row.querySelector('th > div[data-bs-toggle="collapse"]');
            const caret = toggler?.querySelector('.toggle-icon .fa:not(.o_tkg_toggle_placeholder)');
            if (!toggler || !caret || row.dataset.tkgRowToggleBound === '1') {
                row.classList.remove('o_tkg_clickable_row');
                return;
            }
            row.dataset.tkgRowToggleBound = '1';
            row.classList.add('o_tkg_clickable_row');
            row.addEventListener('click', (ev) => {
                if (ev.target.closest('.dropdown, .dropdown-menu, [data-bs-toggle="dropdown"]')) {
                    return;
                }
                if (ev.target.closest('div[data-bs-toggle="collapse"]') === toggler) {
                    return;
                }
                toggler.click();
            });
        });
    }

}
BalanceSheet.template = 'bls_template_new';
actionRegistry.add("bl_s", BalanceSheet);