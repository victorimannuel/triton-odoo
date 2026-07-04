from odoo import http
from odoo.http import request


class SocmedImageController(http.Controller):

    @http.route(
        '/socmed_image/download/<int:wizard_id>',
        type='http', auth='user', methods=['GET']
    )
    def download_image(self, wizard_id):
        """Serve generated image as file download."""
        wizard = request.env['socmed.image.wizard'].browse(wizard_id)
        if not wizard.exists():
            return request.not_found()

        data, filename = wizard.get_image_data()
        headers = [
            ('Content-Type', 'image/png'),
            ('Content-Disposition', f'attachment; filename="{filename}"'),
            ('Content-Length', str(len(data))),
        ]
        return request.make_response(data, headers=headers)