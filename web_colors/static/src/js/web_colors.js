/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";
import { onMounted } from "@odoo/owl";

function getActiveCompanyTheme() {
    const company = user.activeCompany;
    if (!company) {
        return null;
    }

    const darkMode = document.cookie.includes('color_scheme=dark');
    return {
        brand: darkMode ? (company.color_brand_dark || '#243742') : (company.color_brand_light || '#243742'),
        primary: darkMode ? (company.color_primary_dark || '#5D8DA8') : (company.color_primary_light || '#5D8DA8'),
        success: darkMode ? (company.color_success_dark || '#1DC959') : (company.color_success_light || '#28A745'),
        info: darkMode ? (company.color_info_dark || '#6AB5FB') : (company.color_info_light || '#17A2B8'),
        warning: darkMode ? (company.color_warning_dark || '#FBB56A') : (company.color_warning_light || '#FFAC00'),
        danger: darkMode ? (company.color_danger_dark || '#FF5757') : (company.color_danger_light || '#DC3545'),
    };
}

function applyWebColors(container = document) {
    const theme = getActiveCompanyTheme();
    const navbar = container.querySelector('.o_main_navbar');
    if (!theme) {
        return;
    }
    const root = document.documentElement;

    root.style.setProperty('--wc-brand', theme.brand);
    root.style.setProperty('--wc-primary', theme.primary);
    root.style.setProperty('--wc-success', theme.success);
    root.style.setProperty('--wc-info', theme.info);
    root.style.setProperty('--wc-warning', theme.warning);
    root.style.setProperty('--wc-danger', theme.danger);

    if (navbar) {
        navbar.style.setProperty('--NavBar-brand-color', '#ffffff');
        navbar.style.setProperty('--NavBar-entry-color', 'rgba(255, 255, 255, 0.9)');
        navbar.style.setProperty('--NavBar-entry-color--hover', '#ffffff');
        navbar.style.setProperty('--NavBar-entry-color--active', '#ffffff');
        navbar.style.setProperty('--NavBar-entry-backgroundColor', theme.brand);
        navbar.style.setProperty('--NavBar-entry-backgroundColor--hover', theme.primary);
        navbar.style.setProperty('--NavBar-entry-backgroundColor--focus', theme.primary);
        navbar.style.setProperty('--NavBar-entry-backgroundColor--active', theme.primary);
        navbar.style.setProperty('--NavBar-entry-borderColor-active', theme.primary);
        navbar.style.setProperty('--o-navbar-badge-bg', theme.success);
        navbar.style.setProperty('--o-navbar-badge-color', '#ffffff');
        navbar.style.setProperty('background-color', theme.brand);
        navbar.style.setProperty('border-bottom', `1px solid ${theme.primary}`);
    }

    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
        metaThemeColor.setAttribute('content', theme.brand);
    }
}

patch(NavBar.prototype, {
    setup() {
        super.setup();
        onMounted(() => {
            applyWebColors(this.el);
        });
    },
});

patch(NavBar, {
    template: 'web.NavBar',
});

applyWebColors();
document.addEventListener('DOMContentLoaded', applyWebColors);
