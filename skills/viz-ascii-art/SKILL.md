---
name: viz-ascii-art
description: "Generate ASCII art visualizations (default 1080x1080, variable resolution up to 3840px, custom palettes) with kaomoji, procedural effects, and emotion-driven styles. Use when users want to create visualizations, ASCII art images, emotion-based graphics, market mood images, or generate kaomoji art. Supports PNG, animated GIF, and MP4 output. Trigger words: visualization, ASCII art, kaomoji, emotion image, mood graphic, market visualization, generate viz."
---

# VIZ ASCII Art Generator

AI handles intent, data, and emotion; VIZ renders ASCII art (default 1080x1080, variable resolution, custom palettes).

## Quick Start

```bash
# Minimal
echo '{"emotion":"joy"}' | python3 viz.py generate

# With content
echo '{"headline":"BTC $95K","emotion":"euphoria","metrics":["ETH: $4.2k"]}' | python3 viz.py generate

# Animated GIF
echo '{"emotion":"panic","video":true}' | python3 viz.py generate

# Query all available options
python3 viz.py capabilities --format json
```

Run from the VIZ project root. Only dependency: `pillow`.

## JSON Input (all fields optional)

### Core

| Field | Type | Description |
|-------|------|-------------|
| `emotion` | string | One of 26 emotions (see references/EMOTIONS.md) |
| `headline` | string | Main text |
| `metrics` | list[str] | Data lines: `["BTC: $92k", "ETH: $4.2k"]` |
| `body` | string | Body text (also used for emotion inference) |
| `title` | string | Overlay title |

### Visual Overrides

| Field | Type | Description |
|-------|------|-------------|
| `effect` | string | Background effect (see references/EFFECTS.md for all 17) |
| `vad` | str/list | Direct VAD vector `[0.8, 0.5, 0.3]` — bypasses emotion name |
| `layout` | string | `random_scatter` / `grid_jitter` / `spiral` / `force_directed` / `preset` |
| `decoration` | string | `corners` / `edges` / `scattered` / `minimal` / `none` / `frame` / `grid_lines` / `circuit` |
| `gradient` | string | See gradient list below (73 presets) |
| `color_scheme` | string | `heat` / `rainbow` / `cool` / `matrix` / `plasma` / `ocean` / `fire` / `default` |
| `palette` | list[[r,g,b]] | Custom color palette (2+ RGB triplets 0-255), overrides `color_scheme` |
| `seed` | int | Reproducible output — **omit or vary** (see tip below) |
| `overlay` | object | `{"effect":"wave","blend":"SCREEN","mix":0.3}` — layer two effects |
| `params` | object | Effect-specific tuning, including deformation params (see references/COMPOSITION.md) |
| `transforms` | list[dict] | Domain transform chain: `[{"type":"kaleidoscope","segments":6}]` |
| `postfx` | list[dict] | PostFX chain: `[{"type":"vignette","strength":0.5}]` |
| `composition` | string | `blend` / `masked_split` / `radial_masked` / `noise_masked` / `sdf_masked` |
| `mask` | string | Mask type+params (CLI: `radial:center_x=0.5,radius=0.3`) |
| `variant` | string | Force effect variant name (e.g. `warped`, `alien`, `turbulent`) |

**Seed tip:** Do NOT always use `seed: 42`. Each seed produces a completely different visual — effect, layout, gradient, decoration are all seed-driven. Omit `seed` to let VIZ randomize, or pick a varied number (timestamp, random int, hash of the prompt). Only pin a seed when the user asks to reproduce a specific result.

### Output Control

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `video` | bool | false | Output GIF animation |
| `mp4` | bool | false | Also output MP4 (requires FFmpeg) |
| `duration` | float | 3.0 | GIF seconds |
| `fps` | int | 15 | Frames per second |
| `variants` | int | 1 | Generate multiple variants (different seeds) |
| `width` | int | 1080 | Output width in pixels (120-3840) |
| `height` | int | 1080 | Output height in pixels (120-3840) |

