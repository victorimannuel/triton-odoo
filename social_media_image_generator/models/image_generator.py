import base64
import io
import logging
import os
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageFilter

_logger = logging.getLogger(__name__)

# ── Platform dimensions ──────────────────────────────────────────
SIZE_PRESETS = {
    'instagram_square': (1080, 1080),
    'instagram_story':  (1080, 1920),
    'facebook':         (1200, 628),
}

# ── Template colours ─────────────────────────────────────────────
TEMPLATE_COLORS = {
    'announcement': {'primary': (52, 152, 219),  'secondary': (41, 128, 185),  'accent': (255, 215, 0)},
    'tips':         {'primary': (46, 204, 113),  'secondary': (39, 174, 96),   'accent': (255, 255, 255)},
    'quote':        {'primary': (155, 89, 182),  'secondary': (142, 68, 173),  'accent': (255, 215, 0)},
    'event':        {'primary': (231, 76, 60),   'secondary': (192, 57, 43),   'accent': (255, 255, 255)},
    'custom':       {'primary': (52, 73, 94),    'secondary': (44, 62, 80),    'accent': (230, 126, 34)},
}

# ── Background template paths (generated on install) ─────────────
MODULE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
TEMPLATES_DIR = os.path.join(MODULE_DIR, 'static', 'src', 'img', 'templates')

FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


