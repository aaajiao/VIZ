# VIZ Effects Reference

Detailed documentation for all 17 procedural background effects.

## Effect Selection

VIZ auto-selects effects based on emotion, but you can override with `effect` field:

```json
{"emotion": "joy", "effect": "plasma"}
```

## Effects

### plasma

**Animated sine wave interference patterns (4-layer)**

Best for: High-energy emotions (euphoria, excitement, joy)

```json
{"effect": "plasma", "params": {"frequency": 2.0, "speed": 1.0}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| frequency | 2.0 | 0.5-5.0 | Wave frequency |
| speed | 1.0 | 0.1-3.0 | Animation speed |
| self_warp | 0.0 | 0.0-1.0 | Output-feedback coordinate warp |
| noise_injection | 0.0 | 0.0-1.0 | Random coordinate offset |

---

### flame

**Doom-style fire propagation with heat decay**

Best for: Panic, anger, intense negative emotions

```json
{"effect": "flame", "params": {"intensity": 0.8, "cooling": 0.02}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| intensity | 0.8 | 0.3-1.0 | Fire intensity |
| cooling | 0.02 | 0.01-0.05 | Heat decay rate |

---

### wave

**Multi-frequency sine stacking**

Best for: Flowing, calm, meditative moods

```json
{"effect": "wave", "params": {"layers": 4, "amplitude": 1.0}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| layers | 4 | 2-8 | Number of wave layers |
| amplitude | 1.0 | 0.5-2.0 | Wave amplitude |
| self_warp | 0.0 | 0.0-1.0 | Wave-feedback coordinate warp |
| noise_injection | 0.0 | 0.0-1.0 | Random coordinate offset |

---

### moire

**Radial wave multiplication patterns**

Best for: Mysterious, psychedelic, awe-inspiring

```json
{"effect": "moire", "params": {"rings": 20, "rotation": 0.5}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| rings | 20 | 5-50 | Number of radial rings |
| rotation | 0.5 | 0-2.0 | Rotation speed |
| distortion | 0.0 | 0.0-1.0 | Polar noise distortion |
| multi_center | 1 | 1-4 | Number of interference centers |

---

### sdf_shapes

**Smooth distance field geometry (circles, boxes)**

Best for: Structural, modern, clean aesthetics

```json
{"effect": "sdf_shapes", "params": {"shape_count": 5, "smoothness": 0.1}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| shape_count | 5 | 1-20 | Number of shapes |
| smoothness | 0.1 | 0.01-0.5 | Edge smoothness |

---

### noise_field

**Perlin-like value noise with FBM (Fractional Brownian Motion)**

Best for: Organic, natural, calm moods

```json
{"effect": "noise_field", "params": {"octaves": 4, "persistence": 0.5}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| octaves | 4 | 1-8 | FBM octave layers |
| persistence | 0.5 | 0.3-0.8 | Amplitude decay |
| scale | 1.0 | 0.5-3.0 | Noise scale |

---

### cppn

**CPPN (Compositional Pattern-Producing Network) neural patterns**

Best for: Unique, seed-dependent artistic patterns. Every seed produces completely different output.

```json
{"effect": "cppn", "params": {"complexity": 5, "symmetry": true}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| complexity | 5 | 2-10 | Network depth |
| symmetry | true | bool | Enable radial symmetry |

---

### ten_print

**Classic Commodore 64 maze pattern with animated diagonal lines**

Best for: Retro, nostalgic, chaotic/playful moods

```json
{"effect": "ten_print", "params": {"cell_size": 6, "probability": 0.5}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| cell_size | 6 | 4-12 | Grid cell size |
| probability | 0.5 | 0.3-0.7 | Probability of \ vs / |
| speed | 1.0 | 0.1-3.0 | Animation speed |

---

### game_of_life

**Conway's Game of Life cellular automaton with cell age tracking**

Best for: Organic complexity, contemplative moods

```json
{"effect": "game_of_life", "params": {"density": 0.4, "speed": 5.0}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| density | 0.4 | 0.3-0.7 | Initial fill ratio |
| speed | 5.0 | 1.0-15.0 | Generations per second |
| wrap | true | bool | Toroidal (wrapping) topology |

---

### donut

**Rotating 3D torus with z-buffer and per-pixel lighting (donut.c)**

Best for: Futuristic, technical aesthetics

```json
{"effect": "donut", "params": {"R1": 1.0, "R2": 2.0, "rotation_speed": 1.0}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| R1 | 1.0 | 0.5-3.0 | Minor radius (cross-section) |
| R2 | 2.0 | 1.0-5.0 | Major radius (ring distance) |
| rotation_speed | 1.0 | 0.1-5.0 | Rotation speed |
| surface_noise | 0.0 | 0.0-1.0 | Surface noise deformation |
| asymmetry_x | 1.0 | 0.3-2.0 | X-axis non-uniform scaling |
| asymmetry_y | 1.0 | 0.3-2.0 | Y-axis non-uniform scaling |
| twist | 0.0 | 0.0-2.0 | Cross-section twist |
| count | 1 | 1-3 | Number of tori |
| ring_offset | 0.3 | 0.1-0.5 | Multi-torus orbit offset |

---

### mod_xor

**Fractal patterns via bitwise XOR/AND/OR with modular arithmetic**

Best for: Mathematical, abstract, high-energy visuals

```json
{"effect": "mod_xor", "params": {"modulus": 16, "operation": "xor"}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| modulus | 16 | 2-64 | Base modulus value |
| operation | "xor" | xor/and/or | Bitwise operation |
| layers | 1 | 1-3 | Number of stacked layers |
| speed | 0.5 | 0.1-2.0 | Animation speed |
| zoom | 1.0 | 0.5-3.0 | Coordinate zoom |
| distortion | 0.0 | 0.0-1.0 | Coordinate noise distortion |

---

### wireframe_cube

**3D rotating wireframe cube via SDF edge rendering with perspective**

Best for: Geometric, tech aesthetics, structured moods

```json
{"effect": "wireframe_cube", "params": {"scale": 0.3, "edge_thickness": 0.015}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| rotation_speed_x | 0.7 | 0.0-3.0 | X-axis rotation speed |
| rotation_speed_y | 1.0 | 0.0-3.0 | Y-axis rotation speed |
| rotation_speed_z | 0.3 | 0.0-3.0 | Z-axis rotation speed |
| scale | 0.3 | 0.1-0.5 | Cube scale factor |
| edge_thickness | 0.015 | 0.005-0.05 | Edge line thickness |
| vertex_noise | 0.0 | 0.0-1.0 | Vertex displacement noise |
| morph | 0.0 | 0.0-1.0 | Shape morphing factor |

---

### chroma_spiral

**Polar spiral with chromatic aberration (RGB channel offset)**

Best for: Psychedelic, hypnotic, colorful aesthetics

```json
{"effect": "chroma_spiral", "params": {"arms": 3, "chroma_offset": 0.1}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| arms | 3 | 1-8 | Number of spiral arms |
| tightness | 0.5 | 0.1-2.0 | Spiral compression |
| speed | 1.0 | 0.1-3.0 | Animation speed |
| chroma_offset | 0.1 | 0.0-0.3 | Chromatic aberration strength |
| distortion | 0.0 | 0.0-1.0 | Polar noise distortion |
| multi_center | 1 | 1-4 | Number of spiral centers |

---

### wobbly

**Domain warping via iterative noise displacement for fluid distortion**

Best for: Dreamy, soft, organic visuals

```json
{"effect": "wobbly", "params": {"warp_amount": 0.4, "iterations": 2}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| warp_amount | 0.4 | 0.1-1.0 | Displacement magnitude |
| warp_freq | 0.03 | 0.01-0.1 | Base warping frequency |
| iterations | 2 | 1-3 | Warp iterations |
| speed | 0.5 | 0.1-2.0 | Animation speed |

---

### sand_game

**Falling sand particle simulation with gravity and sliding**

Best for: Meditative, calm, passive observation

```json
{"effect": "sand_game", "params": {"spawn_rate": 0.3, "particle_types": 2}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| spawn_rate | 0.3 | 0.1-0.8 | Particle spawn probability |
| gravity_speed | 2 | 1-5 | Physics steps per frame |
| particle_types | 2 | 1-3 | Distinct color types |

---

### slime_dish

**Physarum slime mold agent simulation with chemotaxis trails**

Best for: Biological, organic, contemplative moods

```json
{"effect": "slime_dish", "params": {"agent_count": 2000, "decay_rate": 0.95}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| agent_count | 2000 | 500-5000 | Number of agents |
| sensor_distance | 9 | 3-15 | Agent sensing range |
| sensor_angle | 0.4 | 0.2-1.0 | Sensor cone angle (rad) |
| decay_rate | 0.95 | 0.9-0.99 | Trail decay per frame |
| speed | 3 | 1-5 | Simulation steps per frame |

---

### dyna

**Dynamic moving attractors generating sine wave interference**

Best for: Energetic, excited, joyful moods

```json
{"effect": "dyna", "params": {"attractor_count": 4, "frequency": 0.5}}
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| attractor_count | 4 | 2-8 | Moving wave sources |
| frequency | 0.5 | 0.1-2.0 | Wave frequency |
| speed | 1.0 | 0.1-3.0 | Attractor movement speed |
| bounce | true | bool | Bounce vs. wrap at edges |

---

## Effect Overlay

Combine two effects using overlay:

```json
{
  "effect": "noise_field",
  "overlay": {
    "effect": "wave",
    "blend": "SCREEN",
    "mix": 0.3
  }
}
```

**Blend modes**:
- `ADD` — Additive blending (brightens)
- `SCREEN` — Screen blend (soft brightening)
- `OVERLAY` — Contrast enhancement
- `MULTIPLY` — Darkening blend

---

## Color Schemes

Effects use these color schemes based on emotion:

| Scheme | Colors | Used For |
|--------|--------|----------|
| `heat` | Black → Red → Orange → Yellow → White | High arousal |
| `rainbow` | HSV hue cycle | Positive valence |
| `cool` | Blue → Cyan → White | Low arousal |
| `matrix` | Dark Green → Bright Green | Neutral/tech |
| `plasma` | Multi-color with brightness pulse | Mixed |
| `ocean` | Deep Blue → Cyan → Sea White | Calm/oceanic |
| `fire` | Black → Dark Red → Orange → Bright Yellow | Intense/fiery |

Color scheme is auto-selected from VAD, but gradient names also influence final palette.

Color schemes also drive the **background fill** second render pass. Grammar selects a color scheme based on warmth/energy; the bg_fill pass maps char_idx intensity through this scheme to generate textured backgrounds (~750k unique combinations from 13 effects × variants × transforms × PostFX × masks × 8 color modes).
