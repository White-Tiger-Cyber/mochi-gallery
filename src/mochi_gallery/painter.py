import os
import random
import glob
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def get_font_paths():
    # Look in the local directory first (development mode)
    local_fonts = os.path.join(os.getcwd(), "assets", "fonts")
    if os.path.exists(local_fonts):
        return glob.glob(os.path.join(local_fonts, "*.ttf"))
    return []

def get_font_by_vibe(vibe: str, size: int):
    font_files = get_font_paths()
    selected_font = None
    if font_files:
        for f in font_files:
            if vibe in f.lower():
                selected_font = f
                break
        if not selected_font: selected_font = random.choice(font_files)

    try:
        if selected_font: return ImageFont.truetype(selected_font, size)
        else: return ImageFont.truetype("DejaVuSerif.ttf", size)
    except: return ImageFont.load_default()

def hex_to_rgb(hex_color: str):
    return tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

def get_luminance(rgb_tuple):
    """Calculates relative luminance to decide if color is dark or light."""
    r, g, b = rgb_tuple
    return (0.299 * r + 0.587 * g + 0.114 * b)

def draw_text_with_glow(base_img, x, y, text, font, text_color, glow_color, glow_strength):
    """
    Draws text with:
    1. A wide soft glow (atmosphere)
    2. A tight shadow (definition)
    3. A 1px hard stroke (readability guarantee)
    """

    # 1. Wide Ambient Glow (Softens the background area)
    # Increased strength from 0.5 to 0.7 for busy backgrounds
    wide_glow = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw_wide = ImageDraw.Draw(wide_glow)
    for ox in range(-2, 3):
        for oy in range(-2, 3):
            draw_wide.text((x+ox, y+oy), text, font=font, fill=glow_color + (int(glow_strength * 0.7),))
    wide_glow = wide_glow.filter(ImageFilter.GaussianBlur(radius=8))

    # 2. Tight Definition Shadow
    tight_glow = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw_tight = ImageDraw.Draw(tight_glow)
    for ox in [-1, 1]:
        for oy in [-1, 1]:
            draw_tight.text((x+ox, y+oy), text, font=font, fill=glow_color + (glow_strength,))
    tight_glow = tight_glow.filter(ImageFilter.GaussianBlur(radius=2))

    # Composite Glows
    base_img.alpha_composite(wide_glow)
    base_img.alpha_composite(tight_glow)

    # 3. Determine Smart Stroke Color
    # If text is dark (<128), stroke is white. If text is light, stroke is black.
    # We mix the stroke slightly with the text color to make it look less harsh.
    lum = get_luminance(text_color)
    stroke_rgb = (0, 0, 0) if lum > 128 else (255, 255, 255)

    # However, if the user requested a specific Shadow Color, we should respect that for the stroke
    # unless it ruins contrast. For now, let's stick to the AI's requested shadow color 
    # BUT force it to be fully opaque for the stroke line.
    stroke_rgb = glow_color

    draw = ImageDraw.Draw(base_img)

    # Draw Main Text with Stroke
    # stroke_width=1 adds a 1px border around the letters
    draw.text(
        (x, y), 
        text, 
        font=font, 
        fill=text_color + (255,), 
        stroke_width=1, 
        stroke_fill=stroke_rgb + (255,) # Fully opaque stroke
    )

    return base_img

def render_poster(img: Image.Image, haiku: str, block_num: int, design) -> Image.Image:
    print("4. Applying holistic render...")
    img = img.copy()
    w, h = img.size

    ref_dim = min(w, h)
    base_size = int(ref_dim * 0.045)

    font_main = get_font_by_vibe(design.font_vibe, base_size)
    font_footer = get_font_by_vibe("sans", int(base_size * 0.6))

    lines = [l.strip() for l in haiku.split('\n') if l.strip()]
    if not lines: lines = ["No Haiku"]

    line_h = int(base_size * 1.4)
    total_h = len(lines) * line_h
    center_y = int(h * (design.y_position_percent / 100))

    margin = int(h * 0.1)
    min_y = margin + (total_h // 2)
    max_y = h - margin - (total_h // 2) - int(h * 0.05)
    center_y = max(min_y, min(center_y, max_y))

    start_y = center_y - (total_h // 2)
    center_x = w // 2

    txt_rgb = hex_to_rgb(design.text_color_hex)
    shadow_rgb = hex_to_rgb(design.shadow_color_hex)

    curr_y = start_y
    for line in lines:
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), line, font=font_main)
        lw = bbox[2] - bbox[0]
        lx = center_x - (lw // 2)
        img = draw_text_with_glow(img, lx, curr_y, line, font_main, txt_rgb, shadow_rgb, design.shadow_strength)
        curr_y += line_h

    block_txt = f"Mochimo Block #{block_num}"
    b_bbox = draw.textbbox((0,0), block_txt, font=font_footer)
    bw = b_bbox[2] - b_bbox[0]
    bx = center_x - (bw // 2)
    by = h - int(h * 0.05)

    img = draw_text_with_glow(img, bx, by, block_txt, font_footer, (220,220,220), (0,0,0), 120)
    return img
