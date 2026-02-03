# VIZ Effects Reference

Detailed documentation for all 7 procedural background effects.

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

Color scheme is auto-selected from VAD, but gradient names also influence final palette.