## Emotions at a Glance

26 predefined VAD (Valence-Arousal-Dominance) emotions. Full values in **references/EMOTIONS.md**.

| Category | Emotions |
|----------|----------|
| High-energy positive | `euphoria` `excitement` `joy` `surprise` `awe` |
| Low-energy positive | `calm` `serenity` `love` `hope` `trust` `nostalgia` |
| High-energy negative | `panic` `fear` `anxiety` `anger` `rage` `volatile` |
| Low-energy negative | `sadness` `despair` `melancholy` `boredom` |
| Special | `bull` `bear` `neutral` `contempt` `disgust` |

Priority: `emotion` field > `vad` field > infer from text > `neutral`.

## Effects at a Glance

17 procedural effects. Full params in **references/EFFECTS.md**.

| Effect | Best For |
|--------|----------|
| `plasma` | High-energy, euphoria |
| `flame` | Panic, anger |
| `wave` | Flowing, calm |
| `cppn` | Unique per seed |
| `game_of_life` | Organic complexity |
| `donut` | 3D, futuristic |
| `slime_dish` | Biological, organic |
| `ten_print` | Retro, nostalgic |
| `noise_field` | Natural, organic |
| `moire` / `chroma_spiral` | Psychedelic |
| `sdf_shapes` / `wireframe_cube` | Geometric, structural |
| `wobbly` | Dreamy, soft |
| `sand_game` | Meditative |
| `mod_xor` | Mathematical, fractal |
| `dyna` | Dynamic, energetic |

VIZ auto-selects from emotion; override with `effect` field. Background is separately textured via a second render pass using another effect + transforms + color scheme (auto-selected by grammar).

Effects support deformation params via `params` field (e.g. `{"params": {"surface_noise": 0.5}}`).

## Director Mode

Grammar auto-selects transforms, PostFX, masks, and variants from emotion; Director Mode fields override any dimension for precise control. In GIF/video mode, composition layers animate automatically (grammar injects animation params based on energy).

| Field | Type | What it controls |
|-------|------|------------------|
| `transforms` | list[dict] | Domain transform chain (mirror, kaleidoscope, tile, etc.); params can be animated kwargs |
| `postfx` | list[dict] | Post-processing chain with optional animation (vignette pulse, scanline scroll, etc.) |
| `composition` | string | How two effects merge: `blend` / `masked_split` / `radial_masked` / `noise_masked` / `sdf_masked` |
| `mask` | string | Spatial mask for composition: `radial`, `noise`, `diagonal`, etc. |
| `variant` | string | Named structural variant per effect (e.g. `warped`, `alien`, `turbulent`) |
| `params` | object | Effect-specific tuning: deformation, noise, twist, `mask_anim_speed` (see references/COMPOSITION.md) |

**Simple** — kaleidoscope symmetry + vignette:
```json
{
  "emotion": "awe",
  "effect": "chroma_spiral",
  "transforms": [{"type": "kaleidoscope", "segments": 8}],
  "postfx": [{"type": "vignette", "strength": 0.5}]
}
```

**Full Director** — effect + variant + transforms + PostFX + composition:
```json
{
  "emotion": "euphoria",
  "effect": "plasma",
  "variant": "warped",
  "transforms": [{"type": "kaleidoscope", "segments": 6}],
  "postfx": [{"type": "vignette", "strength": 0.5, "pulse_speed": 0.5}, {"type": "color_shift", "hue_shift": 0.1, "drift_speed": 0.3}],
  "composition": "radial_masked",
  "seed": 100
}
```

**Animated GIF** — rotating transform + scrolling scanlines + pulsing mask:
```json
{
  "emotion": "euphoria",
  "video": true,
  "transforms": [{"type": "rotate", "angle": {"base": 0.0, "speed": 0.3, "mode": "linear"}}],
  "postfx": [{"type": "scanlines", "spacing": 4, "scroll_speed": 2.0}],
  "params": {"mask_anim_speed": 1.0}
}
```

