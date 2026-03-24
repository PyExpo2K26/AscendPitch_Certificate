from PIL import Image, ImageDraw, ImageFont, ImageOps
import qrcode
import os
import re


def sanitize_name_for_file(name):
    """Convert participant name into a safe filename.
    
    Examples:
        "Boomathi P" → "boomathi_p"
        "Boomathi @ KGiSL" → "boomathi_kgisl"
    """
    name = name.strip().lower()
    # Keep only lowercase letters, numbers, spaces, and underscores.
    name = re.sub(r'[^a-z0-9_\s]', '', name)
    # Normalize whitespace and repeated underscores into single underscores.
    name = re.sub(r'[\s_]+', '_', name)
    # Remove leading/trailing underscores.
    name = name.strip('_')
    return name or "participant"


def generate_certificate(
    template_path,
    output_path,
    participant_name,
    college_name,
    participant_photo_path,
    qr_data,
    font_path,
):

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
    
    # Start with balanced font sizes and auto-fit where needed.
    name_font_size = max(52, int(img_height * 0.030))
    desc_font_size = max(20, int(img_height * 0.010))
    name_font = ImageFont.truetype(name_font_path, name_font_size)
    desc_font = ImageFont.truetype(desc_font_path, desc_font_size)

    # Relative anchors keep placement stable if template dimensions change.
    line_y = int(img_height * 0.49)

    photo_size = max(220, int(img_height * 0.167))
    photo_card_padding = 12
    photo_card_size = photo_size + (photo_card_padding * 2)
    photo_margin_right = int(img_width * 0.120)
    photo_margin_top = int(img_height * 0.318)
    photo_x = img_width - photo_card_size - photo_margin_right
    photo_y = photo_margin_top

    qr_size = max(190, int(img_height * 0.150))
    qr_card_padding = 12
    qr_card_size = qr_size + (qr_card_padding * 2)
    qr_margin_right = int(img_width * 0.080)
    qr_margin_bottom = int(img_height * 0.188)
    qr_x = img_width - qr_card_size - qr_margin_right
    qr_y = img_height - qr_card_size - qr_margin_bottom

    if participant_photo_path:
        photo = Image.open(participant_photo_path).convert("RGB")
        photo = ImageOps.fit(photo, (photo_size, photo_size), method=Image.Resampling.LANCZOS)

        # Keep photo inside border on a white card.
        framed_photo = Image.new("RGB", (photo_card_size, photo_card_size), "white")
        frame_draw = ImageDraw.Draw(framed_photo)
        frame_draw.rectangle(
            [0, 0, photo_card_size - 1, photo_card_size - 1],
            outline="#d1d5db",
            width=1,
        )
        framed_photo.paste(photo, (photo_card_padding, photo_card_padding))
        img.paste(framed_photo, (photo_x, photo_y))

    # =============================
    # ANCHOR: HORIZONTAL LINE
    # =============================
    
    # =============================
    # NAME
    # =============================
    
    # Auto-shrink long names so they remain centered in the available middle area.
    max_name_width = int(img_width * 0.58)
    while True:
        bbox = draw.textbbox((0, 0), participant_name, font=name_font)
        text_width = bbox[2] - bbox[0]
        if text_width <= max_name_width or name_font_size <= 34:
            break
        name_font_size -= 2
        name_font = ImageFont.truetype(name_font_path, name_font_size)

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    name_x = (img_width - text_width) // 2
    name_y = line_y - text_height - 14
    draw.text((name_x, name_y), participant_name, fill="#0b2a44", font=name_font)

    # =============================
    # DESCRIPTION
    # =============================
    
    # Keep body text minimal to avoid overlapping the printed template wording.
    if college_name:
        college_line = f"{college_name}"
        bbox = draw.textbbox((0, 0), college_line, font=desc_font)
        text_width = bbox[2] - bbox[0]
        desc_x = (img_width - text_width) // 2
        desc_y = line_y + 56
        draw.text((desc_x, desc_y), college_line, fill="#0b2a44", font=desc_font)

    # =============================
    # QR
    # =============================
    
    qr = qrcode.make(qr_data).convert("RGB")
    qr = qr.resize((qr_size, qr_size), Image.Resampling.NEAREST)

    # Keep QR inside border on a white card.
    framed_qr = Image.new("RGB", (qr_card_size, qr_card_size), "white")
    qr_draw = ImageDraw.Draw(framed_qr)
    qr_draw.rectangle([0, 0, qr_card_size - 1, qr_card_size - 1], outline="#d1d5db", width=1)
    framed_qr.paste(qr, (qr_card_padding, qr_card_padding))
    img.paste(framed_qr, (qr_x, qr_y))

    # =============================
    # VERIFY TEMPLATE SIZE
    # =============================
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img = img.convert("RGB")
    img.save(output_path, "PDF")