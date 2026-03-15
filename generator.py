import os
import re

import qrcode
from PIL import Image, ImageDraw, ImageFont


def ensure_default_template(template_path):
    """Create a default certificate template if it doesn't exist."""
    if os.path.exists(template_path):
        return

    os.makedirs(os.path.dirname(template_path), exist_ok=True)
    # Create a professional-looking default certificate template
    image = Image.new("RGB", (1600, 1131), color=(250, 248, 245))
    draw = ImageDraw.Draw(image)

    # Border
    draw.rectangle((30, 30, 1570, 1101), outline=(100, 70, 40), width=5)
    inner_border = 50
    draw.rectangle((inner_border, inner_border, 1600-inner_border, 1131-inner_border), 
                   outline=(150, 100, 60), width=2)

    # Header text (this will be covered by our dynamic text)
    draw.text((200, 50), "ASCENDPITCH", fill=(40, 40, 40))
    draw.text((250, 100), "CERTIFICATE OF PARTICIPATION", fill=(80, 80, 80))
    draw.text((200, 180), "THIS CERTIFICATE IS PRESENTED TO", fill=(60, 60, 60))

    image.save(template_path)


def sanitize_name_for_file(name):
    safe = re.sub(r"\s+", "_", name.strip())
    safe = re.sub(r"[^A-Za-z0-9_]", "", safe)
    return safe or "Participant"


def load_font(font_path, size):
    """Load a font file or return default if not available."""
    if font_path and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size=size)
        except Exception:
            return ImageFont.load_default()
    return ImageFont.load_default()


def center_text(draw, text, font, canvas_width, y, fill=(20, 20, 20)):
    """Draw text centered horizontally at given y position."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = int((canvas_width - text_width) / 2)
    draw.text((x, y), text, font=font, fill=fill)
    return y + (bbox[3] - bbox[1]) + 10  # Return next y position


def wrap_text(text, max_width, font, draw):
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        text_line = " ".join(current_line)
        bbox = draw.textbbox((0, 0), text_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width > max_width:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return lines


def generate_certificate(
    template_path,
    output_path,
    participant_name,
    college_name,
    participant_photo_path,
    qr_data,
    font_path=None,
):
    """
    Generate certificate image using a fixed template and dynamic participant data.
    
    Template layout (3508x2480 A4 landscape):
    
    ASCENDPITCH
    CERTIFICATE OF PARTICIPATION
    THIS CERTIFICATE IS PRESENTED TO
    
    [Participant Name]       ← centered, large (72pt)
    [College Name]           ← centered, medium (48pt)
    
    [Achievement Paragraph]  ← centered, wrapped (36pt)
    
    [Signature] [Seal] [Signature]  ← bottom section from template
    [Photo 250x250] [QR 200x200]    ← right side
    """
    ensure_default_template(template_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    certificate = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(certificate)

    width, height = certificate.size
    
    # Responsive font sizing based on template actual size
    # For 3508x2480, scale fonts appropriately
    scale_factor = width / 3508.0  # Scale based on actual template width
    
    name_font = load_font(font_path, int(72 * scale_factor))           # Participant name
    college_font = load_font(font_path, int(48 * scale_factor))        # College name
    paragraph_font = load_font(font_path, int(36 * scale_factor))      # Achievement text
    label_font = load_font(font_path, int(28 * scale_factor))          # Labels

    # Color scheme
    name_color = (161, 118, 52)          # Gold/brown
    text_color = (40, 40, 40)            # Dark gray
    accent_color = (100, 50, 30)         # Darker brown

    # PARTICIPANT NAME - centered, positioned appropriately
    # Assuming header takes top ~400 pixels (ASCENDPITCH, CERTIFICATE OF..., THIS CERTIFICATE...)
    name_y = int(height * 0.25)  # ~25% down from top
    center_text(draw, participant_name, name_font, width, name_y, fill=name_color)

    # COLLEGE NAME - centered, below participant name
    college_y = name_y + int(120 * scale_factor)  # Space below name
    center_text(draw, college_name, college_font, width, college_y, fill=text_color)

    # ACHIEVEMENT PARAGRAPH - centered and wrapped
    paragraph_text = (
        "has successfully participated in the Ascend Pitch Certificate Program "
        "held at KGiSL Institute of Technology and demonstrated remarkable "
        "enthusiasm and commitment during the event held on March 28, 2026."
    )
    
    # Wrap paragraph to fit in certificate (accounting for space for photo/QR on right)
    max_paragraph_width = int(width * 0.55)  # Limit width to leave room for photo/QR
    paragraph_lines = wrap_text(paragraph_text, max_paragraph_width, paragraph_font, draw)
    
    # Draw paragraph lines centered
    paragraph_y = college_y + int(120 * scale_factor)  # Space below college name
    line_height = int(60 * scale_factor)  # Space between lines
    for line in paragraph_lines:
        center_text(draw, line, paragraph_font, width, paragraph_y, fill=text_color)
        paragraph_y += line_height

    # PARTICIPANT PHOTO - right side, properly sized (250x250)
    try:
        photo = Image.open(participant_photo_path).convert("RGB")
        photo_size = int(250 * scale_factor)  # Scale based on template size
        
        # Create a square by padding if necessary
        if photo.width != photo.height:
            # Make it square by adding padding
            size = max(photo.width, photo.height)
            new_photo = Image.new("RGB", (size, size), color=(255, 255, 255))
            offset = ((size - photo.width) // 2, (size - photo.height) // 2)
            new_photo.paste(photo, offset)
            photo = new_photo
        
        photo = photo.resize((photo_size, photo_size), Image.Resampling.LANCZOS)
        
        # Position on right side, middle height
        photo_x = width - photo_size - int(150 * scale_factor)  # 150px from right edge
        photo_y = int(height * 0.35)  # Middle height
        certificate.paste(photo, (photo_x, photo_y))
    except Exception as e:
        print(f"[WARNING] Could not load participant photo: {e}")

    # QR CODE - bottom-right corner (200x200)
    try:
        qr = qrcode.make(qr_data).convert("RGB")
        qr_size = int(200 * scale_factor)  # Scale based on template size
        qr = qr.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        # Position bottom-right corner
        qr_x = width - qr_size - int(150 * scale_factor)  # 150px from right edge
        qr_y = height - qr_size - int(200 * scale_factor)  # 200px from bottom
        certificate.paste(qr, (qr_x, qr_y))
        
        # QR label
        draw.text((qr_x - int(100 * scale_factor), qr_y - int(70 * scale_factor)), 
                  "Scan to verify", font=label_font, fill=accent_color)
    except Exception as e:
        print(f"[WARNING] Could not generate QR code: {e}")

    certificate.save(output_path, format="PNG")
    return output_path
