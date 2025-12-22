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
    Generates index.html with Masonry, Filtering, Lightbox, and PAGINATION.
    """
    html_path = os.path.join(output_dir, "index.html")
    
    # Serialize data to JSON string
    json_data = json.dumps(data)

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
        
        /* Filters */
        #filters { display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; margin-top: 20px; }
        .filter-btn { 
            background: #202020; color: #666; border: 1px solid #333; padding: 8px 16px; 
            border-radius: 4px; cursor: pointer; font-family: inherit; font-size: 0.75rem;
            transition: all 0.2s; text-transform: uppercase; user-select: none;
        }
        .filter-btn:hover { border-color: var(--accent); color: var(--accent); }
        .filter-btn.active { background: var(--accent); color: #000; border-color: var(--accent); font-weight: bold; }

        /* Pagination Bar */
        #pagination-bar {
            display: flex; justify-content: space-between; align-items: center;
            max-width: 1800px; margin: 20px auto; padding: 10px; background: #111; border: 1px solid #222; border-radius: 4px;
        }
        .page-controls { display: flex; align-items: center; gap: 15px; }
        select { background: #222; color: #fff; border: 1px solid #444; padding: 5px; border-radius: 4px; font-family: inherit; }
        .page-btn {
            background: #222; color: var(--accent); border: 1px solid #444; padding: 5px 15px; cursor: pointer; border-radius: 4px;
        }
        .page-btn:disabled { color: #444; border-color: #222; cursor: default; }
        .page-btn:hover:not(:disabled) { border-color: var(--accent); }
        #page-info { font-size: 0.9rem; color: #888; }

        .gallery { max-width: 1800px; margin: 0 auto; min-height: 500px; }
        
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
    <img src="/assets/img/logo.png" alt="Mochimo Logo" class="logo">
    <h1>MOCHIMO GALLERY</h1>
    <div class="subtitle">AI-GENERATED BLOCKCHAIN ARTIFACTS</div>
    
    <div id="filters">
        <button id="btn-all" class="filter-btn active" onclick="toggleFilter('all')">ALL</button>
    </div>
</header>

<!-- Pagination Control Bar -->
<div id="pagination-bar">
    <div class="page-controls">
        <label for="pageSize" style="color: #666; font-size: 0.8rem;">ITEMS PER PAGE:</label>
        <select id="pageSize" onchange="changePageSize()">
            <option value="20">20</option>
            <option value="50" selected>50</option>
            <option value="100">100</option>
            <option value="999999">ALL</option>
        </select>
    </div>
    
    <div class="page-controls">
        <button id="btn-prev" class="page-btn" onclick="changePage(-1)">PREV</button>
        <span id="page-info">Page 1 of 1</span>
        <button id="btn-next" class="page-btn" onclick="changePage(1)">NEXT</button>
    </div>
</div>

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
    
    // State
    let activeFilters = new Set();
    let filteredData = DATA; // Contains all items matching current filters
    let currentViewData = []; // Contains only items on current page
    let msnry; 
    
    // Pagination State
    let currentPage = 1;
    let itemsPerPage = 50;

    // 1. Initialize Filters
    const styles = [...new Set(DATA.map(i => i.style))].sort();
    styles.forEach(style => {
        const btn = document.createElement('button');
        btn.className = 'filter-btn';
        btn.innerText = style;
        btn.dataset.style = style;
        btn.onclick = () => toggleFilter(style);
        filterNav.appendChild(btn);
    });

    // 2. Pagination Logic
    function applyPagination() {
        const start = (currentPage - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        currentViewData = filteredData.slice(start, end);
        
        render(currentViewData);
        updatePaginationControls();
    }

    function changePageSize() {
        itemsPerPage = parseInt(document.getElementById('pageSize').value);
        currentPage = 1; // Reset to start
        applyPagination();
    }

    function changePage(delta) {
        const maxPage = Math.ceil(filteredData.length / itemsPerPage);
        const newPage = currentPage + delta;
        
        if (newPage >= 1 && newPage <= maxPage) {
            currentPage = newPage;
            applyPagination();
            // Scroll to top of gallery smoothly
            document.getElementById('pagination-bar').scrollIntoView({behavior: 'smooth'});
        }
    }

    function updatePaginationControls() {
        const maxPage = Math.ceil(filteredData.length / itemsPerPage) || 1;
        document.getElementById('page-info').innerText = `Page ${currentPage} of ${maxPage}`;
        document.getElementById('btn-prev').disabled = (currentPage === 1);
        document.getElementById('btn-next').disabled = (currentPage === maxPage);
    }

    // 3. Render
    function render(items) {
        if (msnry) msnry.destroy();
        container.innerHTML = '';
        items.forEach((item, index) => {
            const card = document.createElement('div');
            card.className = 'card';
            // Important: Lightbox index now refers to currentViewData index
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

    // 4. Filter Logic
    function toggleFilter(style) {
        const allBtn = document.getElementById('btn-all');
        const styleBtns = document.querySelectorAll('.filter-btn:not(#btn-all)');
        
        if (style === 'all') { activeFilters.clear(); } 
        else { if (activeFilters.has(style)) activeFilters.delete(style); else activeFilters.add(style); }

        // Update UI Classes
        if (activeFilters.size === 0) {
            allBtn.classList.add('active');
            styleBtns.forEach(b => b.classList.remove('active'));
            filteredData = DATA;
        } else {
            allBtn.classList.remove('active');
            styleBtns.forEach(b => {
                if (activeFilters.has(b.dataset.style)) b.classList.add('active');
                else b.classList.remove('active');
            });
            filteredData = DATA.filter(item => activeFilters.has(item.style));
        }
        
        // Reset pagination when filters change
        currentPage = 1;
        applyPagination();
    }

    // 5. Lightbox Logic
    const lb = document.getElementById('lightbox');
    const lbImg = document.getElementById('lb-img');
    const lbHaiku = document.getElementById('lb-haiku');
    const lbInfo = document.getElementById('lb-info');
    let lightboxIndex = 0; // Local index relative to currentViewData

    function openLightbox(index) {
        lightboxIndex = index;
        updateLightbox();
        lb.classList.add('active');
    }

    function updateLightbox() {
        const item = currentViewData[lightboxIndex];
        lbImg.src = "/output/" + item.filename;
        lbHaiku.innerText = item.haiku;
        lbInfo.innerText = `BLOCK #${item.block} // ${item.style}`;
    }

    function nav(dir) {
        lightboxIndex += dir;
        if (lightboxIndex < 0) lightboxIndex = currentViewData.length - 1;
        if (lightboxIndex >= currentViewData.length) lightboxIndex = 0;
        updateLightbox();
    }

    // Delete Logic
    function deleteCurrent(e) {
        e.stopPropagation();
        const item = currentViewData[lightboxIndex];
        if (!confirm(`Are you sure you want to delete block #${item.block}?`)) return;

        fetch('/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: `filename=${item.filename}`
        })
        .then(res => {
            if (res.ok) {
                // Remove from Master DATA
                const globalIndex = DATA.indexOf(item);
                if (globalIndex > -1) DATA.splice(globalIndex, 1);
                
                // Remove from Filtered Data
                const filteredIndex = filteredData.indexOf(item);
                if (filteredIndex > -1) filteredData.splice(filteredIndex, 1);

                // Close and refresh current page view
                lb.classList.remove('active');
                applyPagination();
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

    // Initial Load
    applyPagination();
    
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
