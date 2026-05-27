from odoo import models, fields


class ResCompany(models.Model):
    
    _inherit = 'res.company'
    
    #----------------------------------------------------------
    # Fields
    #----------------------------------------------------------
    
    sidebar_image = fields.Binary(
        string='Sidebar Image',
        attachment=True
    )
    
    background_image = fields.Binary(
        string='Apps Menu Background Image',
        attachment=True
    )

    theme_color_sidebar_text = fields.Char(
        string='Sidebar Text Color',
        default='#DEE2E6',
    )

    theme_color_sidebar_active = fields.Char(
        string='Sidebar Active Color',
        default='#5D8DA8',
    )

    theme_color_sidebar_active_text = fields.Char(
        string='Sidebar Active Text Color',
        default='#FFFFFF',
    )

    theme_color_sidebar_background = fields.Char(
        string='Sidebar Background Color',
        default='#111827',
    )
