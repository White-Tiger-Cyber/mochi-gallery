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
    style_id = request.form.get('style')
    model = request.form.get('model')
    ar = request.form.get('ar')
    text_model = request.form.get('text_model')
    
    client = get_client()
    haiku = fetch_haiku(block_num)
    
    style_data = None
    if style_id != "none":
        path = os.path.join(STYLE_DIR, f"{style_id}.json")
        if os.path.exists(path):
            with open(path, 'r') as f: style_data = json.load(f)

    prompt = generate_image_prompt(client, haiku, style_data, ar, text_model=text_model)
    img = generate_image_native(client, prompt, ar, model)
    design = get_design_directives(client, img, haiku, text_model=text_model)
    poster = render_poster(img, haiku, block_num, design)
    
    filename = f"{style_id if style_id else 'custom'}_block_{block_num}_{int(time.time())}.png"
    save_path = os.path.join(OUTPUT_DIR, filename)
    
    meta = PngInfo()
    meta.add_text("Haiku", haiku)
    meta.add_text("Block", str(block_num))
    poster.save(save_path, pnginfo=meta)
    
    return render_template('partial_result.html', filename=filename, prompt=prompt)

if __name__ == '__main__':
    print("Starting Flask Server...")
    app.run(debug=True, port=5000, host='0.0.0.0')
