# VIZ Visual Options Reference

Run `viz capabilities --format json` for the authoritative, version-accurate list. This file provides context and categories.

## Layouts (5)

| Layout | Description |
|--------|-------------|
| `random_scatter` | Random placement |
| `grid_jitter` | Grid + random offset |
| `spiral` | Spiral arrangement |
| `force_directed` | Force-directed (mutual repulsion) |
| `preset` | Preset positions |

## Decorations (8)

`corners` / `edges` / `scattered` / `minimal` / `none` / `frame` / `grid_lines` / `circuit`

## Color Schemes (8)

| Scheme | Colors | Best For |
|--------|--------|----------|
| `heat` | Black -> Red -> Orange -> Yellow -> White | High arousal |
| `rainbow` | HSV hue cycle | Positive valence |
| `cool` | Blue -> Cyan -> White | Low arousal |
| `matrix` | Dark Green -> Bright Green | Neutral/tech |
| `plasma` | Multi-color with brightness pulse | Mixed |
| `ocean` | Deep Blue -> Cyan -> Sea White | Calm/oceanic |
| `fire` | Black -> Dark Red -> Orange -> Bright Yellow | Intense/fiery |
| `default` | Warm neutral | Fallback |

Set via `color_scheme` field in JSON or `--color-scheme` CLI arg. Custom palettes (`palette` field: 2+ RGB triplets) override named schemes.

## Blend Modes (overlay effects)

`ADD` / `SCREEN` / `OVERLAY` / `MULTIPLY`

Used in the `overlay` field: `{"effect":"wave","blend":"SCREEN","mix":0.3}`

## ASCII Gradients (73)

Control the character density ramp. Set via `gradient` field. All sourced from `lib/box_chars.py`.

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

Run `viz capabilities --format json` to discover all available `kaomoji_moods`.
