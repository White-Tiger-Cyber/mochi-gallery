# Mochimo Gallery Generator

**Mochimo Gallery** is a CLI tool that turns [Mochimo Blockchain](https://mochimo.org/) blocks into bespoke, AI-generated posters.

It fetches the unique "Haiku" (nonce) from a specific block, uses **Google Gemini** as an Art Director to interpret the mood, and uses **Google Imagen** to render a high-fidelity illustration. Finally, it uses a holistic design engine to artistically overlay the text based on the image's composition.

> **Project Status:** This is an experimental creative tool. It is designed to be run locally from the cloned repository.

## 🌟 New Features (v0.2)
* **Style Alchemy:** Mix multiple styles together (e.g., `ghibli+steampunk`) to create unique hybrid aesthetics.
* **Batch Mode:** Generate entire collections at once using ranges (`880000-880050`) or lists (`880000,880005`).
* **Smart Recovery:** If a block fails in a batch, the tool skips it and keeps working.

## ⚠️ Prerequisites: Google API Setup

To use this tool, you must have a Google Cloud account with billing enabled. **Image generation via the API (Imagen 4) is a paid feature** (Pay-as-you-go), though the cost is generally low per image.

### 1. Get Your API Key
1.  Go to [Google AI Studio](https://aistudio.google.com/).
2.  Click **Get API key** (top left) -> **Create API key**.
3.  Save this string; you will need it later.

### 2. Enable "Tier 1" Pay-as-you-go
The free tier does not allow access to `imagen-4.0-generate`. You must upgrade to the paid plan.

1.  Go to the [Google Cloud Console Billing Page](https://console.cloud.google.com/billing).
2.  Select the project associated with your API Key.
3.  Click **Link a Billing Account** and add a valid credit card.

## Installation

**Note:** This tool relies on local assets (`assets/styles` and `assets/fonts`). You must clone the repository and run it from within the directory.

### 1. Clone the Repository
```bash
git clone [https://github.com/White-Tiger-Cyber/mochi-gallery.git](https://github.com/White-Tiger-Cyber/mochi-gallery.git)
cd mochi-gallery
```

### 2. Set up the Environment
It is recommended to use a virtual environment to keep dependencies clean.

```bash
# Create venv
python3 -m venv .venv

# Activate venv (Linux/Mac)
source .venv/bin/activate
# Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
Install the package in "editable" mode so you can run the `mochi-gallery` command globally.

```bash
pip install -e .
```

### 4. Configuration (API Key)
Export your key to your environment variables:

```bash
export GEMINI_API_KEY="AIzaSy...YourKeyHere"
```

### 5. Install Fonts (Critical for "Vibes")
The tool uses a "Holistic Vibe" engine that picks fonts based on the mood of the Haiku. If you do not install fonts, it will fall back to a generic default.

We recommend downloading these open-source fonts into `assets/fonts/`:

```bash
# From the project root
cd assets/fonts

# Handwritten (Caveat) - Perfect for Nature/Ghibli/VanGogh
wget -O handwritten_caveat.ttf "[https://github.com/google/fonts/raw/main/ofl/caveat/Caveat%5Bwght%5D.ttf](https://github.com/google/fonts/raw/main/ofl/caveat/Caveat%5Bwght%5D.ttf)"

# Typewriter (Space Mono) - Perfect for Glitch/Quantum/Giger
wget -O typewriter_roboto.ttf [https://github.com/google/fonts/raw/main/ofl/spacemono/SpaceMono-Regular.ttf](https://github.com/google/fonts/raw/main/ofl/spacemono/SpaceMono-Regular.ttf)

# Serif (Prata) - Perfect for Ansel Adams/Classic
wget -O serif_playfair.ttf [https://github.com/google/fonts/raw/main/ofl/prata/Prata-Regular.ttf](https://github.com/google/fonts/raw/main/ofl/prata/Prata-Regular.ttf)

# Sans (Oswald) - Perfect for Modern/Bold/Cinematic
wget -O sans_oswald.ttf "[https://github.com/google/fonts/raw/main/ofl/oswald/Oswald%5Bwght%5D.ttf](https://github.com/google/fonts/raw/main/ofl/oswald/Oswald%5Bwght%5D.ttf)"

cd ../..
```

---

## Usage

### 1. Basic Generation
Generate a poster for a specific block number using the AI's default artistic judgment.
```bash
mochi-gallery 880030
```

### 2. Batch Processing (Create a Collection)
You can now process multiple blocks in one go.
```bash
# Generate a range of 10 blocks
mochi-gallery 884000-884010

# Generate specific blocks
mochi-gallery 884000,884005,884022
```

### 3. Style Alchemy (Mixing Vibes)
Combine styles to create something new. The AI "Art Director" will merge the visual directives of all selected styles.
```bash
# Mix Studio Ghibli with Steampunk
mochi-gallery 880030 --style ghibli+steampunk

# The "Mega Mix"
mochi-gallery 880030 --style cyberpunk+ansel+picasso
```

### 4. Listing Available Styles
To see what artistic styles are installed on your system:
```bash
mochi-gallery list
```

### 5. Override Aspect Ratio
Force a specific aspect ratio on the fly using `--ar`. Supported: `1:1`, `3:4`, `4:3`, `9:16`, `16:9`.
```bash
mochi-gallery 880030 --style quantum --ar 16:9
```

### 6. Switching Models (Speed vs Quality)
You can fine-tune both the **Painter** (Imagen) and the **Art Director** (Gemini).

**Image Models (`--model`):**
* `fast`: **Imagen 4 Fast**. Lowest latency, lower cost.
* `standard`: **Imagen 4**. (Default). Good balance.
* `ultra`: **Imagen 4 Ultra**. Highest fidelity and lighting.

**Text Models (`--text-model`):**
* `gemini-2.5-flash`: Fast, reliable workhorse (Default).
* `gemini-3-pro-preview`: The smartest model for nuanced art direction.
* `gemini-2.0-flash-thinking-exp`: Great for abstract/weird haikus.

```bash
# Masterpiece render
mochi-gallery 880030 --style ansel --model ultra --text-model gemini-3-pro-preview
```

### 7. Mock Mode (Free Testing)
Test the text overlay logic and font selection **without** hitting your Google API quota.
```bash
mochi-gallery 880030 --style quantum --mock
```

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

## Troubleshooting

**Error: 429 RESOURCE_EXHAUSTED**
* This means you have hit your daily image generation limit.
* **Solution:** Switch models! If `standard` is out, try `--model fast`. Or use `--mock` to keep working on layout logic.

**Error: 404 NOT_FOUND (Model not found)**
* This usually means you are on the Free Tier, or your API Key project does not have Billing enabled. Refer to the "Prerequisites" section.
* It may also mean you selected a `--text-model` that isn't available in your region.

## License
MIT License.