Omit any field to let grammar auto-select it. Full option lists in **references/COMPOSITION.md**.

## ASCII Gradients

73 gradient presets (450+ unique characters) controlling character density ramps. Set via `gradient` field. All gradients sourced from `lib/box_chars.py`.

| Category | Gradients |
|----------|-----------|
| Classic ASCII (5) | `classic` / `default` / `smooth` / `matrix` / `plasma` |
| Block Fill (8) | `blocks` / `blocks_fine` / `blocks_ultra` / `glitch` / `vbar` / `hbar` / `quadrant` / `halves` |
| Box-Drawing (20) | `box_density` / `box_vertical` / `box_cross` / `box_thin` / `box_thin_corner` / `box_thick` / `box_thick_corner` / `box_double` / `box_double_corner` / `box_rounded` / `box_mixed_dh` / `box_mixed_dv` / `box_mixed_a` / `box_mixed_b` / `box_complex_a` / `box_complex_b` / `box_complex_c` / `box_ends` / `box_weight` / `diagonal` |
| Geometric (14) | `dots_density` / `geometric` / `braille_density` / `circles` / `circles_half` / `circles_arc` / `squares` / `diamonds` / `triangles` / `quarters_geo` / `squares_fill` / `arrows_sm` / `arrows_lg` / `geo_misc` |
| Typography (15) | `punctuation` / `editorial` / `math` / `math_rel` / `brackets` / `greek` / `currency` / `symbols` / `superscript` / `quotes` / `ligature` / `diacritics` / `digits` / `alpha_lower` / `alpha_upper` |
| Stars / Arrows (4) | `stars_density` / `sparkles` / `arrows_flow` / `arrows_double` |
| CP437 / Misc (2) | `cp437_retro` / `misc_symbols` |
| Mixed (5) | `tech` / `cyber` / `organic` / `noise` / `circuit` |

## Vocabulary Overrides

Emotion drives all visual choices by default. Override via `vocabulary` field:

```json
{"emotion": "euphoria", "vocabulary": {"particles": "$€¥₿↑↓", "kaomoji_moods": ["euphoria", "excitement"]}}
```

| Field | Type | Effect |
|-------|------|--------|
| `particles` | string | Override particle charset |
| `kaomoji_moods` | list[str] | Override kaomoji mood pool |
| `decoration_chars` | list[str] | Override decoration characters |

Run `python3 viz.py capabilities --format json` to discover all available kaomoji moods and color schemes.

## Output

stdout JSON:
```json
{"status":"ok","results":[{"path":"media/viz_20260203_120000_s42.png","seed":42,"format":"png"}],"emotion":"euphoria","resolution":[1080,1080]}
```

Specs: Default 1080x1080, configurable via `width`/`height` (120-3840px, supports portrait/landscape). PNG (quality=95), GIF, or MP4. Internal buffer auto-scaled (~6.75x smaller). Background filled via second render pass (independent effect + color scheme, ~750k texture combinations). Files in `./media/`, named `viz_{timestamp}_s{seed}.{ext}`. Each output has a companion `.json` with input params for reproducibility.

### Custom Palette Example

Override color scheme with arbitrary colors:
```json
{"emotion":"joy", "palette":[[0,0,0],[255,0,128],[255,255,0]]}
```

### Variable Resolution Examples

```json
{"emotion":"calm", "width":540, "height":540}
{"emotion":"euphoria", "width":1080, "height":1920}
```

## References

- **references/EMOTIONS.md** — Full VAD values for all 26 emotions and custom VAD usage
- **references/EFFECTS.md** — All 17 effects with parameters, ranges, and overlay/blend details
- **references/COMPOSITION.md** — Composition system: transforms, PostFX, masks, variants, deformation params
- **references/EXAMPLES.md** — Complete examples: market, art, news, mood, advanced techniques
