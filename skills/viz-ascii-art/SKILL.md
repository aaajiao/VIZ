---
name: viz-ascii-art
description: "Generate 1080x1080 ASCII art visualizations with kaomoji, procedural effects, and emotion-driven styles. Use when users want to create visualizations, ASCII art images, emotion-based graphics, market mood images, or generate kaomoji art. Supports PNG, animated GIF, and MP4 output. Trigger words: visualization, ASCII art, kaomoji, emotion image, mood graphic, market visualization, generate viz."
---

# VIZ ASCII Art Generator

AI handles intent, data, and emotion; VIZ renders 1080x1080 ASCII art.

## Quick Start

```bash
# Minimal
echo '{"emotion":"joy"}' | python3 viz.py generate

# With content
echo '{"source":"market","headline":"BTC $95K","emotion":"euphoria","metrics":["ETH: $4.2k"]}' | python3 viz.py generate

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
| `emotion` | string | One of 25 emotions (see references/EMOTIONS.md) |
| `source` | string | `market` / `art` / `news` / `mood` — sets visual vocabulary |
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
| `gradient` | string | `classic` / `smooth` / `matrix` / `plasma` / `blocks` / `glitch` / `circuit` / `cyber` / `organic` |
| `seed` | int | Reproducible output |
| `overlay` | object | `{"effect":"wave","blend":"SCREEN","mix":0.3}` — layer two effects |
| `params` | object | Effect-specific tuning, including deformation params (see references/COMPOSITION.md) |

### Output Control

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `video` | bool | false | Output GIF animation |
| `mp4` | bool | false | Also output MP4 (requires FFmpeg) |
| `duration` | float | 3.0 | GIF seconds |
| `fps` | int | 15 | Frames per second |
| `variants` | int | 1 | Generate multiple variants (different seeds) |

## Emotions at a Glance

25 predefined VAD (Valence-Arousal-Dominance) emotions. Full values in **references/EMOTIONS.md**.

| Category | Emotions |
|----------|----------|
| High-energy positive | `euphoria` `excitement` `joy` `surprise` `awe` |
| Low-energy positive | `calm` `serenity` `love` `hope` `trust` `nostalgia` |
| High-energy negative | `panic` `fear` `anxiety` `anger` `volatile` |
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

VIZ auto-selects from emotion; override with `effect` field.

Effects support deformation params via `params` field (e.g. `{"params": {"surface_noise": 0.5}}`). Domain transforms, PostFX, spatial masks, and structural variants are auto-selected by grammar — no manual input needed. See **references/COMPOSITION.md** for details.

## Content Sources

| Source | Particles | Atmosphere |
|--------|-----------|------------|
| `market` | `$\u00a5\u20ac\u20bf\u2191\u2193\u25b2\u25bc` | HODL, PUMP / SELL, EXIT |
| `art` | `\u2726\u25c6\u25cf\u25bd\u25b3\u25cb\u25c7` | CREATE, EXHIBIT |
| `news` | `\u25ba\u25c6\u25a0\u25cf\u25b6` | BREAKING, ALERT |
| `mood` | `\u00b7\u02da\u2727\u2218\u25cb\u25e6` | BREATHE, PEACE |

## Output

stdout JSON:
```json
{"status":"ok","results":[{"path":"media/viz_20260203_120000.png","seed":42,"format":"png"}],"emotion":"euphoria","source":"market"}
```

Specs: 1080x1080 PNG (quality=95), GIF, or MP4. Internal 160x160 nearest-neighbor upscale. Files in `./media/`.

## References

- **references/EMOTIONS.md** — Full VAD values for all 25 emotions and custom VAD usage
- **references/EFFECTS.md** — All 17 effects with parameters, ranges, and overlay/blend details
- **references/COMPOSITION.md** — Composition system: transforms, PostFX, masks, variants, deformation params
- **references/EXAMPLES.md** — Complete examples: market, art, news, mood, advanced techniques
