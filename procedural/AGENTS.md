# procedural/ - ASCII Art Rendering Engine

**Parent**: See `/workspace/viz/AGENTS.md` for project-level conventions.

Modular rendering system for animated ASCII art. Three-stage pipeline (pre/main/post), pluggable effects, sprite composition.

## Architecture

```
procedural/
├── engine.py          # Orchestrator: render_frame, render_video, save_gif
├── types.py           # Context, Cell, Buffer, Effect protocol
├── layers.py          # Sprite animations: TextSprite, KaomojiSprite
├── renderer.py        # buffer_to_image, upscale_image
├── palette.py         # ASCII gradients, color schemes
├── params.py          # ParamSpec, reproducible RNG
├── effects/
│   ├── __init__.py    # EFFECT_REGISTRY, get_effect()
│   ├── base.py        # BaseEffect (default pre/post)
│   ├── plasma.py      # 4-layer sine interference
│   ├── flame.py       # Heat propagation + decay
│   ├── wave.py        # Multi-frequency sine
│   ├── moire.py       # Radial wave multiplication
│   ├── sdf_shapes.py  # Smooth distance fields
│   └── noise_field.py # ValueNoise + FBM
└── core/
    ├── vec.py         # Vec2 operations
    ├── sdf.py         # sd_circle, sd_box, smooth ops
    ├── noise.py       # ValueNoise, fbm, turbulence
    └── mathx.py       # clamp, mix, smoothstep
```

## Rendering Pipeline

```
1. Engine creates Context + Buffer (160×160)
2. effect.pre(ctx, buffer) → state dict
3. for y,x: buffer[y][x] = effect.main(x, y, ctx, state)
4. effect.post(ctx, buffer, state)
5. buffer_to_image() → PIL (160×160)
6. sprite.render(image, time) for each sprite
7. upscale_image() → 1080×1080 (NEAREST)
8. sharpen + contrast → final frame
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new effect | `effects/` + register in `__init__.py` | Extend BaseEffect |
| Change color mapping | `palette.py` | `value_to_color()` |
| New ASCII gradient | `palette.py` | Add to `ASCII_GRADIENTS` |
| Animation function | `layers.py` | `breathing`, `floating`, `color_cycle` |
| Math primitives | `core/` | Pure Python, no NumPy |

## Effect Protocol

```python
class MyEffect:
    def pre(self, ctx, buffer):
        """Initialize state. Called once per frame."""
        return {'my_param': ctx.params.get('my_param', 1.0)}
    
    def main(self, x, y, ctx, state):
        """Per-pixel. Return Cell(char_idx, fg, bg)."""
        value = ...  # 0.0 to 1.0
        return Cell(char_idx=int(value*9), fg=color, bg=None)
    
    def post(self, ctx, buffer, state):
        """Global modifications. Optional."""
        pass
```

**Register**: `effects/__init__.py`
```python
from .my_effect import MyEffect
EFFECT_REGISTRY['my_effect'] = MyEffect
```

## Key Types

| Type | Description |
|------|-------------|
| `Context` | width, height, time, frame, seed, rng, params |
| `Cell` | char_idx (0-9), fg (RGB tuple), bg (RGB or None) |
| `Buffer` | `list[list[Cell]]` - 2D grid |
| `Effect` | Protocol: pre/main/post methods |

## Usage

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

## ANTI-PATTERNS

- ❌ Computing at 1080×1080 (use 160×160 + upscale)
- ❌ NumPy imports (pure Python only)
- ❌ MP4 output (GIF only)
- ❌ Modifying ctx inside effect (immutable by convention)

## Core Math (no NumPy)

| Module | Key Functions |
|--------|---------------|
| `vec.py` | `Vec2`, `length`, `normalize`, `rotate`, `dot` |
| `sdf.py` | `sd_circle`, `sd_box`, `op_smooth_union` |
| `noise.py` | `ValueNoise`, `.fbm()`, `.turbulence()` |
| `mathx.py` | `clamp`, `mix`, `smoothstep`, `map_range` |

## Available Effects

| Effect | Description |
|--------|-------------|
| `plasma` | Animated sine wave interference |
| `flame` | Doom-style fire (heat propagation) |
| `wave` | Multi-frequency sine stacking |
| `moire` | Radial interference patterns |
| `sdf_shapes` | Distance field circles/boxes |
| `noise_field` | Perlin-like value noise |

## Color Schemes

`value_to_color(v, scheme)` where `v` is 0.0-1.0:

| Scheme | Gradient |
|--------|----------|
| `heat` | Black → Red → Orange → Yellow → White |
| `rainbow` | HSV hue cycle |
| `cool` | Blue → Cyan → White |
| `matrix` | Dark Green → Bright Green |
| `plasma` | Multi-color with brightness pulse |
