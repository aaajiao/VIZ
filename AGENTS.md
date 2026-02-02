# viz - Market & Art ASCII Visualization Toolkit

**Generated:** 2026-02-02 | **Commit:** 332ef40 | **Branch:** main

ASCII art visualization system for market data, art news, and mood tracking. Produces Instagram-ready 1080x1080 PNG/GIF images with kaomoji, glitch effects, and emotional color schemes.

## Tech Stack

- **Language**: Python 3 (no type hints)
- **Core**: Pillow (PIL) for image generation
- **Internal**: `procedural/` engine for dynamic backgrounds
- **External**: `/workspace/scripts/perplexity-search.sh` (optional, news fetching)

## Structure

```
viz/
├── universal_viz_system.py    # MAIN ENTRY - multi-type visualization
├── market_viz_complete.py     # Market-specific with sentiment analysis
├── emotional_market_viz.py    # Emotion-driven (5 moods)
├── stock_pixel_ascii.py       # Image-to-ASCII converter
├── procedural/                # Procedural generation engine (see procedural/AGENTS.md)
│   ├── engine.py              # Core orchestrator
│   ├── layers.py              # Sprite animation system
│   ├── effects/               # Effect implementations (plasma, flame, wave, etc.)
│   └── core/                  # Math primitives (Vec2, noise, SDF)
├── lib/                       # Local utilities
│   ├── kaomoji.py             # ASCII face rendering
│   └── effects.py             # Glow, glitch, particles
└── archive/                   # Deprecated (reference only)
```

## Commands

```bash
# Recommended entry point
python3 viz/universal_viz_system.py <type> [query]
# Types: market, art, mood, news

# Examples
python3 viz/universal_viz_system.py market
python3 viz/universal_viz_system.py art "Venice Biennale"
python3 viz/universal_viz_system.py mood --video --effect flame

# Market-specific
python3 viz/market_viz_complete.py "US stock market today"

# Emotional market (test moods)
python3 viz/emotional_market_viz.py euphoria
python3 viz/emotional_market_viz.py panic --video
```

## CLI Standard

All scripts use `argparse`:

| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `type`/`query` | positional | required | Visualization type or search query |
| `--video` | flag | false | Output GIF instead of PNG |
| `--effect` | string | plasma | Background effect |
| `--duration` | float | 5.0 | Video duration (seconds) |
| `--fps` | int | 30 | Frames per second |
| `--seed` | int | random | Reproducibility seed |

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new viz type | `universal_viz_system.py` | Add to `CONTENT_TYPES` dict |
| New background effect | `procedural/effects/` | Implement Effect protocol |
| Change color scheme | Module-level `COLOR_SCHEMES` dict | Per-file config |
| Sentiment logic | `analyze_sentiment()` | Keyword counting |
| Kaomoji faces | `lib/kaomoji.py` | `ASCII_KAOMOJI` dict |
| Video rendering | `procedural/engine.py` | `Engine.render_video()` |
| Post-processing | `lib/effects.py` | `draw_glow_text`, `apply_glitch` |

## CONVENTIONS

### Imports (strict order)
```python
import math, random, re, subprocess, sys
from datetime import datetime

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from lib.kaomoji import draw_kaomoji  # local
```

### Naming
| Element | Style | Example |
|---------|-------|---------|
| Constants | SCREAMING_SNAKE | `COLOR_SCHEMES`, `ASCII_GRADIENT` |
| Functions | snake_case | `draw_glow_text`, `analyze_sentiment` |
| Dict keys | snake_case strings | `'colors_bull'`, `'key_info'` |

### Docstrings (bilingual)
```python
def generate_viz(market_data, output_path):
    """
    生成可视化 - Generate visualization
    
    market_data = {
        'emotion': 'euphoria' | 'excitement' | 'anxiety' | 'fear' | 'panic',
        'headline': '标题',
        'metrics': ['指标1', '指标2'],
    }
    """
```

### Output Paths
**ALWAYS** absolute + timestamp:
```python
output_path = f'/workspace/media/{type}_viz_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
```

### Post-Processing (REQUIRED)
```python
img = img.filter(ImageFilter.SHARPEN)
img = ImageEnhance.Contrast(img).enhance(1.4)
img.save(output_path, 'PNG', quality=95)
```

## ANTI-PATTERNS

### FORBIDDEN
- ❌ Type hints (not used in this codebase)
- ❌ MP4 output (GIF only, no FFmpeg dependency)
- ❌ NumPy dependency (pure Python math)
- ❌ High-res internal compute (use 160×160 → upscale to 1080×1080)
- ❌ Relative output paths

### ALLOWED ONLY FOR PIXELS
```python
# Bare except ONLY for pixel manipulation
try:
    pixels[x + i, y] = pixels[x + i, (y + shift) % HEIGHT]
except:
    pass  # Out-of-bounds ok here
```

### SUBPROCESS
```python
# ALWAYS check return code
result = subprocess.run([...], capture_output=True, text=True, timeout=30)
return result.stdout if result.returncode == 0 else None
```

## Key Patterns

### Sentiment Analysis (keyword counting)
```python
bull_words = ['up', 'gain', 'rise', 'rally', 'surge', 'bull', 'positive']
bear_words = ['down', 'fall', 'drop', 'decline', 'crash', 'bear', 'negative']
# Bull if bull_count > bear_count + 2, else similar for bear, else neutral
```

### Glitch Effect (extreme emotions only)
```python
if emotion in ['euphoria', 'panic']:
    apply_glitch(img, intensity=150)  # Only for these moods
```

### Canvas Setup
```python
WIDTH, HEIGHT = 1080, 1080  # Instagram square
img = Image.new('RGB', (WIDTH, HEIGHT), colors['bg'])
draw = ImageDraw.Draw(img)
```

## Dependencies

```
Pillow>=9.0.0
requests  # Only for stock_pixel_ascii.py
```

## Output

- **Format**: PNG (quality=95) or GIF
- **Size**: 1080×1080 pixels
- **Location**: `/workspace/media/`

## Notes

- No build system, linter, or test suite (script-based project)
- Each `.py` file is standalone executable
- `archive/poc_playcore.py` is DEPRECATED - use `procedural/` instead
- External `/workspace/scripts/perplexity-search.sh` is optional for news fetching
