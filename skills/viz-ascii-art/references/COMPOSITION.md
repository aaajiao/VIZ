# VIZ Composition System Reference

Transforms, PostFX, masks, and variants are **auto-selected by grammar** by default. You can also **precisely control** them via Director Mode fields: `transforms`, `postfx`, `composition`, `mask`, `variant`. Use `params` to fine-tune deformation parameters that are passed directly to effects.

## Deformation Params (user-settable via `params`)

| Effect | Param | Range | Description |
|--------|-------|-------|-------------|
| donut | `surface_noise` | 0.0-1.0 | Surface noise deformation |
| donut | `asymmetry_x` / `asymmetry_y` | 0.3-2.0 | Non-uniform scaling |
| donut | `twist` | 0.0-2.0 | Cross-section twist |
| donut | `count` | 1-3 | Number of tori |
| donut | `ring_offset` | 0.1-0.5 | Multi-torus orbit offset |
| wireframe_cube | `vertex_noise` | 0.0-1.0 | Vertex displacement noise |
| wireframe_cube | `morph` | 0.0-1.0 | Shape morphing factor |
| plasma | `self_warp` | 0.0-1.0 | Output-feedback coordinate warp |
| plasma | `noise_injection` | 0.0-1.0 | Random coordinate offset |
| wave | `self_warp` | 0.0-1.0 | Wave-feedback coordinate warp |
| wave | `noise_injection` | 0.0-1.0 | Random coordinate offset |
| moire | `distortion` | 0.0-1.0 | Polar noise distortion |
| moire | `multi_center` | 1-4 | Number of interference centers |
| chroma_spiral | `distortion` | 0.0-1.0 | Polar noise distortion |
| chroma_spiral | `multi_center` | 1-4 | Number of spiral centers |
| mod_xor | `distortion` | 0.0-1.0 | Coordinate noise distortion |

Example:
```json
{"effect": "donut", "params": {"surface_noise": 0.5, "twist": 1.2, "count": 2}}
```

## Domain Transforms (9, auto-selected)

Grammar selects 0-3 transforms per render based on energy/structure. Params can be static values or animated kwargs for GIF/video (e.g. `{"base": 0.0, "speed": 0.5, "mode": "linear"}`).

| Transform | Params | Animatable | Description |
|-----------|--------|-----------|-------------|
| `mirror_x` | — | — | Horizontal mirror |
| `mirror_y` | — | — | Vertical mirror |
| `mirror_quad` | — | — | Four-fold symmetry |
| `kaleidoscope` | segments (3-8) | — | N-fold rotational symmetry |
| `tile` | cols, rows (2-4) | — | Repeat/tile |
| `rotate` | angle | angle (linear) | Rotation |
| `zoom` | factor (1.2-3.0) | factor (oscillate) | Zoom in/out |
| `spiral_warp` | twist (0.3-1.5) | twist (linear) | Spiral domain warp |
| `polar_remap` | — | — | Cartesian to polar |

## PostFX Chain (7, auto-selected)

Independent probability per effect. Applied to 160x160 buffer after rendering. 4 effects support time-driven animation for GIF/video.

| PostFX | Params | Animation Params | Description |
|--------|--------|-----------------|-------------|
| `vignette` | strength (0.3-0.7) | `pulse_speed`, `pulse_amp` | Darken edges (pulsing) |
| `scanlines` | spacing (3-6), darkness (0.2-0.4) | `scroll_speed` | Horizontal lines (scrolling) |
| `threshold` | threshold (0.3-0.7) | — | Binary contrast |
| `edge_detect` | — | — | Sobel edge outlines |
| `invert` | — | — | Invert colors + density |
| `color_shift` | hue_shift (0.05-0.25) | `drift_speed` | Hue rotation (drifting) |
| `pixelate` | block_size (3-6) | `pulse_speed`, `pulse_amp` | Lower resolution blocks (pulsing) |

## Spatial Masks (6, auto-selected)

Control how two effects blend across different regions. All masks support `mask_anim_speed` param for GIF/video animation (0 = static, >0 = animated boundaries).

