# Mochimo Gallery Generator

**Mochimo Gallery** is a CLI tool that turns [Mochimo Blockchain](https://mochimo.org/) blocks into bespoke, AI-generated posters.

It fetches the unique "Haiku" (nonce) from a specific block, uses **Google Gemini 2.0** to act as an Art Director to interpret the mood, and uses **Google Imagen 4.0** to render a high-fidelity illustration. Finally, it uses a holistic design engine to artistically overlay the text based on the image's composition.

## ⚠️ Prerequisites: Google API Setup

To use this tool, you must have a Google Cloud account with billing enabled. **Image generation via the API (Imagen 4) is a paid feature** (Pay-as-you-go), though the cost is generally low per image.

### 1. Get Your API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API key** (top left) -> **Create API key**.
3. Save this string; you will need it later.

### 2. Enable "Tier 1" Pay-as-you-go
The free tier does not allow access to `imagen-4.0-generate`. You must upgrade to the paid plan.

1. Go to the [Google Cloud Console Billing Page](https://console.cloud.google.com/billing).
2. Select the project associated with your API Key (usually named "Generative Language Client" or "My Project").
3. Click **Link a Billing Account** and add a valid credit card.
   - *Note: This enables the "Blaze" or "Pay-as-you-go" plan.*
   - *Cost:* Pricing varies, but is typically ~$0.03 - $0.06 per high-quality image generation.

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/mochi-gallery.git
cd mochi-gallery
```

### 2. Set up the Environment
It is recommended to use a virtual environment to keep dependencies clean.

```bash
# Create venv
python3 -m venv .venv

# Activate venv (Linux/Mac)
source .venv/bin/activate

# Activate venv (Windows)
# .venv\Scripts\activate
```

### 3. Install Dependencies
Install the package in "editable" mode so you can run the `mochi-gallery` command globally.

```bash
pip install -e .
```

### 4. Configuration (.env)
Create a file named `.env` in the root of the project to store your API key securely.

```bash
touch .env
```

Open `.env` and add your key:
```ini
GEMINI_API_KEY="AIzaSy...YourKeyHere"
```

### 5. Install Fonts (Critical for "Vibes")
The tool uses a "Holistic Vibe" engine that picks fonts based on the mood of the Haiku (e.g., Handwritten, Typewriter, Serif). If you do not install fonts, it will fall back to a generic default.

We recommend downloading these open-source fonts into `assets/fonts/`:

```bash
# From the project root
cd assets/fonts

# Handwritten (Nature/Ghibli/VanGogh)
wget -O handwritten_caveat.ttf https://github.com/google/fonts/raw/main/ofl/caveat/Caveat-Regular.ttf

# Typewriter (Glitch/Quantum/Giger)
wget -O typewriter_roboto.ttf https://github.com/google/fonts/raw/main/apache/robotomono/RobotoMono-Regular.ttf

# Serif (Ansel Adams/Classic)
wget -O serif_playfair.ttf https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay-Regular.ttf

# Sans (Modern/Cinematic)
wget -O sans_oswald.ttf https://github.com/google/fonts/raw/main/ofl/oswald/Oswald-Regular.ttf

cd ../..
```

---

## Usage

### Basic Command
Generate a poster for a specific block number using the AI's default artistic judgment.

```bash
mochi-gallery 880030
```
*The result will be saved in `output/block_880030.png`.*

### Using Art Styles
You can force a specific artistic style using JSON definition files located in `assets/styles/`.

**Ghibli Style:**
```bash
mochi-gallery 880030 --style assets/styles/ghibli.json
```

**Ansel Adams Style:**
```bash
mochi-gallery 880030 --style assets/styles/ansel.json
```

### Mock Mode (Free Testing)
If you want to test the text overlay logic, directory structure, or font selection **without** hitting your Google API quota (or spending money), use `--mock`.

```bash
mochi-gallery 880030 --style assets/styles/quantum.json --mock
```
*This generates a placeholder grey image but runs the real typography and design engine.*

---

## Creating Custom Styles

You can create your own styles by adding a `.json` file to the `assets/styles/` folder.

**File Format:**
```json
{
  "style_name": "Name of Style",
  "aspect_ratio": "3:4",
  "visual_directives": "Detailed instructions for the AI art director..."
}
```

### Supported Aspect Ratios
Google Imagen 4 supports the following specific strings. Any other value will default to `3:4`.

*   `"1:1"` (Square)
*   `"3:4"` (Portrait Poster - *Default*)
*   `"4:3"` (Landscape TV)
*   `"9:16"` (Mobile Vertical)
*   `"16:9"` (Cinematic Widescreen)

### Example: `cyberpunk.json`
```json
{
  "style_name": "Neon Cyberpunk",
  "aspect_ratio": "16:9",
  "visual_directives": "Blade Runner aesthetic, neon rain, bustling futuristic city, dark damp streets with bright neon signs reflecting in puddles. High contrast, teal and magenta color palette."
}
```

## Troubleshooting

**Error: 429 RESOURCE_EXHAUSTED**
*   This means you have hit your daily image generation limit (currently ~70 images/day for Tier 1).
*   **Solution:** Use `--mock` to keep working on code/layout, or wait 24 hours.

**Error: 404 NOT_FOUND (Model not found)**
*   This usually means you are on the Free Tier, or your API Key project does not have Billing enabled. Refer to the "Prerequisites" section.
