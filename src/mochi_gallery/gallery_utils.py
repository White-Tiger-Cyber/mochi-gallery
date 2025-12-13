import os
import glob
import json
from PIL import Image

def update_gallery_manifest(output_dir):
    """
    Scans the output directory for 'block_*.png' files,
    reads their embedded metadata, and creates a gallery.json file.
    """
    print(f"   > Updating Web Gallery manifest in {output_dir}...")
    
    gallery_items = []
    
    # Find all poster images (ignore raw images)
    search_path = os.path.join(output_dir, "block_*.png")
    files = glob.glob(search_path)
    
    for file_path in files:
        try:
            filename = os.path.basename(file_path)
            
            # Read Metadata directly from the PNG chunks
            with Image.open(file_path) as img:
                # PngInfo is stored in img.text or img.info
                meta = img.text or img.info
                
                # Extract data or use defaults
                item = {
                    "filename": filename,
                    "block": meta.get("Block", "Unknown"),
                    "haiku": meta.get("Haiku", "No Haiku"),
                    "style": meta.get("Style", "Custom"),
                    "timestamp": os.path.getmtime(file_path) # For sorting
                }
                gallery_items.append(item)
        except Exception as e:
            print(f"     [WARN] Could not read {filename}: {e}")
            continue

    # Sort by Block Number (Descending - Newest blocks first)
    # If block is not a number, sort by timestamp
    try:
        gallery_items.sort(key=lambda x: int(x['block']), reverse=True)
    except:
        gallery_items.sort(key=lambda x: x['timestamp'], reverse=True)

    # Write JSON
    manifest_path = os.path.join(output_dir, "gallery.json")
    with open(manifest_path, "w") as f:
        json.dump(gallery_items, f, indent=2)
        
    print(f"   > Gallery updated: {len(gallery_items)} items indexed.")

def create_web_viewer(output_dir):
    """
    Copies the HTML template to the output folder if it doesn't exist.
    """
    html_path = os.path.join(output_dir, "index.html")
    if os.path.exists(html_path):
        return

    # A simple, sleek, dark-mode gallery template
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mochimo Gallery</title>
    <style>
        :root { --bg: #0f0f12; --card: #1a1a20; --text: #e0e0e0; --accent: #ff0055; }
        body { background: var(--bg); color: var(--text); font-family: 'Courier New', monospace; margin: 0; padding: 20px; }
        header { text-align: center; padding: 40px 0; border-bottom: 1px solid #333; margin-bottom: 40px; }
        h1 { font-size: 2.5rem; margin: 0; letter-spacing: -2px; }
        .subtitle { color: #666; font-size: 0.9rem; margin-top: 10px; }
        
        /* Grid Layout */
        .gallery { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
            gap: 30px; 
            max-width: 1600px; 
            margin: 0 auto; 
        }
        
        /* Card Vibe */
        .card { 
            background: var(--card); 
            border-radius: 8px; 
            overflow: hidden; 
            transition: transform 0.2s ease; 
            border: 1px solid #333;
        }
        .card:hover { transform: translateY(-5px); border-color: var(--accent); }
        
        .card img { width: 100%; height: auto; display: block; border-bottom: 1px solid #333; }
        
        .meta { padding: 20px; }
        .block-id { font-size: 0.8rem; color: var(--accent); font-weight: bold; text-transform: uppercase; margin-bottom: 10px; display: block; }
        .haiku { font-size: 1.1rem; line-height: 1.4; color: #fff; white-space: pre-wrap; margin-bottom: 15px; font-style: italic; }
        .tags { display: flex; gap: 10px; font-size: 0.7rem; color: #888; text-transform: uppercase; }
        .tag { background: #252530; padding: 4px 8px; border-radius: 4px; }
        
        /* Loading */
        #loading { text-align: center; color: #666; margin-top: 50px; }
    </style>
</head>
<body>

<header>
    <h1>MOCHIMO GALLERY</h1>
    <div class="subtitle">AI-GENERATED BLOCKCHAIN ARTIFACTS</div>
</header>

<div id="loading">Scanning Output Directory...</div>
<div class="gallery" id="gallery"></div>

<script>
    fetch('gallery.json')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('gallery');
            document.getElementById('loading').style.display = 'none';
            
            data.forEach(item => {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `
                    <a href="${item.filename}" target="_blank">
                        <img src="${item.filename}" alt="Block ${item.block}" loading="lazy">
                    </a>
                    <div class="meta">
                        <span class="block-id">BLOCK #${item.block}</span>
                        <div class="haiku">${item.haiku}</div>
                        <div class="tags">
                            <span class="tag">${item.style}</span>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        })
        .catch(err => {
            document.getElementById('loading').innerHTML = "Error loading gallery.json<br>Make sure you ran the CLI first!";
            console.error(err);
        });
</script>

</body>
</html>
    """
    
    with open(html_path, "w") as f:
        f.write(html_content)
    print(f"   > Web Viewer created: {html_path}")
