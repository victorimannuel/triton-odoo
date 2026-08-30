from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveCancelWizard(models.TransientModel):
    _name = 'account.move.cancel.wizard'
    _description = 'Wizard to Cancel or Delete Journal Entries'

    action_type = fields.Selection([
        ('cancel', 'Cancel Entries'),
        ('delete', 'Cancel and Delete Entries')
    ], string='Action', required=True, default='cancel')

    def action_confirm(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return

        moves = self.env['account.move'].browse(active_ids)
        if not moves:
            return

        # 1. Always cancel first
        moves.button_cancel()

        # 2. Delete if requested
        if self.action_type == 'delete':
            # Unlink usually requires the state to be 'cancel' or 'draft'.
            # button_cancel sets it to 'cancel'.
            moves.unlink()

        return {'type': 'ir.actions.act_window_close'}
