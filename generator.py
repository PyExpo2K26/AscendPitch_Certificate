from PIL import Image, ImageDraw, ImageFont
import qrcode
import textwrap
import os
import re
import logging


def sanitize_name_for_file(name):
    """Convert participant name into a safe filename.
    
    Examples:
        "Boomathi P" → "boomathi_p"
        "Boomathi @ KGiSL" → "boomathi_kgisl"
    """
    name = name.strip().lower()
    # Remove special characters first
    name = re.sub(r'[^a-z0-9\s]', '', name)
    # Replace spaces with underscores
    name = re.sub(r'\s+', '_', name)
    # Remove any trailing underscores
    name = name.strip('_')
    return name or "participant"


def generate_certificate(template_path, output_path, participant_name, college_name, participant_photo_path, qr_data, font_path):

    # Validate template exists
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Certificate template not found: {template_path}")
    
    img = Image.open(template_path)

    draw = ImageDraw.Draw(img)

    img_width, img_height = img.size

    # Construct font paths from the template directory
    static_dir = os.path.dirname(template_path)
    fonts_dir = os.path.join(static_dir, "fonts")
    
    # Check if fonts directory exists
    if not os.path.exists(fonts_dir):
        raise FileNotFoundError(f"Fonts directory not found: {fonts_dir}")
    
    # Define font paths
    name_font_path = os.path.join(fonts_dir, "PlayfairDisplay-Bold.ttf")
    college_font_path = os.path.join(fonts_dir, "PlayfairDisplay-Regular.ttf")
    desc_font_path = os.path.join(fonts_dir, "PlayfairDisplay-Regular.ttf")
    
    # Check if font files exist
    for font_file in [name_font_path, college_font_path, desc_font_path]:
        if not os.path.exists(font_file):
            raise FileNotFoundError(f"Font file not found: {font_file}")
    
    # Load Fonts
    name_font = ImageFont.truetype(name_font_path, 130)
    college_font = ImageFont.truetype(college_font_path, 50)
    desc_font = ImageFont.truetype(desc_font_path, 48)

    # =============================
    # PHOTO
    # =============================
    
    photo = Image.open(participant_photo_path)
    photo.thumbnail((260, 260))
    photo_x = img_width - 520
    photo_y = 480
    img.paste(photo, (photo_x, photo_y))

    # =============================
    # NAME
    # =============================
    
    bbox = draw.textbbox((0, 0), participant_name, font=name_font)
    text_width = bbox[2] - bbox[0]
    name_x = (img_width - text_width) // 2
    name_y = 720
    draw.text((name_x, name_y), participant_name, fill="#0b2a44", font=name_font)

    # =============================
    # DESCRIPTION (no separate college name)
    # =============================
    
    description = (
        f"{college_name} has successfully participated in the Ascend Pitch Certificate "
        "Program held at KGiSL Institute of Technology and demonstrated remarkable "
        "enthusiasm and commitment during the event held on March 28, 2026."
    )

    wrapped = textwrap.fill(description, 60)
    desc_y = 850

    for line in wrapped.split("\n"):
        bbox = draw.textbbox((0, 0), line, font=desc_font)
        text_width = bbox[2] - bbox[0]
        desc_x = (img_width - text_width) // 2
        draw.text((desc_x, desc_y), line, fill="#0b2a44", font=desc_font)
        desc_y += 50

    # =============================
    # QR
    # =============================
    
    logger_debug = logging.getLogger(__name__)
    logger_debug.info(f"Template size: {img.size}")
    
    qr = qrcode.make(qr_data)
    qr = qr.resize((200, 200))
    qr_x = img_width - 420
    qr_y = img_height - 320
    img.paste(qr, (qr_x, qr_y))

    # =============================
    # SAVE CERTIFICATE AS PDF
    # =============================
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img = img.convert("RGB")
    img.save(output_path, "PDF")