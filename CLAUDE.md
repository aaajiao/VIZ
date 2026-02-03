# CLAUDE.md - AI Assistant Guide for VIZ

ASCII art visualization toolkit producing 1080x1080 PNG/GIF images with kaomoji, procedural effects, and emotion-driven visual styles. Pure Python 3 + Pillow, no build system.

## Quick Commands

```bash
# Generate visualization (pure visual, emotion-driven)
python3 viz.py generate --emotion euphoria --seed 42

# Generate with content data via stdin JSON (AI integration)
echo '{"source":"market","headline":"DOW +600","emotion":"bull","metrics":["BTC: $92k"]}' | python3 viz.py generate

# Generate with CLI args
python3 viz.py generate --emotion panic --title "CRASH" --source market --video

# Convert image to ASCII art
python3 viz.py convert image.png --charset blocks --emotion bull

# Query capabilities (for AI discovery)
python3 viz.py capabilities --format json
```

**No build, lint, test, or CI/CD system exists.** `viz.py` is the single CLI entry point. Old scripts moved to `archive/`. There are no unit tests.

## Architecture

**viz.py** is the unified CLI with 3 commands:
- `generate` - Generates 1080x1080 PNG/GIF visualizations. Accepts emotion/VAD + optional content data (headline, metrics, timestamp). AI passes data via stdin JSON or CLI args.
- `convert` - Converts images to ASCII art (wraps `stock_pixel_ascii.py`).
- `capabilities` - Outputs JSON schema for AI discovery (emotions, effects, sources, etc.).

**FlexiblePipeline** (in `procedural/flexible/pipeline.py`) now accepts optional `content` dict with:
- `headline`, `metrics`, `timestamp`, `body` - text content to render
- `source` - determines visual vocabulary (market, art, news, mood)
- `vocabulary` - visual elements (kaomoji, decorations, gradients)

**Content flow**: AI analyzes user request -> constructs JSON with emotion + content data -> pipes to `viz.py generate` -> VIZ renders -> outputs path JSON.

## Project Structure

```
VIZ/
├── viz.py                        # Single CLI entry point (generate, convert, capabilities)
├── stock_pixel_ascii.py          # Image-to-ASCII converter (called by viz.py convert)
│
├── lib/                          # Shared utilities
│   ├── content.py                # Content data structure maker
│   ├── vocabulary.py             # Visual vocabularies (market, art, news, mood)
│   ├── glow.py                   # Glow text effect
│   ├── ascii_texture.py          # ASCII texture utilities
│   ├── kaomoji.py                # Kaomoji rendering (20 categories, 300+ faces)
│   ├── kaomoji_data.py           # Kaomoji data (single-line + multi-line)
│   ├── box_chars.py              # Box-drawing characters (37 charsets)
│   └── effects.py                # Glitch effects, particles
│
├── procedural/                   # Rendering engine (160x160 -> 1080x1080)
│   ├── engine.py                 # Orchestrator: render_frame, render_video, save_gif
│   ├── types.py                  # Core types: Context, Cell, Buffer, Effect (Protocol)
│   ├── renderer.py               # buffer_to_image(), upscale_image()
│   ├── compositor.py             # Effect blending (ADD/MULTIPLY/SCREEN/OVERLAY)
│   ├── layers.py                 # Sprites: TextSprite, KaomojiSprite, decorations
│   ├── layouts.py                # Layout algorithms (scatter, grid, spiral, force)
│   ├── params.py                 # ParamSpec, reproducible RNG
│   ├── palette.py                # 20 ASCII gradients, 5 color schemes
│   ├── effects/                  # Pluggable effects (6 built-in)
│   │   ├── __init__.py           # EFFECT_REGISTRY, get_effect()
│   │   ├── base.py               # BaseEffect (default pre/post)
│   │   ├── plasma.py             # 4-layer sine interference
│   │   ├── flame.py              # Doom-style fire propagation
│   │   ├── wave.py               # Multi-frequency sine stacking
│   │   ├── moire.py              # Radial wave multiplication
│   │   ├── sdf_shapes.py         # Smooth distance fields
│   │   └── noise_field.py        # ValueNoise + FBM
│   ├── core/                     # Math primitives (pure Python, no NumPy)
│   │   ├── vec.py                # Vec2 operations
│   │   ├── sdf.py                # Signed distance fields
│   │   ├── noise.py              # ValueNoise, fbm, turbulence
│   │   └── mathx.py              # clamp, mix, smoothstep, fract, pulse
│   └── flexible/                 # Flexible Output System (infinite variations)
│       ├── emotion.py            # VAD continuous emotion space (24 anchors)
│       ├── color_space.py        # Continuous warmth/saturation/brightness
│       ├── modulator.py          # Noise drifting + domain warping
│       ├── grammar.py            # Probabilistic visual grammar rules
│       ├── cppn.py               # CPPN neural network patterns
│       └── pipeline.py           # Orchestrator combining all modules
│
├── docs/                         # Detailed documentation
│   ├── rendering.md              # Rendering pipeline guide
│   ├── box_chars.md              # Box-drawing character system
│   ├── flexible.md               # Flexible output system
│   ├── effects.md                # Effects reference
│   ├── kaomoji.md                # Kaomoji system
│   └── usage.md                  # CLI entry points guide
│
├── archive/                      # DEPRECATED - reference only, do not modify
└── AGENTS.md                     # Project conventions (also see procedural/AGENTS.md)
```

