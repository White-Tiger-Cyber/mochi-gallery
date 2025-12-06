# Mochimo Gallery Generator

**Mochimo Gallery** is a CLI tool that turns [Mochimo Blockchain](https://mochimo.org/) blocks into bespoke, AI-generated posters.

It fetches the unique "Haiku" (nonce) from a specific block, uses **Google Gemini 2.0** as an Art Director to interpret the mood, and uses **Google Imagen 4.0** to render a high-fidelity illustration. Finally, it uses a holistic design engine to artistically overlay the text based on the image's composition.

> **Project Status:** This is an experimental creative tool. It is designed to be run locally from the cloned repository.

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

**Note:** This tool relies on local assets (`assets/styles` and `assets/fonts`). You must clone the repository and run it from within the directory.

### 1. Clone the Repository
```bash
git clone https://github.com/White-Tiger-Cyber/mochi-gallery.git
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
The tool uses a "Holistic Vibe" engine that picks fonts based on the mood of the Haiku. If you do not install fonts, it will fall back to a generic default.

We recommend downloading these open-source fonts into `assets/fonts/`:

```bash
# From the project root
cd assets/fonts

# Handwritten (Caveat) - Perfect for Nature/Ghibli/VanGogh
wget -O handwritten_caveat.ttf "https://github.com/google/fonts/raw/main/ofl/caveat/Caveat%5Bwght%5D.ttf"

# Typewriter (Space Mono) - Perfect for Glitch/Quantum/Giger
wget -O typewriter_roboto.ttf https://github.com/google/fonts/raw/main/ofl/spacemono/SpaceMono-Regular.ttf

# Serif (Prata) - Perfect for Ansel Adams/Classic
wget -O serif_playfair.ttf https://github.com/google/fonts/raw/main/ofl/prata/Prata-Regular.ttf

# Sans (Oswald) - Perfect for Modern/Bold/Cinematic
wget -O sans_oswald.ttf "https://github.com/google/fonts/raw/main/ofl/oswald/Oswald%5Bwght%5D.ttf"

cd ../..
```

---

## Usage

### 1. Basic Generation
Generate a poster for a specific block number using the AI's default artistic judgment (Default 3:4 Aspect Ratio).

```bash
mochi-gallery 880030
```
*The result will be saved in `output/block_880030.png`. Metadata regarding the Haiku and Generation parameters is embedded in the PNG headers.*

### 2. Listing Available Styles
To see what artistic styles are installed on your system:

```bash
mochi-gallery ?
# OR
mochi-gallery list
```

### 3. Using a Specific Style
You can use the **Short Name** (the filename without `.json`) or the full path.

```bash
# Render in Studio Ghibli style
mochi-gallery 880030 --style ghibli
```

### 4. Override Aspect Ratio
You can force a specific aspect ratio on the fly using `--ar`. This overrides any default set by the selected Style.
**Supported Ratios:** `1:1`, `3:4`, `4:3`, `9:16`, `16:9`.

```bash
# Force a Cinematic Widescreen render of the Quantum style
mochi-gallery 880030 --style quantum --ar 16:9
```

### 5. Switching Models (Speed vs Quality)
You can switch between three Google Imagen models using the `--model` flag. This is useful for saving money during testing or getting maximum quality for final prints.

*   `fast`: **Imagen 4 Fast**. Lowest latency, lower cost. Great for iteration.
*   `standard`: **Imagen 4**. (Default). Good balance of quality and quota.
*   `ultra`: **Imagen 4 Ultra**. Highest fidelity and lighting, but strict daily limits (~30/day).

```bash
# Quick test
mochi-gallery 880030 --model fast

# Masterpiece render
mochi-gallery 880030 --style ansel --model ultra
```

### 6. Mock Mode (Free Testing)
If you want to test the text overlay logic, directory structure, or font selection **without** hitting your Google API quota (or spending money), use `--mock`.

```bash
mochi-gallery 880030 --style quantum --mock
```
*This generates a placeholder grey image but runs the real typography and design engine.*

---

## Creating Custom Styles

You can create your own styles by adding a `.json` file to the `assets/styles/` folder. The filename becomes the "Short Name".

**File Format:**
```json
{
  "style_name": "Name of Style",
  "aspect_ratio": "3:4",
  "visual_directives": "Detailed instructions for the AI art director..."
}
```

## Troubleshooting

**Error: 429 RESOURCE_EXHAUSTED**
*   This means you have hit your daily image generation limit.
*   **Solution:** Switch models! If `standard` is out, try `--model fast`. Or use `--mock` to keep working on layout logic.

**Error: 404 NOT_FOUND (Model not found)**
*   This usually means you are on the Free Tier, or your API Key project does not have Billing enabled. Refer to the "Prerequisites" section.

## License
MIT License. See [LICENSE](LICENSE) file for details.
