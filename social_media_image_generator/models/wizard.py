import base64
import io
import logging

from odoo import api, fields, models, _

from .image_generator import ImageGenerator

_logger = logging.getLogger(__name__)


class SocialMediaImageWizard(models.TransientModel):
    _name = 'socmed.image.wizard'
    _description = 'Social Media Image Generator Wizard'

    # ── Template selection ───────────────────────────────────────
    template = fields.Selection([
        ('announcement', '📢 Announcement / Info'),
        ('tips',         '💡 Tips / List'),
        ('quote',        '⭐ Quote / Testimonial'),
        ('event',        '📅 Event'),
        ('custom',       '✏️ Custom Text'),
    ], default='announcement', required=True)

    platform = fields.Selection([
        ('instagram_square', 'Instagram Post — 1:1 (1080×1080)'),
        ('instagram_story',  'Instagram Story — 9:16 (1080×1920)'),
        ('facebook',         'Facebook / LinkedIn — 1.91:1 (1200×628)'),
    ], default='instagram_square', required=True)

    # ── Common fields ────────────────────────────────────────────
    main_text = fields.Char(
        'Judul Utama',
        help='Nama produk, judul promo, dll')
    subtitle = fields.Char(
        'Subtitle',
        help='Harga, tagline, detail singkat')
    description = fields.Text(
        'Deskripsi',
        help='Detail / bullet list (pisahkan dengan Enter)')

    # ── Promo fields ────────────────────────────────────────────
    badge_text = fields.Char(
        'Badge / Stiker',
        help='Contoh: DISKON 20%, NEW, HOT, LIMITED')
    promo_code = fields.Char(
        'Kode Promo / Voucher',
        help='Tampilkan kode yang bisa dipakai customer')
    valid_until = fields.Date(
        'Berlaku Sampai')

    # ── Testimonial fields ──────────────────────────────────────
    customer_name = fields.Char(
        'Nama Pelanggan')
    customer_title = fields.Char(
        'Jabatan / Asal / Negara Tujuan',
        help='Contoh: Direktur PT ABC, atau Australia')
    quote = fields.Text(
        'Testimonial / Review')

    # ── Event fields ────────────────────────────────────────────
    event_date = fields.Datetime(
        'Tanggal Event')
    event_location = fields.Char(
        'Lokasi',
        help='Contoh: Online / Zoom / Gedung X')
    cta_text = fields.Char(
        'Tombol CTA',
        help='Contoh: Daftar Sekarang, Hubungi Kami',
        default='Daftar Sekarang')

    # ── Output ──────────────────────────────────────────────────
    image_preview = fields.Binary(
        'Preview Gambar', readonly=True,
        attachment=False)
    image_filename = fields.Char(
        'Filename', readonly=True)

    # ── Actions ─────────────────────────────────────────────────

    @api.onchange('template')
    def _onchange_template(self):
        """Reset fields that don't apply to the selected template."""
        for rec in self:
            if rec.template in ('quote',):
                rec.main_text = ''
                rec.subtitle = ''
                rec.badge_text = ''
                rec.promo_code = ''
                rec.valid_until = False
                rec.event_date = False
                rec.event_location = ''
                rec.cta_text = ''
                rec.image_preview = False
            elif rec.template in ('event',):
                rec.badge_text = ''
                rec.promo_code = ''
                rec.valid_until = False
                rec.customer_name = ''
                rec.customer_title = ''
                rec.quote = ''
                rec.image_preview = False
            elif rec.template in ('tips',):
                rec.badge_text = ''
                rec.promo_code = ''
                rec.valid_until = False
                rec.customer_name = ''
                rec.customer_title = ''
                rec.quote = ''
                rec.event_date = False
                rec.event_location = ''
                rec.image_preview = False
            elif rec.template in ('announcement',):
                rec.customer_name = ''
                rec.customer_title = ''
                rec.quote = ''
                rec.event_date = False
                rec.event_location = ''
                rec.image_preview = False
            elif rec.template in ('custom',):
                rec.badge_text = ''
                rec.promo_code = ''
                rec.valid_until = False
                rec.customer_name = ''
                rec.customer_title = ''
                rec.quote = ''
                rec.event_date = False
                rec.event_location = ''
                rec.cta_text = ''
                rec.image_preview = False

    def action_generate(self):
        """Generate the image and show preview."""
        self.ensure_one()

        try:
            png_data = ImageGenerator.generate(self)
            b64_data = base64.b64encode(png_data)

            # Build filename
            safe_name = (self.main_text or 'socmed').replace(' ', '_')[:30]
            ext = '.png'
            filename = f'{safe_name}_{self.template}_{self.platform}{ext}'

            self.write({
                'image_preview': b64_data,
                'image_filename': filename,
            })
        except Exception as e:
            _logger.exception('Image generation failed')
            raise models.UserError(
                _('Gagal generate gambar: %s') % str(e)
            )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'socmed.image.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_download(self):
        """Download the generated image."""
        self.ensure_one()
        if not self.image_preview:
            raise models.UserError(_('Generate dulu gambarnya, Bos!'))

        return {
            'type': 'ir.actions.act_url',
            'url': f'/socmed_image/download/{self.id}',
            'target': 'self',
        }

    # ── Controller helper ───────────────────────────────────────
    def get_image_data(self):
        """Return (bytes, filename) for HTTP download."""
        self.ensure_one()
        return (
            base64.b64decode(self.image_preview),
            self.image_filename or 'socmed_image.png',
        )

    def name_get(self):
        return [(rec.id, f'Generate Image — {rec.template}') for rec in self]

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Override to show dynamic fields based on template."""
        return super().fields_get(allfields, attributes)