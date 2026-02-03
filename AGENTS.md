# viz - ASCII Art Visualization Toolkit

ASCII art visualization for market data, art news, and mood tracking. Produces 1080x1080 PNG/GIF images with kaomoji, glitch effects, and emotional color schemes.

## Quick Reference

| Command | Description |
|---------|-------------|
| `python3 viz/universal_viz_system.py market` | Market visualization |
| `python3 viz/universal_viz_system.py art "query"` | Art news visualization |
| `python3 viz/universal_viz_system.py mood --video` | Mood viz as GIF |
| `python3 viz/emotional_market_viz.py euphoria` | Test specific emotion |

**No build/lint/test system.** Scripts are standalone executables. No unit tests exist.

## Project Structure

```
viz/
├── universal_viz_system.py    # MAIN ENTRY - CLI for all viz types
├── market_viz_complete.py     # Market-specific with sentiment analysis
├── emotional_market_viz.py    # Emotion-driven (5 moods)
├── stock_pixel_ascii.py       # Image-to-ASCII converter
├── procedural/                # Rendering engine (see procedural/AGENTS.md)
│   ├── engine.py              # Orchestrator: render_frame, render_video
│   ├── types.py               # Context, Cell, Buffer, Effect protocol
│   ├── effects/               # Pluggable effects (plasma, flame, wave...)
│   └── core/                  # Math primitives (vec, sdf, noise)
├── lib/                       # Utilities
│   ├── kaomoji.py             # draw_kaomoji(), mood categories
│   ├── kaomoji_data.py        # Single-line kaomoji data
│   └── effects.py             # draw_glow_text, apply_glitch
└── archive/                   # DEPRECATED - reference only
```

## Code Style

### Imports (strict order, grouped by blank lines)
```python
import argparse
import math, random, re, subprocess, sys
from datetime import datetime

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from lib.kaomoji import draw_kaomoji  # local imports last
from procedural.engine import Engine
```

### Naming Conventions
| Element | Style | Example |
|---------|-------|---------|
| Constants | SCREAMING_SNAKE | `COLOR_SCHEMES`, `ASCII_GRADIENT`, `WIDTH` |
| Functions | snake_case | `draw_glow_text`, `analyze_sentiment` |
| Classes | PascalCase | `Engine`, `BaseEffect`, `PlasmaEffect` |
| Dict keys | snake_case strings | `'colors_bull'`, `'key_info'` |

### Docstrings (bilingual Chinese/English pattern)
```python
def generate_viz(market_data, output_path):
    """
    生成可视化 - Generate visualization
    
    Args:
        market_data: dict with 'emotion', 'headline', 'metrics'
        output_path: absolute path for output
    """
```

### Type Annotations
- **Avoid in most files** - codebase doesn't use type hints
- **Exception**: `procedural/types.py` uses dataclasses + Protocol for core types
- Never add type hints to existing untyped code

### Output Paths (ALWAYS absolute + timestamp)
```python
output_path = f'/workspace/media/{type}_viz_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
```

## Error Handling

### Subprocess calls - check return code
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

### Font loading - always provide fallback
```python
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size)
except:
    font = ImageFont.load_default()
```

## FORBIDDEN (Anti-Patterns)

- **Type hints** - not used (except procedural/types.py)
- **NumPy** - pure Python math only
- **MP4 output** - GIF only, no FFmpeg dependency
- **High-res compute** - use 160x160 internally, upscale to 1080x1080
- **Relative output paths** - always `/workspace/media/...`
- **Empty catch blocks** - except for pixel manipulation

## Key Patterns

### Canvas Setup (all visualizers)
```python
WIDTH, HEIGHT = 1080, 1080  # Instagram square
img = Image.new('RGB', (WIDTH, HEIGHT), colors['bg'])
draw = ImageDraw.Draw(img)
```

### Post-Processing (REQUIRED for final images)
```python
img = img.filter(ImageFilter.SHARPEN)
img = ImageEnhance.Contrast(img).enhance(1.4)
img.save(output_path, 'PNG', quality=95)
```

### Sentiment Analysis (keyword counting)
```python
bull_words = ['up', 'gain', 'rise', 'rally', 'surge', 'bull', 'positive']
bear_words = ['down', 'fall', 'drop', 'decline', 'crash', 'bear', 'negative']
# Bull if bull_count > bear_count + 2
```

### Effect Protocol (procedural/effects/)
```python
class MyEffect:
    def pre(self, ctx, buffer):
        """Initialize state. Return dict."""
        return {'param': ctx.params.get('param', 1.0)}
    
    def main(self, x, y, ctx, state):
        """Per-pixel. Return Cell(char_idx, fg, bg)."""
        return Cell(char_idx=int(value*9), fg=color, bg=None)
    
    def post(self, ctx, buffer, state):
        """Global modifications. Optional."""
        pass
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add new viz type | `universal_viz_system.py` -> `CONTENT_TYPES` dict |
| New background effect | `procedural/effects/` + register in `__init__.py` |
| Change color scheme | Module-level `COLOR_SCHEMES` dict |
| Sentiment logic | `analyze_sentiment()` function |
| Kaomoji faces | `lib/kaomoji.py` -> `ASCII_KAOMOJI` dict |
| Video rendering | `procedural/engine.py` -> `Engine.render_video()` |
| Post-processing effects | `lib/effects.py` -> `draw_glow_text`, `apply_glitch` |
| Math primitives | `procedural/core/` -> vec, sdf, noise, mathx |

## CLI Arguments (argparse - all main scripts)

| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `type`/`query` | positional | required | Viz type or search query |
| `--video` | flag | false | Output GIF instead of PNG |
| `--effect` | string | plasma | Background effect |
| `--duration` | float | 5.0 | Video duration (seconds) |
| `--fps` | int | 30 | Frames per second |
| `--seed` | int | random | Reproducibility seed |

## Dependencies

```
Pillow>=9.0.0
requests  # Only for stock_pixel_ascii.py (optional)
```

## Output

- **Format**: PNG (quality=95) or GIF
- **Size**: 1080x1080 pixels
- **Location**: `/workspace/media/`

## Notes

- Each `.py` is standalone executable with `if __name__ == "__main__":`
- `archive/` is DEPRECATED - use `procedural/` instead
- External `/workspace/scripts/perplexity-search.sh` is optional for news fetch
- See `procedural/AGENTS.md` for rendering engine details