class ImageGenerator:
    """Core image generation logic using Pillow."""

    @classmethod
    def generate(cls, wizard):
        """Main entry — returns PNG bytes."""
        size = SIZE_PRESETS.get(wizard.platform, (1080, 1080))
        template = wizard.template
        colors = TEMPLATE_COLORS.get(template, TEMPLATE_COLORS['custom'])

        # 1. Background
        bg = cls._create_background(size, template, colors)

        # 2. Overlay gradient strip
        bg = cls._add_overlay_gradient(bg, colors)

        # 3. Logo / branding bar at top
        bg = cls._add_brand_bar(bg)

        # 4. Template-specific content
        if template == 'announcement':
            bg = cls._render_announcement(bg, wizard, colors)
        elif template == 'tips':
            bg = cls._render_tips(bg, wizard, colors)
        elif template == 'quote':
            bg = cls._render_quote(bg, wizard, colors)
        elif template == 'event':
            bg = cls._render_event(bg, wizard, colors)
        else:
            bg = cls._render_custom(bg, wizard, colors)

        # 5. Save to PNG bytes
        buf = io.BytesIO()
        bg.save(buf, format='PNG')
        return buf.getvalue()

    # ── Low-level helpers ────────────────────────────────────────

    @classmethod
    def _create_background(cls, size, template, colors):
        """Create gradient background."""
        w, h = size
        img = Image.new('RGBA', size, colors['primary'])

        # Gradient overlay (top → bottom)
        for y in range(h):
            ratio = y / h
            r = int(colors['primary'][0] * (1 - ratio) + colors['secondary'][0] * ratio)
            g = int(colors['primary'][1] * (1 - ratio) + colors['secondary'][1] * ratio)
            b = int(colors['primary'][2] * (1 - ratio) + colors['secondary'][2] * ratio)
            for x in range(w):
                img.putpixel((x, y), (r, g, b, 255))

        return img

    @classmethod
    def _add_overlay_gradient(cls, img, colors):
        """Semi-transparent black overlay for text readability."""
        w, h = img.size
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for y in range(h):
            ratio = y / h
            alpha = int(180 * ratio)  # fade in toward bottom
            if alpha > 0:
                draw.line([(0, y), (w, y)], fill=(0, 0, 0, min(alpha, 100)))
        return Image.alpha_composite(img, overlay)

    @classmethod
    def _add_brand_bar(cls, img):
        """Add a thin accent bar at the top."""
        draw = ImageDraw.Draw(img)
        w, _ = img.size
        bar_h = max(8, w // 90)
        # Gold accent bar
        for y in range(bar_h):
            draw.line([(0, y), (w, y)], fill=(255, 215, 0, 220))
        return img

    @classmethod
    def _load_font(cls, size, bold=False):
        try:
            path = FONT_BOLD if bold else FONT_REGULAR
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()

    @classmethod
    def _draw_centered_text(cls, draw, text, y, font, color, max_width):
        """Draw text centered, auto-wrap if too wide."""
        words = text.split()
        lines = []
        current = ''
        for word in words:
            test = (current + ' ' + word).strip()
            bb = draw.textbbox((0, 0), test, font=font)
            if bb[2] - bb[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        x_center = max_width // 2 + 50  # 50px left margin offset
        for line in lines:
            bb = draw.textbbox((0, 0), line, font=font)
            tw = bb[2] - bb[0]
            x = (max_width - tw) // 2 + 50
            draw.text((x, y), line, fill=color, font=font)
            y += bb[3] - bb[1] + 10

        return y

    @classmethod
    def _draw_multiline(cls, draw, text, x, y, font, color, max_width, line_spacing=10):
        """Draw multiline text, wrapping as needed."""
        words = text.split()
        lines = []
        current = ''
        for word in words:
            test = (current + ' ' + word).strip()
            bb = draw.textbbox((0, 0), test, font=font)
            if bb[2] - bb[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        for line in lines:
            draw.text((x, y), line, fill=color, font=font)
            bb = draw.textbbox((0, 0), line, font=font)
            y += bb[3] - bb[1] + line_spacing

        return y

    # ── Template renderers ───────────────────────────────────────

    @classmethod
    def _render_announcement(cls, img, wizard, colors):
        draw = ImageDraw.Draw(img)
        w, h = img.size
        margin = int(w * 0.08)
        usable = w - 2 * margin

        # Badge (top right)
        if wizard.badge_text:
            badge_text = wizard.badge_text.upper()
            badge_font = cls._load_font(int(w * 0.06), bold=True)
            bb = draw.textbbox((0, 0), badge_text, font=badge_font)
            bw = bb[2] - bb[0] + 40
            bh = bb[3] - bb[1] + 20
            bx = w - margin - bw
            by = int(h * 0.08)
            draw.rounded_rectangle(
                [bx, by, bx + bw, by + bh],
                radius=12, fill=colors['accent']
            )
            draw.text(
                (bx + 20, by + 10), badge_text,
                fill=(0, 0, 0, 255), font=badge_font
            )

        # Main title
        if wizard.main_text:
            title_font = cls._load_font(int(w * 0.09), bold=True)
            cls._draw_centered_text(
                draw, wizard.main_text.upper(),
                int(h * 0.30), title_font, (255, 255, 255, 255), usable
            )

        # Subtitle / price
        if wizard.subtitle:
            sub_font = cls._load_font(int(w * 0.06), bold=True)
            cls._draw_centered_text(
                draw, wizard.subtitle,
                int(h * 0.50), sub_font, colors['accent'], usable
            )

        # Description
        if wizard.description:
            desc_font = cls._load_font(int(w * 0.035))
            cls._draw_centered_text(
                draw, wizard.description,
                int(h * 0.62), desc_font, (220, 220, 220, 255), usable
            )

        # Promo code (bottom)
        if wizard.promo_code:
            code_font = cls._load_font(int(w * 0.045), bold=True)
            code_text = f'Kode: {wizard.promo_code}'
            cls._draw_centered_text(
                draw, code_text,
                int(h * 0.82), code_font, colors['accent'], usable
            )

        # Valid until
        if wizard.valid_until:
            date_font = cls._load_font(int(w * 0.03))
            date_text = f'Berlaku sampai: {wizard.valid_until}'
            cls._draw_centered_text(
                draw, date_text,
                int(h * 0.90), date_font, (180, 180, 180, 255), usable
            )

        return img

    @classmethod
    def _render_tips(cls, img, wizard, colors):
        draw = ImageDraw.Draw(img)
        w, h = img.size
        margin = int(w * 0.08)
        usable = w - 2 * margin

        # Title
        if wizard.main_text:
            title_font = cls._load_font(int(w * 0.07), bold=True)
            cls._draw_centered_text(
                draw, wizard.main_text.upper(),
                int(h * 0.15), title_font, (255, 255, 255, 255), usable
            )

        # Subtitle
        if wizard.subtitle:
            sub_font = cls._load_font(int(w * 0.045))
            cls._draw_centered_text(
                draw, wizard.subtitle,
                int(h * 0.28), sub_font, colors['accent'], usable
            )

        # Description as bullet points
        if wizard.description:
            desc_font = cls._load_font(int(w * 0.035))
            y_pos = int(h * 0.40)
            lines = wizard.description.split('\n')
            for line in lines:
                if line.strip():
                    bullet = f'• {line.strip()}'
                    bb = draw.textbbox((0, 0), bullet, font=desc_font)
                    # Clip to usable width
                    while bb[2] - bb[0] > usable and len(bullet) > 10:
                        bullet = bullet[:-5] + '...'
                        bb = draw.textbbox((0, 0), bullet, font=desc_font)
                    draw.text((margin, y_pos), bullet, fill=(255, 255, 255, 240), font=desc_font)
                    y_pos += bb[3] - bb[1] + 15

        # CTA at bottom
        if wizard.cta_text or wizard.badge_text:
            cta = (wizard.cta_text or wizard.badge_text or 'Hubungi Kami').upper()
            cta_font = cls._load_font(int(w * 0.04), bold=True)
            cls._draw_centered_text(
                draw, cta,
                int(h * 0.85), cta_font, colors['accent'], usable
            )

        return img

    @classmethod
    def _render_quote(cls, img, wizard, colors):
        draw = ImageDraw.Draw(img)
        w, h = img.size
        margin = int(w * 0.10)
        usable = w - 2 * margin

        # Quote mark (large)
        quote_font = cls._load_font(int(w * 0.18), bold=True)
        draw.text((margin, int(h * 0.10)), '"', fill=colors['accent'], font=quote_font)

        # Quote text
        if wizard.quote:
            quote_font = cls._load_font(int(w * 0.045))
            cls._draw_multiline(
                draw, wizard.quote,
                margin, int(h * 0.25), quote_font,
                (255, 255, 255, 250), usable
            )

        # Customer name
        if wizard.customer_name:
            name_font = cls._load_font(int(w * 0.05), bold=True)
            cls._draw_centered_text(
                draw, f'— {wizard.customer_name}',
                int(h * 0.70), name_font, (255, 255, 255, 255), usable
            )

        # Customer title
        if wizard.customer_title:
            title_font = cls._load_font(int(w * 0.03))
            cls._draw_centered_text(
                draw, wizard.customer_title,
                int(h * 0.78), title_font, (200, 200, 200, 255), usable
            )

        return img

    @classmethod
    def _render_event(cls, img, wizard, colors):
        draw = ImageDraw.Draw(img)
        w, h = img.size
        margin = int(w * 0.08)
        usable = w - 2 * margin

        # Date (big)
        if wizard.event_date:
            date_str = wizard.event_date.strftime('%d %B %Y') if hasattr(wizard.event_date, 'strftime') else str(wizard.event_date)
            date_font = cls._load_font(int(w * 0.045), bold=True)
            cls._draw_centered_text(
                draw, date_str,
                int(h * 0.15), date_font, colors['accent'], usable
            )

        # Main title
        if wizard.main_text:
            title_font = cls._load_font(int(w * 0.07), bold=True)
            cls._draw_centered_text(
                draw, wizard.main_text.upper(),
                int(h * 0.28), title_font, (255, 255, 255, 255), usable
            )

        # Location
        if wizard.event_location:
            loc_font = cls._load_font(int(w * 0.035))
            loc_text = f'📍 {wizard.event_location}'
            cls._draw_centered_text(
                draw, loc_text,
                int(h * 0.45), loc_font, (220, 220, 220, 255), usable
            )

        # Description
        if wizard.description:
            desc_font = cls._load_font(int(w * 0.035))
            cls._draw_multiline(
                draw, wizard.description,
                margin, int(h * 0.55), desc_font,
                (200, 200, 200, 255), usable
            )

        # CTA button
        if wizard.cta_text:
            cta = wizard.cta_text.upper()
            cta_font = cls._load_font(int(w * 0.04), bold=True)
            bb = draw.textbbox((0, 0), cta, font=cta_font)
            bw = bb[2] - bb[0] + 60
            bh = bb[3] - bb[1] + 30
            cx = (w - bw) // 2
            cy = int(h * 0.80)
            draw.rounded_rectangle(
                [cx, cy, cx + bw, cy + bh],
                radius=20, fill=colors['accent']
            )
            draw.text(
                (cx + 30, cy + 15), cta,
                fill=(0, 0, 0, 255), font=cta_font
            )

        return img

    @classmethod
    def _render_custom(cls, img, wizard, colors):
        draw = ImageDraw.Draw(img)
        w, h = img.size
        margin = int(w * 0.08)
        usable = w - 2 * margin

        # Main text (big, centered)
        if wizard.main_text:
            title_font = cls._load_font(int(w * 0.08), bold=True)
            cls._draw_centered_text(
                draw, wizard.main_text.upper(),
                int(h * 0.20), title_font, (255, 255, 255, 255), usable
            )

        # Subtitle
        if wizard.subtitle:
            sub_font = cls._load_font(int(w * 0.05))
            cls._draw_centered_text(
                draw, wizard.subtitle,
                int(h * 0.40), sub_font, colors['accent'], usable
            )

        # Description
        if wizard.description:
            desc_font = cls._load_font(int(w * 0.035))
            cls._draw_multiline(
                draw, wizard.description,
                margin, int(h * 0.55), desc_font,
                (220, 220, 220, 255), usable
            )

        return img


def generate_background_templates():
    """Generate template backgrounds so module works out of the box."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    for name, colors in TEMPLATE_COLORS.items():
        img = ImageGenerator._create_background((200, 200), name, colors)
        path = os.path.join(TEMPLATES_DIR, f'{name}.png')
        img.save(path)
        _logger.info(f'Generated template: {path}')
    _logger.info('All template backgrounds generated.')