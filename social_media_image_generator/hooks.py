"""Post-init script: generate template backgrounds so the module works OOTB."""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

TEMPLATE_COLORS = {
    'announcement': (52, 152, 219, 41, 128, 185, 255, 215, 0),
    'tips':         (46, 204, 113, 39, 174, 96, 255, 255, 255),
    'quote':        (155, 89, 182, 142, 68, 173, 255, 215, 0),
    'event':        (231, 76, 60, 192, 57, 43, 255, 255, 255),
    'custom':       (52, 73, 94, 44, 62, 80, 230, 126, 34),
}


def _generate_backgrounds(env):
    """Generate simple gradient PNGs for each template."""
    try:
        from PIL import Image
    except ImportError:
        _logger.warning('Pillow not available — skipping template generation')
        return

    import os
    module_path = env['ir.module.module'].sudo().search([
        ('name', '=', 'social_media_image_generator')
    ], limit=1)
    if not module_path:
        return

    module_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    templates_dir = os.path.join(module_dir, 'static', 'src', 'img', 'templates')
    os.makedirs(templates_dir, exist_ok=True)

    for name, (pr, pg, pb, sr, sg, sb, ar, ag, ab) in TEMPLATE_COLORS.items():
        img = Image.new('RGBA', (200, 200))
        w, h = img.size
        for y in range(h):
            ratio = y / h
            r = int(pr * (1 - ratio) + sr * ratio)
            g = int(pg * (1 - ratio) + sg * ratio)
            b = int(pb * (1 - ratio) + sb * ratio)
            for x in range(w):
                img.putpixel((x, y), (r, g, b, 255))

        path = os.path.join(templates_dir, f'{name}.png')
        img.save(path)
        _logger.info('Generated template background: %s', path)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _generate_backgrounds(env)