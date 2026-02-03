# viz - ASCII Art Visualization Toolkit

ASCII art visualization for market data, art news, and mood tracking. Produces 1080×1080 PNG/GIF images with kaomoji, glitch effects, and emotional color schemes.

## Quick Reference

| Command | Description |
|---------|-------------|
| `python3 viz/universal_viz_system.py market` | Market visualization |
| `python3 viz/universal_viz_system.py art "query"` | Art news visualization |
| `python3 viz/universal_viz_system.py mood --video` | Mood viz as GIF |
| `python3 viz/emotional_market_viz.py euphoria` | Test specific emotion |

**No build/lint/test system.** Scripts are standalone executables.

## Structure

```
viz/
├── universal_viz_system.py    # MAIN ENTRY - multi-type visualization
├── market_viz_complete.py     # Market-specific with sentiment analysis
├── emotional_market_viz.py    # Emotion-driven (5 moods)
├── stock_pixel_ascii.py       # Image-to-ASCII converter
├── procedural/                # Rendering engine (see procedural/AGENTS.md)
├── lib/                       # Utilities (kaomoji.py, effects.py)
└── archive/                   # Deprecated (reference only)
```

## CLI Arguments (all scripts use argparse)

| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `type`/`query` | positional | required | Viz type or search query |
| `--video` | flag | false | Output GIF instead of PNG |
| `--effect` | string | plasma | Background effect |
| `--duration` | float | 5.0 | Video duration (seconds) |
| `--fps` | int | 30 | Frames per second |
| `--seed` | int | random | Reproducibility seed |

## Code Style

### Imports (strict order)
```python
import math, random, re, subprocess, sys
from datetime import datetime

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from lib.kaomoji import draw_kaomoji  # local imports last
```

### Naming
| Element | Style | Example |
|---------|-------|---------|
| Constants | SCREAMING_SNAKE | `COLOR_SCHEMES`, `ASCII_GRADIENT` |
| Functions | snake_case | `draw_glow_text`, `analyze_sentiment` |
| Classes | PascalCase | `Engine`, `BaseEffect` |
| Dict keys | snake_case strings | `'colors_bull'`, `'key_info'` |

### Docstrings (bilingual Chinese/English)
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

### Output Paths (ALWAYS absolute + timestamp)
```python
output_path = f'/workspace/media/{type}_viz_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
```

### Post-Processing (REQUIRED for all final images)
```python
img = img.filter(ImageFilter.SHARPEN)
img = ImageEnhance.Contrast(img).enhance(1.4)
img.save(output_path, 'PNG', quality=95)
```

## Error Handling

### Subprocess calls - ALWAYS check return code
```python
result = subprocess.run([...], capture_output=True, text=True, timeout=30)
return result.stdout if result.returncode == 0 else None
```

### Pixel manipulation - bare except ONLY here
```python
try:
    pixels[x + i, y] = pixels[x + i, (y + shift) % HEIGHT]
except:
    pass  # Out-of-bounds ok for glitch effects
```

### Optional imports - handle gracefully
```python
try:
    from lib.kaomoji import draw_kaomoji
except ImportError:
    from viz.lib.kaomoji import draw_kaomoji
```

## FORBIDDEN (Anti-Patterns)

- ❌ **Type hints** - not used in this codebase
- ❌ **NumPy** - pure Python math only
- ❌ **MP4 output** - GIF only, no FFmpeg dependency
- ❌ **High-res compute** - use 160×160 internally, upscale to 1080×1080
- ❌ **Relative output paths** - always absolute `/workspace/media/...`
- ❌ **Empty catch blocks** - except for pixel manipulation (see above)

## Key Patterns

### Canvas Setup
```python
WIDTH, HEIGHT = 1080, 1080  # Instagram square
img = Image.new('RGB', (WIDTH, HEIGHT), colors['bg'])
draw = ImageDraw.Draw(img)
```

### Sentiment Analysis (keyword counting)
```python
bull_words = ['up', 'gain', 'rise', 'rally', 'surge', 'bull', 'positive']
bear_words = ['down', 'fall', 'drop', 'decline', 'crash', 'bear', 'negative']
# Bull if bull_count > bear_count + 2, else similar logic for bear, else neutral
```

### Glitch Effect (extreme emotions only)
```python
if emotion in ['euphoria', 'panic']:
    apply_glitch(img, intensity=150)  # Only for extreme moods
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add new viz type | `universal_viz_system.py` → `CONTENT_TYPES` dict |
| New background effect | `procedural/effects/` → implement Effect protocol |
| Change color scheme | Module-level `COLOR_SCHEMES` dict |
| Sentiment logic | `analyze_sentiment()` function |
| Kaomoji faces | `lib/kaomoji.py` → `ASCII_KAOMOJI` dict |
| Kaomoji data (single-line) | `lib/kaomoji_data.py` → `KAOMOJI_DATA` dict |
| Video rendering | `procedural/engine.py` → `Engine.render_video()` |
| Post-processing | `lib/effects.py` → `draw_glow_text`, `apply_glitch` |
| Dynamic layouts | `procedural/layouts.py` → layout algorithms |
| Effect blending | `procedural/compositor.py` → composite effects |

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

- Each `.py` file is standalone executable
- `archive/poc_playcore.py` is DEPRECATED - use `procedural/` instead
- External `/workspace/scripts/perplexity-search.sh` is optional for news
- See `procedural/AGENTS.md` for rendering engine details
