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
                    try:
                        light_brand = company.color_brand_light
                        light_primary = company.color_primary_light
                        light_success = company.color_success_light
                        light_info = company.color_info_light
                        light_warning = company.color_warning_light
                        light_danger = company.color_danger_light
                        dark_brand = company.color_brand_dark
                        dark_primary = company.color_primary_dark
                        dark_success = company.color_success_dark
                        dark_info = company.color_info_dark
                        dark_warning = company.color_warning_dark
                        dark_danger = company.color_danger_dark
                    except psycopg2_errors.UndefinedColumn:
                        light_brand = '#243742'
                        light_primary = '#5D8DA8'
                        light_success = '#28A745'
                        light_info = '#17A2B8'
                        light_warning = '#FFAC00'
                        light_danger = '#DC3545'
                        dark_brand = '#243742'
                        dark_primary = '#5D8DA8'
                        dark_success = '#1DC959'
                        dark_info = '#6AB5FB'
                        dark_warning = '#FBB56A'
                        dark_danger = '#FF5757'
                    company_data.update({
                        'color_brand_light': light_brand or '#243742',
                        'color_primary_light': light_primary or '#5D8DA8',
                        'color_success_light': light_success or '#28A745',
                        'color_info_light': light_info or '#17A2B8',
                        'color_warning_light': light_warning or '#FFAC00',
                        'color_danger_light': light_danger or '#DC3545',
                        'color_brand_dark': dark_brand or '#243742',
                        'color_primary_dark': dark_primary or '#5D8DA8',
                        'color_success_dark': dark_success or '#1DC959',
                        'color_info_dark': dark_info or '#6AB5FB',
                        'color_warning_dark': dark_warning or '#FBB56A',
                        'color_danger_dark': dark_danger or '#FF5757',
                    })
        return result