## Dependencies

Only two external dependencies (no requirements.txt file):
- **Pillow>=9.0.0** - Image generation (required)
- **requests** - HTTP fetching (optional, only for stock_pixel_ascii.py)

All math is pure Python stdlib. NumPy is forbidden.

## Code Conventions

### Imports (strict order, blank-line separated)
```python
# 1. Standard library
import argparse
import math, random, re, subprocess, sys
from datetime import datetime

# 2. Third-party
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

# 3. Local
from lib.kaomoji import draw_kaomoji
from procedural.engine import Engine
```

Local imports use try/except for path flexibility:
```python
try:
    from lib.kaomoji import draw_kaomoji
except ImportError:
    from viz.lib.kaomoji import draw_kaomoji
```

### Naming
| Element | Style | Example |
|---------|-------|---------|
| Constants | SCREAMING_SNAKE | `COLOR_SCHEMES`, `ASCII_GRADIENT`, `WIDTH` |
| Functions | snake_case | `draw_glow_text()`, `analyze_sentiment()` |
| Classes | PascalCase | `Engine`, `BaseEffect`, `PlasmaEffect` |
| Dict keys | snake_case strings | `'colors_bull'`, `'key_info'` |

### Docstrings (bilingual Chinese/English)
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
- **Do NOT add type hints** to existing code - the codebase intentionally avoids them
- **Exception**: `procedural/types.py` uses dataclasses + Protocol for core types

## Forbidden Patterns

- **NumPy** - all math must be pure Python
- **MP4 output** - GIF only, no FFmpeg dependency
- **High-res compute** - always 160x160 internally, upscale to 1080x1080
- **Relative output paths** - always use `/workspace/media/...` with timestamps
- **Empty catch blocks** - only acceptable for pixel manipulation glitch effects
- **Type hints** - not used except in `procedural/types.py`

## Key Patterns

### Canvas Setup (all visualizers)
```python
WIDTH, HEIGHT = 1080, 1080  # Instagram square
img = Image.new('RGB', (WIDTH, HEIGHT), colors['bg'])
draw = ImageDraw.Draw(img)
```

### Output Paths (always absolute + timestamped)
```python
output_path = f'/workspace/media/{type}_viz_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
```

### Post-Processing (required for final images)
```python
img = img.filter(ImageFilter.SHARPEN)
img = ImageEnhance.Contrast(img).enhance(1.4)
img.save(output_path, 'PNG', quality=95)
```

### Font Loading (always provide fallback)
```python
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size)
except:
    font = ImageFont.load_default()
```

### Effect Protocol (procedural/effects/)
```python
class MyEffect:
    def pre(self, ctx, buffer):
        """Initialize state. Called once per frame. Return dict."""
        return {'param': ctx.params.get('param', 1.0)}

    def main(self, x, y, ctx, state):
        """Per-pixel. Return Cell(char_idx, fg, bg)."""
        return Cell(char_idx=int(value * 9), fg=color, bg=None)

    def post(self, ctx, buffer, state):
        """Global modifications. Optional."""
        pass
```

Register in `procedural/effects/__init__.py`:
```python
from .my_effect import MyEffect
EFFECT_REGISTRY['my_effect'] = MyEffect
```

## Rendering Pipeline

```
Engine creates Context + Buffer (160x160)
  -> effect.pre(ctx, buffer) -> state dict
  -> for y, x: buffer[y][x] = effect.main(x, y, ctx, state)
  -> effect.post(ctx, buffer, state)
  -> buffer_to_image() -> PIL Image (160x160)
  -> sprite.render(image, time) for each sprite
  -> upscale_image() -> 1080x1080 (NEAREST interpolation)
  -> sharpen + contrast -> final PNG/GIF
```

### Key Types (procedural/types.py)

| Type | Description |
|------|-------------|
| `Context` | width, height, time, frame, seed, rng, params |
| `Cell` | char_idx (0-9), fg (RGB tuple), bg (RGB or None) |
| `Buffer` | `list[list[Cell]]` - 2D grid |
| `Effect` | Protocol: pre/main/post methods |

Context is **immutable by convention** - never modify ctx inside an effect.

### Engine Usage
```python
from procedural import Engine
from procedural.effects import get_effect
from procedural.layers import TextSprite

engine = Engine(internal_size=(160, 160), output_size=(1080, 1080))
effect = get_effect('plasma')

# Single frame
img = engine.render_frame(effect, time=1.5, seed=42)

# GIF
frames = engine.render_video(effect, duration=3.0, fps=15, seed=42)
engine.save_gif(frames, 'output.gif', fps=15)
```

### Available Effects

