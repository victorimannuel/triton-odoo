from odoo import models

class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    def button_to_approve(self):
        res = super().button_to_approve()
        for request in self:
            if request.assigned_to:
                template = self.env.ref(
                    "purchase_request_email_approver.email_template_purchase_request_approve", 
                    raise_if_not_found=False
                )
                if template:
                    template.send_mail(
                        request.id, 
                        force_send=True, 
                        email_values={'email_to': request.assigned_to.email}
                    )
        return res
