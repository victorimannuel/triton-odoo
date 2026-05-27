from odoo import models


class IrHttp(models.AbstractModel):

    _inherit = "ir.http"

    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------
    
    def _get_sidebar_colors(self):
        """Fallback colors while upgrading or when columns are missing."""
        return {
            'color_sidebar_text': '#DEE2E6',
            'color_sidebar_active': '#5D8DA8',
            'color_sidebar_active_text': '#FFFFFF',
            'color_sidebar_background': '#111827',
        }

    def session_info(self):
        result = super().session_info()
        if self.env.user._is_internal():
            for company in self.env.user.company_ids.with_context(bin_size=True):
                result['user_companies']['allowed_companies'][company.id].update({
                    'has_sidebar_image': bool(company.sidebar_image),
                    'color_sidebar_text': company.theme_color_sidebar_text or '#DEE2E6',
                    'color_sidebar_active': company.theme_color_sidebar_active or '#5D8DA8',
                    'color_sidebar_active_text': company.theme_color_sidebar_active_text or '#FFFFFF',
                    'color_sidebar_background': company.theme_color_sidebar_background or '#111827',
                })
        return result