| Effect | Description |
|--------|-------------|
| `plasma` | Animated sine wave interference (4-layer) |
| `flame` | Doom-style fire (heat propagation + decay) |
| `wave` | Multi-frequency sine stacking |
| `moire` | Radial interference patterns |
| `sdf_shapes` | Smooth distance field circles/boxes |
| `noise_field` | Perlin-like value noise + FBM |
| `cppn` | CPPN neural network patterns (compositional) |

### Color Schemes

`value_to_color(v, scheme)` where `v` is 0.0-1.0:

| Scheme | Gradient |
|--------|----------|
| `heat` | Black -> Red -> Orange -> Yellow -> White |
| `rainbow` | HSV hue cycle |
| `cool` | Blue -> Cyan -> White |
| `matrix` | Dark Green -> Bright Green |
| `plasma` | Multi-color with brightness pulse |

### Core Math (procedural/core/, no NumPy)

| Module | Key Functions |
|--------|---------------|
| `vec.py` | `Vec2`, `length`, `normalize`, `rotate`, `dot` |
| `sdf.py` | `sd_circle`, `sd_box`, `op_smooth_union` |
| `noise.py` | `ValueNoise`, `.fbm()`, `.turbulence()` |
| `mathx.py` | `clamp`, `mix`, `smoothstep`, `map_range` |

### Sentiment Analysis (keyword counting)
```python
bull_words = ['up', 'gain', 'rise', 'rally', 'surge', 'bull', 'positive']
bear_words = ['down', 'fall', 'drop', 'decline', 'crash', 'bear', 'negative']
# Bull if bull_count > bear_count + 2
```

## Where to Make Changes

| Task | Location |
|------|----------|
| Add new CLI command | `viz.py` -> add subparser + command function |
| Add new vocabulary source | `lib/vocabulary.py` -> `VOCABULARIES` dict |
| Add new background effect | `procedural/effects/` + register in `__init__.py` |
| Change color scheme | `procedural/palette.py` -> `COLOR_SCHEMES`, `ASCII_GRADIENTS` |
| Add kaomoji faces | `lib/kaomoji_data.py` -> `KAOMOJI_SINGLE` dict |
| Add box-drawing charset | `lib/box_chars.py` -> `CHARSETS` |
| Video/GIF rendering | `procedural/engine.py` -> `render_video()`, `save_gif()` |
| Glitch/glow effects | `lib/effects.py` -> `apply_glitch()` |
| Glow text rendering | `lib/glow.py` -> `draw_glow_text()` |
| ASCII textures | `lib/ascii_texture.py` -> texture generators |
| Content data handling | `lib/content.py` -> `make_content()` |
| Sprite animation | `procedural/layers.py` -> breathing, floating, color_cycle |
| Layout algorithms | `procedural/layouts.py` -> scatter, grid, spiral, force |
| Math primitives | `procedural/core/` -> vec, sdf, noise, mathx |
| Emotion mapping | `procedural/flexible/emotion.py` -> VAD anchors |
| Visual grammar rules | `procedural/flexible/grammar.py` |
| Content integration | `procedural/flexible/pipeline.py` -> FlexiblePipeline |

## CLI Arguments (viz.py generate)

| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `--emotion` | string | inferred | Emotion name (joy, fear, bull, bear, etc.) |
| `--source` | string | none | Content source (market, art, news, mood) |
| `--title` | string | none | Title overlay text |
| `--text` | string | none | Text for emotion inference (fallback) |
| `--headline` | string | none | Main headline text |
| `--metrics` | list | none | Metrics to display (space-separated) |
| `--vad` | string | none | Direct VAD vector (e.g., "0.8,0.9,0.7") |
| `--effect` | string | auto | Background effect name |
| `--seed` | int | random | Seed for reproducible output |
| `--video` | flag | false | Output GIF instead of PNG |
| `--duration` | float | 3.0 | GIF duration in seconds |
| `--fps` | int | 15 | Frames per second |
| `--variants` | int | 1 | Number of variants to generate |
| `--layout` | string | auto | Layout algorithm name |
| `--decoration` | string | auto | Decoration style |
| `--gradient` | string | auto | ASCII gradient name |
| `--output-dir` | string | `./media` | Output directory |

**Stdin JSON support**: All arguments can be provided via stdin JSON. CLI args override stdin values.

## Emotion System

The Flexible Output System uses a VAD (Valence-Arousal-Dominance) continuous space with 24 predefined emotion anchors (joy, euphoria, calm, love, fear, panic, sadness, etc.). Each axis ranges from -1 to +1. Text input maps to a VAD vector which drives all visual parameters continuously.

The kaomoji system has 20 emotion categories with 300+ faces. Selection: exact match -> multi-line match -> parent category fallback (bull/bear/neutral).

## Additional Documentation

- `docs/rendering.md` - Detailed rendering pipeline
- `docs/effects.md` - All effects with parameters
- `docs/flexible.md` - Flexible output system architecture
- `docs/kaomoji.md` - Kaomoji categories and rendering
- `docs/box_chars.md` - Box-drawing character system (37 charsets)
- `docs/usage.md` - CLI usage examples
