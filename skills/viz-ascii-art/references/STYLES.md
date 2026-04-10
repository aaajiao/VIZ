# Style Presets

8 visual styles that bundle effect, transform, postfx, and gradient choices into a single `"style"` field. Each style randomly picks from its pools per seed, ensuring variety within a consistent visual character.

## Usage

```json
{"emotion": "joy", "style": "geometric"}
```

Style + explicit overrides (explicit fields take priority):
```json
{"emotion": "euphoria", "style": "psychedelic", "color_scheme": "fire"}
```

## Available Styles

### `geometric` — Structured, angular
- **Effects**: sdf_shapes, wireframe_cube, mod_xor, ten_print
- **Transforms**: mirror_quad, kaleidoscope(6), kaleidoscope(8), mirror_x
- **PostFX**: edge_detect, threshold, vignette
- **Gradients**: box_density, geometric, squares, box_cross, circuit

### `organic` — Flowing, natural
- **Effects**: noise_field, wobbly, slime_dish, wave
- **Transforms**: spiral_warp(0.5), spiral_warp(0.8), none
- **PostFX**: vignette, color_shift, none
- **Gradients**: organic, circles, braille_density, dots_density, smooth

### `retro` — Nostalgic, pixelated
- **Effects**: ten_print, mod_xor, game_of_life, plasma
- **Transforms**: tile(2x2), tile(3x3), none
- **PostFX**: scanlines, scanlines+vignette, pixelate
- **Gradients**: cp437_retro, classic, blocks, blocks_fine, digits

### `psychedelic` — Colorful, hypnotic
- **Effects**: chroma_spiral, moire, plasma, cppn
- **Transforms**: kaleidoscope(8), kaleidoscope(12), polar_remap, spiral_warp(1.5)
- **PostFX**: color_shift, color_shift+vignette, invert
- **Gradients**: sparkles, glitch, cyber, noise, tech

### `minimal` — Clean, sparse
- **Effects**: noise_field, wave, sdf_shapes, plasma
- **Transforms**: none, none, mirror_x
- **PostFX**: threshold, none, vignette
- **Gradients**: dots_density, smooth, box_thin, classic, default

### `brutal` — Harsh, intense
- **Effects**: flame, plasma, dyna, mod_xor
- **Transforms**: mirror_x, mirror_y, zoom(2x)
- **PostFX**: scanlines+threshold, threshold, edge_detect+invert
- **Gradients**: blocks_ultra, blocks, tech, box_thick

### `ethereal` — Dreamy, soft
- **Effects**: wobbly, wave, sand_game, noise_field
- **Transforms**: spiral_warp(0.3), rotate(0.2), none
- **PostFX**: vignette+color_shift, color_shift, none
- **Gradients**: circles_arc, organic, smooth, sparkles, stars_density

### `glitch` — Digital, broken
- **Effects**: cppn, mod_xor, plasma, moire
- **Transforms**: tile(3x3)+mirror_quad, mirror_quad+zoom(1.5x), tile(2x2)
- **PostFX**: pixelate+invert, pixelate+scanlines, invert+edge_detect
- **Gradients**: glitch, cyber, noise, cp437_retro, tech
