# VIZ Composition System Reference

Transforms, PostFX, masks, and variants are **auto-selected by grammar** — no manual specification needed. Use `params` to fine-tune deformation parameters that are passed directly to effects.

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

Grammar selects 0-3 transforms per render based on energy/structure.

| Transform | Params | Description |
|-----------|--------|-------------|
| `mirror_x` | — | Horizontal mirror |
| `mirror_y` | — | Vertical mirror |
| `mirror_quad` | — | Four-fold symmetry |
| `kaleidoscope` | segments (3-8) | N-fold rotational symmetry |
| `tile` | cols, rows (2-4) | Repeat/tile |
| `rotate` | angle | Rotation |
| `zoom` | factor (1.2-3.0) | Zoom in/out |
| `spiral_warp` | twist (0.3-1.5) | Spiral domain warp |
| `polar_remap` | — | Cartesian to polar |

## PostFX Chain (7, auto-selected)

Independent probability per effect. Applied to 160x160 buffer after rendering.

| PostFX | Params | Description |
|--------|--------|-------------|
| `vignette` | strength (0.3-0.7) | Darken edges |
| `scanlines` | spacing (3-6), darkness (0.2-0.4) | Horizontal lines |
| `threshold` | threshold (0.3-0.7) | Binary contrast |
| `edge_detect` | — | Sobel edge outlines |
| `invert` | — | Invert colors + density |
| `color_shift` | hue_shift (0.05-0.25) | Hue rotation |
| `pixelate` | block_size (3-6) | Lower resolution blocks |

## Spatial Masks (6, auto-selected)

Control how two effects blend across different regions.

| Mask | Description |
|------|-------------|
| `horizontal_split` | Top vs bottom |
| `vertical_split` | Left vs right |
| `diagonal` | Diagonal split with angle |
| `radial` | Center vs edges gradient |
| `noise` | Organic blobs via fractal noise |
| `sdf` | Circle/box/ring geometric shapes |

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

## Composition Modes (4, auto-selected)

| Mode | Description |
|------|-------------|
| `blend` | Standard CompositeEffect (ADD/SCREEN/OVERLAY/MULTIPLY) |
| `masked_split` | Spatial split via horizontal/vertical/diagonal masks |
| `radial_masked` | Center vs edges with radial mask |
| `noise_masked` | Organic noise-based region blending |
