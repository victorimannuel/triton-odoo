/** @odoo-module **/

import { user } from "@web/core/user";

function applySidebarColors() {
    const company = user.activeCompany;
    const root = document.documentElement;
    if (!company || !root) {
        return;
    }
    root.style.setProperty('--tkg-sidebar-text', company.color_sidebar_text || '#DEE2E6');
    root.style.setProperty('--tkg-sidebar-active', company.color_sidebar_active || '#5D8DA8');
    root.style.setProperty('--tkg-sidebar-active-text', company.color_sidebar_active_text || '#FFFFFF');
    root.style.setProperty('--tkg-sidebar-background', company.color_sidebar_background || '#111827');
}

applySidebarColors();

document.addEventListener('DOMContentLoaded', applySidebarColors);
document.addEventListener('click', () => {
    window.requestAnimationFrame(applySidebarColors);
}, true);
