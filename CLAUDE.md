# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

ASCII art visualization toolkit producing 1080x1080 PNG/GIF/MP4 images with kaomoji, procedural effects, and emotion-driven visual styles. Pure Python 3 + Pillow, no build system. `viz.py` is the single CLI entry point.

## Development Workflow

**Always develop new features on the `dev` branch.** PRs target `main`.

```bash
# Dev environment setup (if ffmpeg/pyright not found)
bash .devcontainer/setup.sh

# Run all tests
pytest tests/ -v

# Run single test file
pytest tests/test_emotion.py -v

# Run single test
pytest tests/test_emotion.py::TestEmotionAnchors::test_joy -v

# Generate a test visualization
python3 viz.py generate --emotion euphoria --seed 42
```

No build step. No requirements.txt. Only dependency is `Pillow>=9.0.0`. CI runs `pytest tests/ -v --tb=short` on Python 3.11.

## Architecture

**Two-layer design**: `lib/` provides shared utilities (kaomoji, effects, text rendering), `procedural/` is the rendering engine.

**Rendering pipeline** (the critical path):
1. `viz.py generate` parses CLI args + stdin JSON -> calls `FlexiblePipeline`
2. `FlexiblePipeline` (`procedural/flexible/pipeline.py`) orchestrates: emotion -> VAD vector -> visual grammar -> effect selection -> sprite layout -> decoration
3. `Engine` (`procedural/engine.py`) renders: creates 160x160 Buffer of Cells -> effect fills buffer -> `buffer_to_image()` -> sprites overlay -> upscale to 1080x1080 via NEAREST -> sharpen + contrast -> save

**Key types** (in `procedural/types.py`): `Context` (immutable by convention), `Cell` (char_idx 0-9, fg RGB, bg RGB|None), `Buffer` (2D Cell grid), `Effect` (Protocol: pre/main/post).

**Emotion system**: VAD (Valence-Arousal-Dominance) continuous space with 25 anchors in `procedural/flexible/emotion.py`. Each axis -1 to +1. Drives all visual parameters.

**Content flow**: stdin JSON or CLI args -> `FlexiblePipeline` -> rendered image -> stdout JSON with path.

## Forbidden Patterns

- **NumPy** - all math must be pure Python stdlib (`procedural/core/` has vec, sdf, noise, mathx)
- **High-res compute** - always 160x160 internally, upscale to 1080x1080
- **Type hints** - not used except in `procedural/types.py` and `procedural/flexible/`
- **Empty catch blocks** - only acceptable for pixel manipulation glitch effects and font loading fallbacks

## Code Conventions

- **Imports**: stdlib -> third-party -> local, blank-line separated. Local imports use `try/except ImportError` for path flexibility (`from lib.x` with fallback to `from viz.lib.x`).
- **Naming**: `SCREAMING_SNAKE` constants, `snake_case` functions, `PascalCase` classes, `snake_case` dict keys.
- **Docstrings**: Bilingual Chinese/English format: `"""生成可视化 - Generate visualization"""`
- **Font loading**: Always provide fallback with `try: truetype() except: load_default()`
- **Canvas**: Always 1080x1080 (`WIDTH, HEIGHT = 1080, 1080`), post-process with sharpen + contrast 1.4
- **Output paths**: Timestamped in `./media/` directory

## Where to Make Changes

| Task | Location |
|------|----------|
| New CLI command | `viz.py` -> add subparser + command function |
| New vocabulary source | `lib/vocabulary.py` -> `VOCABULARIES` dict |
| New background effect | `procedural/effects/` + register in `__init__.py` EFFECT_REGISTRY |
| Color scheme | `procedural/palette.py` -> `COLOR_SCHEMES`, `ASCII_GRADIENTS` |
| Kaomoji faces | `lib/kaomoji_data.py` -> `KAOMOJI_SINGLE` dict |
| Box-drawing charset | `lib/box_chars.py` -> `CHARSETS` |
| Video/GIF/MP4 rendering | `procedural/engine.py` -> `render_video()`, `save_gif()`, `save_mp4()` |
| Emotion mapping | `procedural/flexible/emotion.py` -> VAD anchors |
| Visual grammar rules | `procedural/flexible/grammar.py` |
| Decoration style | `procedural/flexible/decorations.py` -> add `deco_xxx()` + register |
| Content integration | `procedural/flexible/pipeline.py` -> `FlexiblePipeline` |
| Layout algorithms | `procedural/layouts.py` -> scatter, grid, spiral, force |
| Sprite animation | `procedural/layers.py` -> breathing, floating, color_cycle |

## Adding a New Effect

```python
# procedural/effects/my_effect.py
class MyEffect:
    def pre(self, ctx, buffer):    # Init state, called once per frame, return dict
        return {'param': ctx.params.get('param', 1.0)}
    def main(self, x, y, ctx, state):  # Per-pixel, return Cell
        return Cell(char_idx=int(value * 9), fg=color, bg=None)
    def post(self, ctx, buffer, state):  # Optional global modifications
        pass

# Register in procedural/effects/__init__.py:
from .my_effect import MyEffect
EFFECT_REGISTRY['my_effect'] = MyEffect
```

## MP4 Output

MP4 uses FFmpeg subprocess (not a Python library). Gracefully degrades to GIF-only if FFmpeg unavailable. Triggered via `--video --mp4` flags.

## Further Reference

Detailed docs in `docs/`: `ai-integration.md` (start here), `rendering.md`, `flexible.md`, `effects.md`, `kaomoji.md`, `box_chars.md`, `usage.md`.
