from odoo import models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _sync_and_notify(self, method_name):
        self.ensure_one()
        result = getattr(self.env['id.region.sync.service'], method_name)()
        return result

    def action_sync_indonesia_regions(self):
        return self._sync_and_notify('action_sync_all_regions')

    def action_sync_indonesia_provinces(self):
        return self._sync_and_notify('action_sync_provinces')

    def action_sync_indonesia_cities(self):
        return self._sync_and_notify('action_sync_cities')

    def action_sync_indonesia_districts(self):
        return self._sync_and_notify('action_sync_districts')

    def action_sync_indonesia_villages(self):
        return self._sync_and_notify('action_sync_villages')

    def action_sync_indonesia_districts_scoped(self):
        self.ensure_one()
        # Force full sync for stability: ignore province scope.
        return self._sync_and_notify('action_sync_districts')

    def action_sync_indonesia_villages_scoped(self):
        self.ensure_one()
        # Force full sync for stability: ignore province scope.
        return self._sync_and_notify('action_sync_villages')