| Mask | Description | Animation |
|------|-------------|-----------|
| `horizontal_split` | Top vs bottom | Split oscillates |
| `vertical_split` | Left vs right | Split oscillates |
| `diagonal` | Diagonal split with angle | Angle rotates |
| `radial` | Center vs edges gradient | Radius pulses |
| `noise` | Organic blobs via fractal noise | Pattern drifts |
| `sdf` | Circle/box/ring geometric shapes | Size pulses |

## Structural Variants (32 named, auto-selected)

Grammar picks a named variant per effect and samples params from its ranges.

| Effect | Variants |
|--------|----------|
| donut (6) | classic, alien, thin_ring, fat_blob, multi, twisted |
| wireframe_cube (4) | classic, irregular, morphing, deformed |
| plasma (5) | classic, warped, noisy, turbulent, slow_morph |
| wave (4) | classic, warped, chaotic, minimal |
| moire (4) | classic, distorted, multi_center, dense |
| chroma_spiral (5) | classic, warped, multi, tight, loose |
| mod_xor (4) | classic, distorted, fine, layered |

## Composition Modes (4, auto-selected or via `composition` field)

| Mode | Description |
|------|-------------|
| `blend` | Standard CompositeEffect (ADD/SCREEN/OVERLAY/MULTIPLY) |
| `masked_split` | Spatial split via horizontal/vertical/diagonal masks |
| `radial_masked` | Center vs edges with radial mask |
| `noise_masked` | Organic noise-based region blending |

## Background Fill (auto-selected, ~320k combinations)

After main rendering, a **second render pass** fills `bg=None` cells with textured backgrounds. Grammar auto-selects all dimensions:

| Dimension | Options | Count |
|-----------|---------|-------|
| Effect | 13 lightweight candidates (excludes game_of_life/sand_game/slime_dish/dyna) | 13 |
| Variants | Sampled from VARIANT_REGISTRY | ~4 per effect |
| Transforms | 0-2 from mirror/tile/kaleidoscope/spiral_warp/polar_remap | ~15 combos |
| PostFX | 0-1 from vignette/color_shift/scanlines/threshold | 4 |
| Masks | 0-1 from radial/noise/diagonal | 3 |
| Color mode | 7 named schemes + continuous (warmth/saturation) | 8 |

Total: ~320,000 discrete background texture combinations × continuous parameters.

Background fill is fully automatic — no user-facing fields needed. Dim factor ~30% ensures backgrounds stay subtle.

## Director Mode (precise control)

**Delegate mode** (default): omit composition fields — grammar auto-selects optimal transforms, PostFX, masks, and variants from emotion+energy.

**Director mode**: specify any subset of fields — each specified field overrides grammar; unspecified fields are still auto-selected.

### Examples

**Single override** — force a variant, let grammar handle everything else:
```json
{"effect": "donut", "variant": "alien"}
```

**Transform + PostFX** — kaleidoscope symmetry with vignette and hue rotation:
```json
{
  "emotion": "awe",
  "effect": "chroma_spiral",
  "transforms": [{"type": "kaleidoscope", "segments": 8}],
  "postfx": [{"type": "vignette", "strength": 0.5}, {"type": "color_shift", "hue_shift": 0.15}]
}
```

**Full Director** — all composition dimensions specified:
```json
{
  "emotion": "euphoria",
  "effect": "plasma",
  "variant": "warped",
  "transforms": [{"type": "kaleidoscope", "segments": 6}],
  "postfx": [{"type": "vignette", "strength": 0.5}, {"type": "color_shift", "hue_shift": 0.1}],
  "composition": "radial_masked",
  "mask": "radial:center_x=0.5,radius=0.3",
  "seed": 100
}
```

### Common Combos

| Transforms | PostFX | Visual Character |
|------------|--------|------------------|
| `kaleidoscope` (6-8 segments) | `vignette` | Mandala, spiritual |
| `mirror_quad` | `scanlines` | Retro symmetry |
| `spiral_warp` | `color_shift` | Psychedelic swirl |
| `tile` (3x3) | `edge_detect` | Grid wireframe |
| `polar_remap` | `vignette` + `scanlines` | Tunnel / portal |

### CLI equivalent

```bash
python3 viz.py generate --effect plasma --variant warped \
  --transforms kaleidoscope:segments=6 \
  --postfx vignette:strength=0.5 color_shift:hue_shift=0.1 \
  --composition radial_masked --mask radial:center_x=0.5,radius=0.3
```
