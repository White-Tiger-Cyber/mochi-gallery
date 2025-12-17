import os
import glob
import json
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL.PngImagePlugin import PngInfo

# Import your existing engine
from src.mochi_gallery.client import get_client, fetch_haiku, generate_image_prompt, generate_image_native, get_design_directives
from src.mochi_gallery.painter import render_poster
from src.mochi_gallery.gallery_utils import update_gallery_manifest

app = Flask(__name__)

# Config
OUTPUT_DIR = os.path.join(os.getcwd(), 'output')
STYLE_DIR = os.path.join(os.getcwd(), 'assets', 'styles')
os.makedirs(os.path.join(OUTPUT_DIR, 'raw'), exist_ok=True)

def get_styles():
    styles = []
    files = glob.glob(os.path.join(STYLE_DIR, "*.json"))
    for f in sorted(files):
        try:
            with open(f, 'r') as j:
                data = json.load(j)
                name = os.path.splitext(os.path.basename(f))[0]
                pretty_name = data.get('style_name', name)
                styles.append({"id": name, "name": pretty_name})
        except: continue
    return styles

@app.route('/')
def index():
    """Render the Generator Interface"""
    return render_template('generator.html', styles=get_styles())

@app.route('/gallery')
def gallery():
    """Serve your existing static gallery with NO CACHE"""
    # Ensure gallery is up to date
    update_gallery_manifest(OUTPUT_DIR)
    
    # Serve the file but force browser to not cache it
    response = send_from_directory(OUTPUT_DIR, 'index.html')
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/gallery/<path:filename>')
def serve_gallery_assets(filename):
    """Handle relative path requests from the gallery page (images inside output)"""
    return send_from_directory(OUTPUT_DIR, filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve files from the local assets directory (like logo.png)"""
    return send_from_directory(os.path.join(os.getcwd(), 'assets'), filename)

@app.route('/output/<path:filename>')
def serve_output(filename):
    """Serve images for the Generator preview"""
    return send_from_directory(OUTPUT_DIR, filename)

@app.route('/api/haiku', methods=['POST'])
def get_haiku_text():
    block_num = request.form.get('block_num')
    try:
        haiku = fetch_haiku(int(block_num))
        if not haiku or "no haiku" in haiku.lower():
            return "<div class='text-red-500'>No Haiku found for this block.</div>"
        return f"<div class='haiku-preview'>{haiku}</div>"
    except Exception as e:
        return f"<div class='text-red-500'>Error: {str(e)}</div>"

@app.route('/generate', methods=['POST'])
def generate():
    block_num = int(request.form.get('block_num'))
    
    # CHANGED: Get both styles
    style_id_1 = request.form.get('style_1')
    style_id_2 = request.form.get('style_2')
    
    model = request.form.get('model')
    ar = request.form.get('ar')
    text_model = request.form.get('text_model')
    
    client = get_client()
    haiku = fetch_haiku(block_num)
    
    # --- STYLE MERGING LOGIC ---
    style_data = None
    active_styles = []
    
    # Helper to load a style dict
    def load_style_json(sid):
        if not sid or sid == "none": return None
        path = os.path.join(STYLE_DIR, f"{sid}.json")
        if os.path.exists(path):
            with open(path, 'r') as f: return json.load(f)
        return None

    s1_data = load_style_json(style_id_1)
    s2_data = load_style_json(style_id_2)

    # Logic: 
    # 1. If only S1: Use S1
    # 2. If only S2: Use S2
    # 3. If Both: Merge them
    
    if s1_data and not s2_data:
        style_data = s1_data
        active_styles.append(style_id_1)
    elif s2_data and not s1_data:
        style_data = s2_data
        active_styles.append(style_id_2)
    elif s1_data and s2_data:
        # The Merge
        active_styles = [style_id_1, style_id_2]
        style_data = {
            "style_name": f"{s1_data.get('style_name')} + {s2_data.get('style_name')}",
            "visual_directives": (
                "COMBINE THE FOLLOWING STYLES INTO A COHESIVE IMAGE:\n\n"
                f"--- STYLE 1: {s1_data.get('style_name')} ---\n{s1_data.get('visual_directives')}\n\n"
                f"--- STYLE 2: {s2_data.get('style_name')} ---\n{s2_data.get('visual_directives')}"
            ),
            # Default to S1's Aspect Ratio, unless S1 is missing it
            "aspect_ratio": s1_data.get("aspect_ratio", s2_data.get("aspect_ratio"))
        }

    # Generate Prompt
    prompt = generate_image_prompt(client, haiku, style_data, ar, text_model=text_model)
    
    # Paint
    img = generate_image_native(client, prompt, ar, model)
    
    # Design
    design = get_design_directives(client, img, haiku, text_model=text_model)
    poster = render_poster(img, haiku, block_num, design)
    
    # Save
    style_prefix = "_".join(active_styles) if active_styles else "custom"
    filename = f"{style_prefix}_block_{block_num}_{int(time.time())}.png"
    save_path = os.path.join(OUTPUT_DIR, filename)
    
    meta = PngInfo()
    meta.add_text("Haiku", haiku)
    meta.add_text("Block", str(block_num))
    if style_data:
        meta.add_text("Style", style_data.get("style_name", "Custom"))
        
    poster.save(save_path, pnginfo=meta)
    
    return render_template('partial_result.html', filename=filename, prompt=prompt)

# --- NEW ROUTE: Soft Delete ---
@app.route('/delete', methods=['POST'])
def delete_artifact():
    filename = request.form.get('filename')
    
    # Security: Prevent directory traversal
    if not filename or '..' in filename or '/' in filename:
        return "Invalid filename", 400

    src_path = os.path.join(OUTPUT_DIR, filename)
    trash_dir = os.path.join(OUTPUT_DIR, 'deleted')
    os.makedirs(trash_dir, exist_ok=True)
    dst_path = os.path.join(trash_dir, filename)

    if os.path.exists(src_path):
        try:
            # Move file to trash
            os.rename(src_path, dst_path)
            # Rebuild gallery.json immediately
            update_gallery_manifest(OUTPUT_DIR)
            return "OK", 200
        except Exception as e:
            return str(e), 500
    else:
        return "File not found", 404

if __name__ == '__main__':
    print("Starting Flask Server...")
    app.run(debug=True, port=5000, host='0.0.0.0')
