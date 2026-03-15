import os
import re

import qrcode
from PIL import Image, ImageDraw, ImageFont


def ensure_default_template(template_path):
    if os.path.exists(template_path):
        return

    os.makedirs(os.path.dirname(template_path), exist_ok=True)
    image = Image.new("RGB", (1600, 1131), color=(247, 244, 235))
    draw = ImageDraw.Draw(image)

    draw.rectangle((50, 50, 1550, 1081), outline=(40, 40, 40), width=8)
    draw.text((650, 120), "CERTIFICATE", fill=(20, 20, 20))
    draw.text((560, 200), "OF PARTICIPATION", fill=(90, 90, 90))

    image.save(template_path)


def sanitize_name_for_file(name):
    safe = re.sub(r"\s+", "_", name.strip())
    safe = re.sub(r"[^A-Za-z0-9_]", "", safe)
    return safe or "Participant"


def load_font(font_path, size):
    if font_path and os.path.exists(font_path):
        return ImageFont.truetype(font_path, size=size)
    return ImageFont.load_default()


def center_text(draw, text, font, canvas_width, y, fill=(20, 20, 20)):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = int((canvas_width - text_width) / 2)
    draw.text((x, y), text, font=font, fill=fill)


def generate_certificate(
    template_path,
    output_path,
    participant_name,
    college_name,
    participant_photo_path,
    qr_data,
    font_path=None,
):
    """Generate certificate image using a fixed template and dynamic participant data."""
    ensure_default_template(template_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    certificate = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(certificate)

    width, height = certificate.size

    # Keep placement values centralized so alignment is easy to adjust.
    title_font = load_font(font_path, 68)
    name_font = load_font(font_path, 76)
    detail_font = load_font(font_path, 38)
    small_font = load_font(font_path, 26)

    center_text(draw, participant_name, name_font, width, 490, fill=(161, 118, 52))
    center_text(
        draw,
        f"College: {college_name}",
        detail_font,
        width,
        740,
        fill=(50, 50, 50),
    )

    # Participant photo appears near the lower-left area.
    photo = Image.open(participant_photo_path).convert("RGB")
    photo = photo.resize((190, 220))
    certificate.paste(photo, (120, height - 300))

    # QR is always placed in the bottom-right corner for verification scanning.
    qr = qrcode.make(qr_data).convert("RGB")
    qr_size = 170
    qr = qr.resize((qr_size, qr_size))
    qr_x = width - qr_size - 80
    qr_y = height - qr_size - 80
    certificate.paste(qr, (qr_x, qr_y))

    draw.text((120, height - 70), "Participant Photo", font=small_font, fill=(60, 60, 60))
    draw.text((qr_x - 35, qr_y - 35), "Scan to verify", font=small_font, fill=(60, 60, 60))

    certificate.save(output_path, format="PNG")
    return output_path
