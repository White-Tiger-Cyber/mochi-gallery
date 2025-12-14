import os
import glob
import json
from PIL import Image

def update_gallery_manifest(output_dir):
    """
    Scans for images, builds the data list, and regenerates the HTML.
    """
    print(f"   > Updating Web Gallery in {output_dir}...")
    
    gallery_items = []
    
    # Find all poster images
    search_path = os.path.join(output_dir, "*block_*.png")
    files = glob.glob(search_path)
    
    for file_path in files:
        try:
            filename = os.path.basename(file_path)
            
            with Image.open(file_path) as img:
                meta = img.text or img.info
                item = {
                    "filename": filename,
                    "block": meta.get("Block", "Unknown"),
                    "haiku": meta.get("Haiku", "No Haiku"),
                    "style": meta.get("Style", "Custom"),
                    "timestamp": os.path.getmtime(file_path)
                }
                gallery_items.append(item)
        except Exception as e:
            print(f"     [WARN] Could not read {filename}: {e}")
            continue

    # Sort: Newest Blocks First
    try:
        gallery_items.sort(key=lambda x: int(x['block']), reverse=True)
    except:
        gallery_items.sort(key=lambda x: x['timestamp'], reverse=True)

    # REFACTOR: Pass the data directly to the HTML generator
    create_web_viewer(output_dir, gallery_items)

def create_web_viewer(output_dir, data):
    """
    Generates index.html with EMBEDDED JSON data to bypass CORS issues.
    """
    html_path = os.path.join(output_dir, "index.html")
    
    # Serialize data to JSON string for embedding
    json_data = json.dumps(data)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mochimo Gallery</title>
    <style>
        :root {{ --bg: #0f0f12; --card: #1a1a20; --text: #e0e0e0; --accent: #ff0055; }}
        body {{ background: var(--bg); color: var(--text); font-family: 'Courier New', monospace; margin: 0; padding: 20px; }}
        header {{ text-align: center; padding: 40px 0; border-bottom: 1px solid #333; margin-bottom: 40px; }}
        h1 {{ font-size: 2.5rem; margin: 0; letter-spacing: -2px; }}
        .subtitle {{ color: #666; font-size: 0.9rem; margin-top: 10px; }}
        
        .gallery {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
            gap: 30px; 
            max-width: 1600px; 
            margin: 0 auto; 
        }}
        
        .card {{ 
            background: var(--card); 
            border-radius: 8px; 
            overflow: hidden; 
            transition: transform 0.2s ease; 
            border: 1px solid #333;
        }}
        .card:hover {{ transform: translateY(-5px); border-color: var(--accent); }}
        
        .card img {{ width: 100%; height: auto; display: block; border-bottom: 1px solid #333; }}
        
        .meta {{ padding: 20px; }}
        .block-id {{ font-size: 0.8rem; color: var(--accent); font-weight: bold; text-transform: uppercase; margin-bottom: 10px; display: block; }}
        .haiku {{ font-size: 1.1rem; line-height: 1.4; color: #fff; white-space: pre-wrap; margin-bottom: 15px; font-style: italic; }}
        .tags {{ display: flex; gap: 10px; font-size: 0.7rem; color: #888; text-transform: uppercase; }}
        .tag {{ background: #252530; padding: 4px 8px; border-radius: 4px; }}
    </style>
</head>
<body>

<header>
    <h1>MOCHIMO GALLERY</h1>
    <div class="subtitle">AI-GENERATED BLOCKCHAIN ARTIFACTS</div>
</header>

<div class="gallery" id="gallery"></div>

<script>
    // DATA EMBEDDED DIRECTLY TO BYPASS CORS
    const GALLERY_DATA = {json_data};

    const container = document.getElementById('gallery');
    
    GALLERY_DATA.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <a href="${{item.filename}}" target="_blank">
                <img src="${{item.filename}}" alt="Block ${{item.block}}" loading="lazy">
            </a>
            <div class="meta">
                <span class="block-id">BLOCK #${{item.block}}</span>
                <div class="haiku">${{item.haiku}}</div>
                <div class="tags">
                    <span class="tag">${{item.style}}</span>
                </div>
            </div>
        `;
        container.appendChild(card);
    }});
</script>

</body>
</html>
    """
    
    with open(html_path, "w") as f:
        f.write(html_content)
    print(f"   > Web Viewer updated: {html_path}")
