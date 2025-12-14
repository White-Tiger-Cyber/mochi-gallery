import argparse
import os
import json
import sys
import glob
import time
from PIL.PngImagePlugin import PngInfo
from .client import get_client, fetch_haiku, generate_image_prompt, generate_image_native, get_design_directives
from .painter import render_poster
# Import the new Web Gallery tools
from .gallery_utils import update_gallery_manifest, create_web_viewer

def list_available_styles():
    style_dir = os.path.join(os.getcwd(), "assets", "styles")
    if not os.path.exists(style_dir):
        print(f"Error: Style directory not found at {style_dir}")
        return

    json_files = glob.glob(os.path.join(style_dir, "*.json"))
    if not json_files:
        print("No styles found.")
        return

    print(f"\nAvailable Styles ({len(json_files)} found):")
    print(f"{'SHORT NAME':<20} | {'ASPECT':<8} | {'STYLE NAME'}")
    print("-" * 60)

    for f in sorted(json_files):
        try:
            filename = os.path.basename(f)
            short_name = os.path.splitext(filename)[0]
            with open(f, 'r') as json_file:
                data = json.load(json_file)
            print(f"{short_name:<20} | {data.get('aspect_ratio', '3:4'):<8} | {data.get('style_name', 'Unknown')}")
        except: continue
    print("-" * 60)

def resolve_style_path(user_input):
    if os.path.exists(user_input): return user_input
    default_path = os.path.join(os.getcwd(), "assets", "styles", f"{user_input}.json")
    if os.path.exists(default_path): return default_path
    return None

def load_mixed_styles(style_arg):
    if not style_arg: return None, ""

    style_names = style_arg.split('+')
    merged_data = {"style_name": [], "visual_directives": [], "aspect_ratio": None}
    prefix_parts = []

    for s_name in style_names:
        s_name = s_name.strip()
        resolved_path = resolve_style_path(s_name)
        if resolved_path:
            prefix_parts.append(os.path.splitext(os.path.basename(resolved_path))[0])
            try:
                with open(resolved_path, 'r') as f:
                    data = json.load(f)
                merged_data["style_name"].append(data.get("style_name", s_name))
                merged_data["visual_directives"].append(data.get("visual_directives", ""))
                if not merged_data["aspect_ratio"]:
                    merged_data["aspect_ratio"] = data.get("aspect_ratio")
            except Exception as e:
                print(f"   [WARN] Error loading style '{s_name}': {e}")
        else:
            print(f"   [WARN] Style '{s_name}' not found. Skipping.")

    if not merged_data["style_name"]: return None, ""

    final_style_data = {
        "style_name": " + ".join(merged_data["style_name"]),
        "visual_directives": "COMBINE THE FOLLOWING STYLES INTO A COHESIVE IMAGE:\n\n" + 
                             "\n\n".join([f"--- STYLE {i+1}: {name} ---\n{direct}" 
                                          for i, (name, direct) in enumerate(zip(merged_data['style_name'], merged_data['visual_directives']))]),
        "aspect_ratio": merged_data["aspect_ratio"] or "3:4"
    }
    return final_style_data, "_".join(prefix_parts) + "_"

def parse_block_range(block_input):
    blocks = []
    parts = block_input.split(',')
    for part in parts:
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if start > end: start, end = end, start
                if (end - start) > 50: end = start + 50
                blocks.extend(range(start, end + 1))
            except ValueError: continue
        else:
            try: blocks.append(int(part))
            except ValueError: continue
    return sorted(list(set(blocks)))

