import argparse
import os
import json
import sys
import glob
from PIL.PngImagePlugin import PngInfo
from .client import get_client, fetch_haiku, generate_image_prompt, generate_image_native, get_design_directives
from .painter import render_poster

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

def get_unique_filepath(directory, filename):
    """
    Checks if filename exists in directory. If so, appends _1, _2, etc.
    Returns the full safe path.
    """
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
    parser.add_argument("block_number", type=str, help="Mochimo Block Number (or '?' to list styles)")
    parser.add_argument("--style", type=str, help="Short name (e.g. 'ghibli') or path to JSON file", default=None)
    parser.add_argument("--ar", type=str, help="Override aspect ratio (e.g. 16:9, 1:1)", default=None)
    parser.add_argument("--model", type=str, choices=['fast', 'standard', 'ultra'], default='standard', help="Google Imagen model to use")
    parser.add_argument("--output", type=str, help="Output directory", default="output")
    parser.add_argument("--mock", action="store_true", help="Skip API calls and use placeholder images")
    
    args = parser.parse_args()

    # Handle Lists
    if args.block_number in ["?", "list"] or args.style in ["?", "list"]:
        list_available_styles()
        return

    try:
        block_num_int = int(args.block_number)
    except ValueError:
        print(f"Error: Block number must be an integer.")
        return

    os.makedirs(args.output, exist_ok=True)
    os.makedirs(os.path.join(args.output, "raw"), exist_ok=True)

    # --- SETUP ---
    style_data = None
    file_prefix = ""
    aspect_ratio = "3:4" 
    VALID_RATIOS = ["1:1", "3:4", "4:3", "9:16", "16:9"]

    if args.style:
        resolved_path = resolve_style_path(args.style)
        if resolved_path:
            try:
                file_prefix = f"{os.path.splitext(os.path.basename(resolved_path))[0]}_"
                with open(resolved_path, 'r') as f:
                    style_data = json.load(f)
                if "aspect_ratio" in style_data and style_data["aspect_ratio"] in VALID_RATIOS:
                    aspect_ratio = style_data["aspect_ratio"]
                print(f"   > Loaded Style: {style_data.get('style_name', 'Custom')} ({aspect_ratio})")
            except Exception as e:
                sys.exit(f"Error loading style: {e}")
        else:
            sys.exit(f"Error: Style '{args.style}' not found.")

    # Override AR
    if args.ar:
        if args.ar in VALID_RATIOS:
            aspect_ratio = args.ar
            print(f"   > Enforcing CLI Aspect Ratio: {aspect_ratio}")
        else:
            sys.exit(f"Error: Invalid aspect ratio '{args.ar}'. Supported: {VALID_RATIOS}")

    # --- EXECUTION ---
    client = get_client()
    haiku = fetch_haiku(block_num_int)
    
    if not haiku or "no haiku" in haiku.lower():
        print("No haiku found.")
        return

    print(f"--- Block {block_num_int} ---")
    print(haiku)

    if args.mock:
        prompt = "Mock prompt."
    else:
        prompt = generate_image_prompt(client, haiku, style_data, aspect_ratio)

    # Generate Image (passing model alias)
    img = generate_image_native(client, prompt, aspect_ratio, args.model, mock=args.mock)
    
    # Save Raw (Safe)
    raw_filename = f"{file_prefix}raw_{block_num_int}.png"
    safe_raw_path = get_unique_filepath(os.path.join(args.output, "raw"), raw_filename)
    
    # Prepare Metadata
    metadata = PngInfo()
    metadata.add_text("Comment", "Created by AI using Google Imagen 4.0 via Mochi-Gallery")
    metadata.add_text("Software", "Mochi-Gallery v0.1")
    metadata.add_text("Haiku", haiku)
    metadata.add_text("Block", str(block_num_int))
    if style_data:
        metadata.add_text("Style", style_data.get("style_name", "Custom"))
    
    img.save(safe_raw_path, pnginfo=metadata)

    # Design & Render
    design = get_design_directives(client, img, haiku)
    poster = render_poster(img, haiku, block_num_int, design)
    
    # Save Poster (Safe)
    poster_filename = f"{file_prefix}block_{block_num_int}.png"
    safe_out_path = get_unique_filepath(args.output, poster_filename)
    
    poster.save(safe_out_path, pnginfo=metadata)
    print(f"Saved: {safe_out_path}")

if __name__ == "__main__":
    main()
