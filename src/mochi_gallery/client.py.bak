import os
import sys
import requests
import io
from PIL import Image
from google import genai
from google.genai import types
from .models import DesignDirectives
from dotenv import load_dotenv

load_dotenv()

MOCHISAN_API_URL = "https://dev-api.mochiscan.org:8443/block"
    
# OLD
# TEXT_MODEL = "gemini-2.0-flash"

# NEW - Use the stable 1.5 Flash model
TEXT_MODEL = "gemini-2.5-flash"

# Model Short-name Mapping
MODEL_MAP = {
    "fast": "imagen-4.0-fast-generate-001",
    "standard": "imagen-4.0-generate-001",
    "ultra": "imagen-4.0-ultra-generate-001"
}

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment or .env file.")
        sys.exit(1)
    return genai.Client(api_key=api_key)

def fetch_haiku(block_number: int) -> str:
    payload = {
        "network_identifier": {"blockchain": "mochimo", "network": "mainnet"},
        "block_identifier": {"index": block_number, "hash": ""},
    }
    try:
        resp = requests.post(MOCHISAN_API_URL, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        meta = data.get("block", {}).get("metadata", {})
        return meta.get("haiku", "")
    except Exception as e:
        print(f"Error fetching block data: {e}")
        return ""

def generate_image_prompt(client, haiku: str, style_data: dict = None, aspect_ratio: str = "3:4") -> str:
    print(f"1. Dreaming up the scene...")
    style_instruction = "You are a visual art director. Create a SINGLE, detailed text-to-image prompt."
    
    if style_data:
        style_name = style_data.get("style_name", "Custom Style")
        directives = style_data.get("visual_directives", "")
        print(f"   > Enforcing Style: {style_name}")
        style_instruction += (
            f"\n\nIMPORTANT: The user has strictly requested the following art style:\n"
            f"STYLE NAME: {style_name}\n"
            f"DIRECTIVES: {directives}\n"
        )
    
    prompt_text = (
        f"{style_instruction}\n\n"
        f"The image aspect ratio will be {aspect_ratio}.\n"
        "Rules: NO TEXT in image. Composition is critical (Subject vs Negative Space).\n"
        f"Haiku:\n{haiku}"
    )
    
    try:
        response = client.models.generate_content(model=TEXT_MODEL, contents=prompt_text)
        return response.text.strip()
    except Exception as e:
        sys.exit(f"Error generating prompt: {e}")

def generate_image_native(client, prompt: str, aspect_ratio: str = "3:4", model_alias: str = "standard", mock: bool = False) -> Image.Image:
    # Resolve short name to full ID
    full_model_name = MODEL_MAP.get(model_alias, MODEL_MAP["standard"])

    if mock:
        print(f"   [MOCK] Bypassing {full_model_name}...")
        w, h = 768, 1024
        if aspect_ratio == "1:1": w, h = 1024, 1024
        elif aspect_ratio == "16:9": w, h = 1024, 576
        img = Image.new('RGB', (w, h), color=(50, 50, 60))
        return img.convert("RGBA")

    print(f"2. Painting ({aspect_ratio}) using {model_alias}...")
    try:
        response = client.models.generate_images(
            model=full_model_name, prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio=aspect_ratio)
        )
        return Image.open(io.BytesIO(response.generated_images[0].image.image_bytes)).convert("RGBA")
    
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            print(f"\nCRITICAL ERROR: Quota Exceeded for {full_model_name}.")
            print("Try switching models using --model [fast|standard|ultra] or use --mock.")
            sys.exit(1)
        else:
            sys.exit(f"Error painting image: {e}")

def get_design_directives(client, image: Image.Image, haiku: str) -> DesignDirectives:
    print(f"3. Analyzing composition...")
    prompt = (
        "Act as a Senior Graphic Designer. I need to overlay this Haiku on the image:\n"
        f"'{haiku}'\n"
        "Identify visual weight and negative space. Return JSON plan."
    )
    try:
        response = client.models.generate_content(
            model=TEXT_MODEL, contents=[prompt, image],
            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=DesignDirectives)
        )
        return response.parsed
    except Exception as e:
        print(f"Design AI failed ({e}), using defaults.")
        return DesignDirectives(
            composition_analysis="Error", text_color_hex="#FFFFFF", 
            shadow_color_hex="#000000", shadow_strength=180, 
            y_position_percent=50, font_vibe="serif"
        )
