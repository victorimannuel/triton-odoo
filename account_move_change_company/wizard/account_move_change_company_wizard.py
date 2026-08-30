from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveChangeCompanyWizard(models.TransientModel):
    _name = 'account.move.change.company.wizard'
    _description = 'Transfer Invoices/Entries to Another Company'

    invoice_ids = fields.Many2many(
        'account.move',
        relation='acc_move_chg_company_wizard_rel',
        string='Moves',
    )
    current_company_id = fields.Many2one(
        'res.company',
        string='Current Company',
        readonly=True,
    )
    destination_company_id = fields.Many2one(
        'res.company',
        string='Destination Company',
        required=True,
        domain="[('id', '!=', current_company_id)]",
    )

    # Summary counts (computed after dest company is chosen)
    invoice_count = fields.Integer(compute='_compute_summary')
    payment_count = fields.Integer(compute='_compute_summary')
    line_count = fields.Integer(compute='_compute_summary')

    @api.depends('invoice_ids')
    def _compute_summary(self):
        for wizard in self:
            all_moves, all_payments = wizard._get_full_record_set(wizard.invoice_ids)
            wizard.invoice_count = len(wizard.invoice_ids)
            wizard.payment_count = len(all_payments)
            wizard.line_count = len(all_moves.mapped('line_ids'))

    def _get_full_record_set(self, initial_moves):
        all_moves = initial_moves
        all_payments = self.env['account.payment']
        
        while True:
            # Find payments linked by reconciliation + origin_payment_id
            new_payments = self._get_linked_payments(all_moves) | all_moves.mapped('origin_payment_id')
            new_payments -= all_payments
            
            if not new_payments:
                break
            all_payments |= new_payments
            
            # Find moves linked to these payments
            new_moves = new_payments.mapped('move_id')
            new_moves -= all_moves
            
            if not new_moves:
                break
            all_moves |= new_moves
            
        return all_moves, all_payments

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            raise UserError(_("Please select at least one invoice or entry."))

        moves = self.env['account.move'].browse(active_ids)
        companies = moves.mapped('company_id')
        if len(companies) > 1:
            raise UserError(_(
                "All selected records must belong to the same company.\n"
                "The selection spans: %s"
            ) % ', '.join(companies.mapped('name')))

        res['invoice_ids'] = [(6, 0, moves.ids)]
        res['current_company_id'] = companies[:1].id
        return res

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_linked_payments(self, moves):
        """Return account.payment records linked to these moves via reconciliation."""
        move_line_ids = moves.mapped('line_ids').ids
        partials = self.env['account.partial.reconcile'].sudo().search([
            '|',
            ('debit_move_id', 'in', move_line_ids),
            ('credit_move_id', 'in', move_line_ids),
        ])
        reconciled_line_ids = (
            partials.mapped('debit_move_id') | partials.mapped('credit_move_id')
        )
        return reconciled_line_ids.mapped('payment_id')

    def _remap_account(self, account, dest_company, account_cache):
        """Return the matching account in dest_company by code. Raise if not found."""
        code = account.code
        if code not in account_cache:
            dest_account = self.env['account.account'].sudo().search([
                ('code', '=', code),
                ('company_ids', 'in', dest_company.id),
            ], limit=1)
            account_cache[code] = dest_account
        return account_cache[code]

    def _remap_tax(self, tax, dest_company, tax_cache):
        """Return matching tax in dest_company by name. Return False if not found."""
        key = tax.name
        if key not in tax_cache:
            dest_tax = self.env['account.tax'].sudo().search([
                ('name', '=', tax.name),
                ('company_id', '=', dest_company.id),
            ], limit=1)
            tax_cache[key] = dest_tax
        return tax_cache[key]

    def _remap_journal(self, journal, dest_company, journal_cache):
        """Return matching journal in dest_company by type. Raise if not found."""
        jtype = journal.type
        if jtype not in journal_cache:
            dest_journal = self.env['account.journal'].sudo().search([
                ('type', '=', jtype),
                ('company_id', '=', dest_company.id),
            ], limit=1)
            journal_cache[jtype] = dest_journal
        return journal_cache[jtype]

    # ------------------------------------------------------------------
    # Main transfer
    # ------------------------------------------------------------------

    def action_transfer(self):
        self.ensure_one()

        if self.current_company_id == self.destination_company_id:
            raise UserError(_("Destination company must differ from the current company."))

        dest = self.destination_company_id
        all_moves, payments = self._get_full_record_set(self.invoice_ids)

        # --- Phase 1: Pre-compute all required mappings to avoid mid-write flushes ---
        all_lines = all_moves.mapped('line_ids')
        account_cache = {}
        tax_cache = {}
        journal_cache = {}

        missing_accounts = []
        for line in all_lines:
            if line.account_id:
                mapped = self._remap_account(line.account_id, dest, account_cache)
                if not mapped and line.account_id.code not in missing_accounts:
                    missing_accounts.append(line.account_id.code)

        if missing_accounts:
            raise UserError(_(
                "The following account codes do not exist in '%s'.\n"
                "Please create them first:\n\n%s"
            ) % (dest.name, '\n'.join(missing_accounts)))

        missing_journals = []
        for move in all_moves:
            if move.journal_id:
                mapped = self._remap_journal(move.journal_id, dest, journal_cache)
                if not mapped and move.journal_id.type not in missing_journals:
                    missing_journals.append(move.journal_id.type)

        for payment in payments:
            if payment.journal_id:
                mapped = self._remap_journal(payment.journal_id, dest, journal_cache)
                if not mapped and payment.journal_id.type not in missing_journals:
                    missing_journals.append(payment.journal_id.type)

        if missing_journals:
            raise UserError(_(
                "No journal of type(s) %s found in '%s'.\n"
                "Please create the appropriate journals first."
            ) % (', '.join(missing_journals), dest.name))
            
        # Pre-cache taxes
        for line in all_lines:
            if line.tax_ids:
                for tax in line.tax_ids:
                    self._remap_tax(tax, dest, tax_cache)
            if line.tax_line_id:
                self._remap_tax(line.tax_line_id, dest, tax_cache)

        posted_move_ids = [m.id for m in all_moves if m.state == 'posted']

        # --- Phase 2: Teleport EVERY field via SQL to bypass ALL business logic/computes ---
        for payment in payments:
            dest_journal = journal_cache[payment.journal_id.type]
            self.env.cr.execute(
                "UPDATE account_payment SET company_id = %s, journal_id = %s WHERE id = %s", 
                (dest.id, dest_journal.id, payment.id)
            )
            
        for move in all_moves:
            dest_journal = journal_cache[move.journal_id.type]
            # Reset name to '/' if posted so it can get a new sequence
            name_val = '/' if (move.id in posted_move_ids and move.name and move.name != '/') else move.name
            
            self.env.cr.execute(
                "UPDATE account_move SET company_id = %s, journal_id = %s, fiscal_position_id = NULL, name = %s WHERE id = %s", 
                (dest.id, dest_journal.id, name_val, move.id)
            )
            self.env.cr.execute(
                "UPDATE account_move_line SET company_id = %s, journal_id = %s WHERE move_id = %s", 
                (dest.id, dest_journal.id, move.id)
            )

        for line in all_lines:
            new_acc_id = account_cache[line.account_id.code].id if line.account_id else None
            new_tax_line_id = tax_cache.get(line.tax_line_id.name).id if line.tax_line_id and tax_cache.get(line.tax_line_id.name) else None
            
            set_clauses = []
            params = []
            if new_acc_id:
                set_clauses.append("account_id = %s")
                params.append(new_acc_id)
            if line.tax_line_id:
                set_clauses.append("tax_line_id = %s")
                params.append(new_tax_line_id)
                
            if set_clauses:
                params.append(line.id)
                self.env.cr.execute(f"UPDATE account_move_line SET {', '.join(set_clauses)} WHERE id = %s", params)

            if line.tax_ids:
                remapped_tax_ids = []
                for tax in line.tax_ids:
                    t = tax_cache.get(tax.name)
                    if t:
                        remapped_tax_ids.append(t.id)
                        
                if remapped_tax_ids:
                    self.env.cr.execute("DELETE FROM account_move_line_account_tax_rel WHERE account_move_line_id = %s", (line.id,))
                    for t_id in set(remapped_tax_ids):
                        self.env.cr.execute("INSERT INTO account_move_line_account_tax_rel (account_move_line_id, account_tax_id) VALUES (%s, %s)", (line.id, t_id))

        # --- Phase 3: Finalize ---
        # Force the ORM to recognize the SQL changes
        self.env.invalidate_all()
        
        # Generate new sequences for posted moves that had their names reset to '/'
        if posted_move_ids:
            moves_to_sequence = self.env['account.move'].browse(posted_move_ids).filtered(lambda m: m.name == '/')
            for move in moves_to_sequence:
                move._set_next_sequence()

        return {'type': 'ir.actions.act_window_close'}
