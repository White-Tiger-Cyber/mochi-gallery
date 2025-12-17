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

    create_web_viewer(output_dir, gallery_items)

def create_web_viewer(output_dir, data):
    """
    Generates index.html using a safe string template (no f-string) to avoid syntax errors.
    """
    html_path = os.path.join(output_dir, "index.html")
    
    # Serialize data to JSON string
    json_data = json.dumps(data)

    # NOTE: This is a STANDARD string, not an f-string. 
    # We use __JSON_DATA__ as a placeholder to replace later.
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mochimo Gallery</title>
    
    <script src="https://unpkg.com/imagesloaded@5/imagesloaded.pkgd.min.js"></script>
    <script src="https://unpkg.com/masonry-layout@4/dist/masonry.pkgd.min.js"></script>

    <style>
        :root { --bg: #0a0a0a; --card: #141414; --text: #e0e0e0; --accent: #00ff41; --overlay: rgba(0,0,0,0.95); }
        
        body { background: var(--bg); color: var(--text); font-family: 'Courier New', monospace; margin: 0; padding: 20px; overflow-y: scroll; }
        
        header { text-align: center; padding: 40px 0 20px; border-bottom: 1px solid #333; margin-bottom: 30px; }
        .logo { width: 80px; height: auto; margin-bottom: 15px; display: block; margin-left: auto; margin-right: auto; }
        h1 { font-size: 2.5rem; margin: 0; letter-spacing: -2px; color: #fff; }
        .subtitle { color: var(--accent); font-size: 0.9rem; margin-top: 10px; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; }
        
        #filters { display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; margin-top: 20px; }
        .filter-btn { 
            background: #202020; color: #666; border: 1px solid #333; padding: 8px 16px; 
            border-radius: 4px; cursor: pointer; font-family: inherit; font-size: 0.75rem;
            transition: all 0.2s; text-transform: uppercase; user-select: none;
        }
        .filter-btn:hover { border-color: var(--accent); color: var(--accent); }
        .filter-btn.active { background: var(--accent); color: #000; border-color: var(--accent); font-weight: bold; }

        .gallery { max-width: 1800px; margin: 0 auto; }
        
        .card { 
            width: 320px; margin-bottom: 20px; background: var(--card); border-radius: 4px; 
            overflow: hidden; transition: transform 0.2s ease, box-shadow 0.2s ease; 
            border: 1px solid #222; cursor: pointer; opacity: 0; animation: fadeIn 0.5s forwards;
        }
        .card:hover { transform: translateY(-3px); border-color: var(--accent); box-shadow: 0 0 15px rgba(0, 255, 65, 0.1); z-index: 10; }
        .card img { width: 100%; height: auto; display: block; border-bottom: 1px solid #222; }
        
        .meta { padding: 20px; }
        .block-id { font-size: 0.8rem; color: var(--accent); font-weight: bold; display: block; margin-bottom: 10px; }
        .haiku { font-size: 1.1rem; line-height: 1.4; color: #fff; white-space: pre-wrap; font-style: italic; }
        .tags { display: flex; gap: 10px; font-size: 0.65rem; color: #666; margin-top: 15px; text-transform: uppercase; }

        #lightbox { 
            position: fixed; inset: 0; background: var(--overlay); z-index: 1000; 
            display: none; justify-content: center; align-items: center; flex-direction: column;
            backdrop-filter: blur(5px);
        }
        #lightbox.active { display: flex; }
        #lightbox img { 
            max-height: 80vh; max-width: 90vw; border-radius: 4px; box-shadow: 0 0 50px rgba(0, 255, 65, 0.1); 
            border: 1px solid #333;
        }
        .lb-nav {
            position: absolute; top: 50%; transform: translateY(-50%);
            font-size: 4rem; color: #444; cursor: pointer; user-select: none;
            padding: 20px; transition: color 0.2s;
        }
        .lb-nav:hover { color: var(--accent); text-shadow: 0 0 10px var(--accent); }
        #lb-prev { left: 20px; }
        #lb-next { right: 20px; }
        #lightbox .lb-meta { margin-top: 20px; text-align: center; max-width: 600px; }
        #lightbox .lb-haiku { color: #fff; font-size: 1.2rem; font-style: italic; margin-bottom: 10px; }
        #lightbox .lb-info { color: var(--accent); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }
        #lb-close { position: absolute; top: 20px; right: 30px; font-size: 3rem; color: #444; cursor: pointer; }
        #lb-close:hover { color: var(--accent); }

        /* DELETE BUTTON */
        #lb-delete { 
            position: absolute; top: 20px; left: 30px; 
            font-size: 1.2rem; color: #666; cursor: pointer; 
            border: 1px solid #333; padding: 5px 12px; border-radius: 4px;
            transition: all 0.2s; font-weight: bold; font-family: inherit;
        }
        #lb-delete:hover { color: #ff0055; border-color: #ff0055; background: rgba(255, 0, 85, 0.1); }

        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    </style>
</head>
<body>

<header>
    <!-- Logo with Absolute Path -->
    <img src="/assets/img/logo.png" alt="Mochimo Logo" class="logo">
    
    <h1>MOCHIMO GALLERY</h1>
    <div class="subtitle">AI-GENERATED BLOCKCHAIN ARTIFACTS</div>
    <div id="filters">
        <button id="btn-all" class="filter-btn active" onclick="toggleFilter('all')">ALL</button>
    </div>
</header>

<div class="gallery" id="gallery"></div>

<!-- Lightbox -->
<div id="lightbox" onclick="closeLightbox(event)">
    <span id="lb-close">&times;</span>
    <div id="lb-delete" onclick="deleteCurrent(event)" title="Move to Trash">🗑 DELETE</div>
    
    <div id="lb-prev" class="lb-nav" onclick="nav(-1); event.stopPropagation();">‹</div>
    <div id="lb-next" class="lb-nav" onclick="nav(1); event.stopPropagation();">›</div>
    
    <img id="lb-img" src="">
    
    <div class="lb-meta">
        <div id="lb-haiku" class="lb-haiku"></div>
        <div id="lb-info" class="lb-info"></div>
    </div>
</div>

<script>
    const DATA = __JSON_DATA__;
    const container = document.getElementById('gallery');
    const filterNav = document.getElementById('filters');
    
    let activeFilters = new Set();
    let currentItems = []; 
    let currentIndex = 0; 
    let msnry; 

    // Filters
    const styles = [...new Set(DATA.map(i => i.style))].sort();
    styles.forEach(style => {
        const btn = document.createElement('button');
        btn.className = 'filter-btn';
        btn.innerText = style;
        btn.dataset.style = style;
        btn.onclick = () => toggleFilter(style);
        filterNav.appendChild(btn);
    });

    // Render
    function render(items) {
        currentItems = items;
        if (msnry) msnry.destroy();
        container.innerHTML = '';
        items.forEach((item, index) => {
            const card = document.createElement('div');
            card.className = 'card';
            card.onclick = () => openLightbox(index);
            
            card.innerHTML = `
                <img src="/output/${item.filename}" alt="Block ${item.block}">
                <div class="meta">
                    <span class="block-id">BLOCK #${item.block}</span>
                    <div class="haiku">${item.haiku}</div>
                    <div class="tags">${item.style}</div>
                </div>
            `;
            container.appendChild(card);
        });
        imagesLoaded( container, function() {
            msnry = new Masonry( container, { itemSelector: '.card', columnWidth: 320, gutter: 20, fitWidth: true });
        });
    }

    function toggleFilter(style) {
        const allBtn = document.getElementById('btn-all');
        const styleBtns = document.querySelectorAll('.filter-btn:not(#btn-all)');
        if (style === 'all') { activeFilters.clear(); } 
        else { if (activeFilters.has(style)) activeFilters.delete(style); else activeFilters.add(style); }

        if (activeFilters.size === 0) {
            allBtn.classList.add('active');
            styleBtns.forEach(b => b.classList.remove('active'));
            render(DATA);
        } else {
            allBtn.classList.remove('active');
            styleBtns.forEach(b => {
                if (activeFilters.has(b.dataset.style)) b.classList.add('active');
                else b.classList.remove('active');
            });
            const filtered = DATA.filter(item => activeFilters.has(item.style));
            render(filtered);
        }
    }

    const lb = document.getElementById('lightbox');
    const lbImg = document.getElementById('lb-img');
    const lbHaiku = document.getElementById('lb-haiku');
    const lbInfo = document.getElementById('lb-info');

    function openLightbox(index) {
        currentIndex = index;
        updateLightbox();
        lb.classList.add('active');
    }

    function updateLightbox() {
        const item = currentItems[currentIndex];
        lbImg.src = "/output/" + item.filename;
        lbHaiku.innerText = item.haiku;
        lbInfo.innerText = `BLOCK #${item.block} // ${item.style}`;
    }

    function nav(dir) {
        currentIndex += dir;
        if (currentIndex < 0) currentIndex = currentItems.length - 1;
        if (currentIndex >= currentItems.length) currentIndex = 0;
        updateLightbox();
    }

    // Delete Logic
    function deleteCurrent(e) {
        e.stopPropagation();
        const item = currentItems[currentIndex];
        if (!confirm(`Are you sure you want to delete block #${item.block}?`)) return;

        fetch('/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: `filename=${item.filename}`
        })
        .then(res => {
            if (res.ok) {
                const globalIndex = DATA.indexOf(item);
                if (globalIndex > -1) DATA.splice(globalIndex, 1);
                currentItems.splice(currentIndex, 1);
                
                lb.classList.remove('active');
                render(currentItems);
            } else {
                alert("Error deleting file.");
            }
        });
    }

    function closeLightbox(e) {
        if (e.target === lb || e.target.id === 'lb-close') {
            lb.classList.remove('active');
        }
    }

    render(DATA);
    
    document.addEventListener('keydown', (e) => {
        if (!lb.classList.contains('active')) return;
        if (e.key === 'Escape') lb.classList.remove('active');
        if (e.key === 'ArrowLeft') nav(-1);
        if (e.key === 'ArrowRight') nav(1);
    });
</script>

</body>
</html>
    """
    
    # Safe injection
    final_html = html_template.replace("__JSON_DATA__", json_data)
    
    with open(html_path, "w") as f:
        f.write(final_html)
    print(f"   > Web Viewer updated: {html_path}")
