from PIL import Image, ImageDraw, ImageFont, ImageOps
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
    desc_font_path = os.path.join(fonts_dir, "PlayfairDisplay-Regular.ttf")
    
    # Check if font files exist
    for font_file in [name_font_path, desc_font_path]:
        if not os.path.exists(font_file):
            raise FileNotFoundError(f"Font file not found: {font_file}")
    
    # Load Fonts
    name_font = ImageFont.truetype(name_font_path, 110)
    desc_font = ImageFont.truetype(desc_font_path, 42)

    # =============================
    # PHOTO
    # =============================
    
    photo = Image.open(participant_photo_path).convert("RGB")
    # Use a fixed square crop so portrait photos don't look tiny after thumbnail scaling.
    photo = ImageOps.fit(photo, (290, 290), method=Image.Resampling.LANCZOS)

    photo_x = 1580
    photo_y = 390

    img.paste(photo,(photo_x,photo_y))

    # =============================
    # ANCHOR: HORIZONTAL LINE
    # =============================
    
    line_y = 640

    # =============================
    # NAME
    # =============================
    
    bbox = draw.textbbox((0, 0), participant_name, font=name_font)
    text_width = bbox[2] - bbox[0]
    name_x = (img_width - text_width) // 2
    name_y = line_y - 85
    draw.text((name_x, name_y), participant_name, fill="#0b2a44", font=name_font)

    # =============================
    # DESCRIPTION
    # =============================
    
    description = (
        f'from {college_name} has successfully participated in the Ascend Pitch '
        'held at KGiSL Institute of Technology and demonstrated remarkable enthusiasm '
        'and commitment during the event held on March 28, 2026.'
    )

    wrapped = textwrap.fill(description, 65)
    desc_y = line_y + 60
    line_spacing = 48

    for line in wrapped.split("\n"):
        bbox = draw.textbbox((0, 0), line, font=desc_font)
        text_width = bbox[2] - bbox[0]
        desc_x = (img_width - text_width) // 2
        draw.text((desc_x, desc_y), line, fill="#0b2a44", font=desc_font)
        desc_y += line_spacing

    # =============================
    # QR
    # =============================
    
    qr = qrcode.make(qr_data)
    qr = qr.resize((240, 240))
    qr_x = img_width - 400
    qr_y = img_height - 450
    img.paste(qr, (qr_x, qr_y))

    # =============================
    # VERIFY TEMPLATE SIZE
    # =============================
    
    print(img.size)

    # =============================
    # SAVE CERTIFICATE AS PDF
    # =============================
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img = img.convert("RGB")
    img.save(output_path, "PDF")