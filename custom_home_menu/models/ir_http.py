from psycopg2 import errors as psycopg2_errors

from odoo import models


class IrHttp(models.AbstractModel):

    _inherit = 'ir.http'

    def session_info(self):
        result = super().session_info()
        if self.env.user._is_internal():
            allowed_companies = result.setdefault('user_companies', {}).setdefault(
                'allowed_companies',
                {},
            )
            for company in self.env.user.company_ids.with_context(bin_size=True):
                company_data = allowed_companies.get(company.id)
                if company_data is not None:
                    # Fall back to the default color if the database column has
                    # not been created yet on an upgraded deployment.
                    try:
                        background_color = company.custom_home_menu_background_color
                    except psycopg2_errors.UndefinedColumn:
                        background_color = None
                    company_data.update({
                        'custom_home_menu_background_color': (
                            background_color or '#e8d5f0'
                        ),
                    })
        return result