def get_unique_filepath(directory, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    full_path = os.path.join(directory, filename)
    while os.path.exists(full_path):
        new_filename = f"{base}_{counter}{ext}"
        full_path = os.path.join(directory, new_filename)
        counter += 1
    return full_path

def main():
    parser = argparse.ArgumentParser(description="Mochimo Gallery Generator")
    parser.add_argument("blocks", type=str, help="Block number, list (a,b), or range (a-b)")
    parser.add_argument("--style", type=str, help="Style name(s)", default=None)
    parser.add_argument("--ar", type=str, help="Override aspect ratio", default=None)
    parser.add_argument("--model", type=str, choices=['fast', 'standard', 'ultra'], default='standard', help="Google Imagen model")
    parser.add_argument("--output", type=str, help="Output directory", default="output")
    parser.add_argument("--mock", action="store_true", help="Skip API calls")

    known_models = ["gemini-3-pro-preview", "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash-thinking-exp"]
    parser.add_argument("--text-model", type=str, default="gemini-2.5-flash", help=f"Gemini model ID. Options: {', '.join(known_models)}")

    args = parser.parse_args()

    if args.blocks in ["?", "list"] or args.style in ["?", "list"]:
        list_available_styles()
        return

    block_list = parse_block_range(args.blocks)
    if not block_list: sys.exit("Error: No valid block numbers found.")

    os.makedirs(args.output, exist_ok=True)
    os.makedirs(os.path.join(args.output, "raw"), exist_ok=True)

    style_data, file_prefix = load_mixed_styles(args.style)
    aspect_ratio = "3:4"
    if style_data and style_data.get("aspect_ratio"): aspect_ratio = style_data["aspect_ratio"]
    if args.ar: aspect_ratio = args.ar

    if style_data: print(f"   > Visual Style: {style_data['style_name']}")

    try: client = get_client()
    except Exception as e: sys.exit(f"Client Init Error: {e}")

    total = len(block_list)
    print(f"\n--- Starting Batch Job: {total} Blocks ---")

    for index, block_num in enumerate(block_list):
        print(f"\n[{index+1}/{total}] Processing Block {block_num}...")
        
        try:
            haiku = fetch_haiku(block_num)
            if not haiku or "no haiku" in haiku.lower():
                print(f"   [SKIP] No haiku found for block {block_num}.")
                continue
            
            # --- RESTORED HAIKU DISPLAY ---
            print("\n" + "-"*30)
            print(haiku)
            print("-"*30 + "\n")
            # ------------------------------

            if args.mock:
                prompt = "Mock prompt."
            else:
                prompt = generate_image_prompt(client, haiku, style_data, aspect_ratio, text_model=args.text_model)
                
            # --- ART DIRECTOR OUTPUT ---
            print("="*60)
            print(f"🎨 ART DIRECTOR'S PROMPT ({args.text_model}):")
            print("-" * 60)
            print(prompt)
            print("="*60 + "\n")
            # ---------------------------

            img = generate_image_native(client, prompt, aspect_ratio, args.model, mock=args.mock)
            
            # Save Raw
            raw_filename = f"{file_prefix}raw_{block_num}.png"
            safe_raw_path = get_unique_filepath(os.path.join(args.output, "raw"), raw_filename)
            metadata = PngInfo()
            metadata.add_text("Haiku", haiku)
            metadata.add_text("Block", str(block_num))
            if style_data: metadata.add_text("Style", style_data.get("style_name", "Custom"))
            img.save(safe_raw_path, pnginfo=metadata)

            # Design & Render
            design = get_design_directives(client, img, haiku, text_model=args.text_model)
            poster = render_poster(img, haiku, block_num, design)
            
            poster_filename = f"{file_prefix}block_{block_num}.png"
            safe_out_path = get_unique_filepath(args.output, poster_filename)
            poster.save(safe_out_path, pnginfo=metadata)
            print(f"   > Saved: {safe_out_path}")

        except Exception as e:
            print(f"   [ERROR] Failed block {block_num}: {e}")
            continue
        
        if not args.mock and index < total - 1: time.sleep(1)

    print("\n--- Batch Complete ---")
    
# --- WEB GALLERY UPDATE ---
    try:
        # This function now handles everything (JSON + HTML generation)
        update_gallery_manifest(args.output)
    except Exception as e:
        print(f"   [WARN] Failed to update web gallery: {e}")

if __name__ == "__main__":
    main()
