# VIZ Usage Examples

Complete examples for common use cases.

## Market Visualizations

### Bull Market Celebration

```json
{
  "headline": "BTC BREAKS $100K",
  "emotion": "euphoria",
  "metrics": ["ETH: $5.2k", "SOL: $300", "Volume: $89B"],
  "effect": "plasma",
  "seed": 42
}
```

### Bear Market Warning

```json
{
  "headline": "MARKET CRASH -15%",
  "emotion": "panic",
  "metrics": ["BTC: -12%", "ETH: -18%", "Fear Index: 95"],
  "effect": "flame",
  "video": true,
  "duration": 5,
  "fps": 20
}
```

### Volatile Trading Day

```json
{
  "headline": "WILD SWINGS",
  "emotion": "volatile",
  "metrics": ["High: $98k", "Low: $82k", "Range: 16%"],
  "effect": "moire"
}
```

---

## Art & Creative

### Exhibition Announcement

```json
{
  "headline": "Venice Biennale 2026",
  "emotion": "awe",
  "body": "immersive digital installations exploring human-AI collaboration",
  "effect": "cppn",
  "decoration": "minimal"
}
```

### Nostalgic Memory

```json
{
  "headline": "Summer Memories",
  "emotion": "nostalgia",
  "effect": "noise_field",
  "gradient": "organic"
}
```

### Love Letter

```json
{
  "emotion": "love",
  "title": "For You",
  "effect": "wave",
  "decoration": "scattered"
}
```

---

## News & Alerts

### Breaking News

```json
{
  "headline": "BREAKING: Major Policy Change",
  "emotion": "surprise",
  "body": "Federal Reserve announces unexpected rate decision",
  "effect": "plasma"
}
```

### Crisis Alert

```json
{
  "headline": "EMERGENCY ALERT",
  "emotion": "fear",
  "effect": "flame",
  "video": true
}
```

---

## Mood & Personal

### Morning Calm

```json
{
  "emotion": "calm",
  "title": "Sunday Morning",
  "effect": "noise_field",
  "gradient": "organic",
  "decoration": "minimal"
}
```

### Anxiety Journal

```json
{
  "emotion": "anxiety",
  "body": "racing thoughts, can't focus",
  "effect": "moire",
  "video": true,
  "duration": 3
}
```

### Hope & Recovery

```json
{
  "emotion": "hope",
  "headline": "Things Will Get Better",
  "effect": "wave",
  "gradient": "smooth"
}
```

---

## New Effects Showcase

### Retro Maze (10 PRINT)

```json
{
  "headline": "RETRO COMPUTING",
  "emotion": "nostalgia",
  "effect": "ten_print",
  "params": {"cell_size": 8, "probability": 0.5}
}
```

### Game of Life

```json
{
  "headline": "EMERGENCE",
  "emotion": "awe",
  "effect": "game_of_life",
  "video": true,
  "duration": 5
}
```

### 3D Donut

```json
{
  "headline": "DIGITAL SCULPTURE",
  "emotion": "excitement",
  "effect": "donut",
  "video": true
}
```

### Fractal Math

```json
{
  "headline": "ALGORITHMIC BEAUTY",
  "emotion": "surprise",
  "effect": "mod_xor",
  "params": {"modulus": 32, "operation": "xor"}
}
```

### Wireframe Geometry

```json
{
  "headline": "TECH FORWARD",
  "emotion": "trust",
  "effect": "wireframe_cube",
  "video": true
}
```

### Psychedelic Spiral

```json
{
  "emotion": "euphoria",
  "effect": "chroma_spiral",
  "params": {"arms": 5, "chroma_offset": 0.2},
  "video": true
}
```

### Dreamy Fluid

```json
{
  "headline": "DRIFTING",
  "emotion": "serenity",
  "effect": "wobbly",
  "gradient": "organic"
}
```

### Falling Sand Meditation

```json
{
  "emotion": "calm",
  "effect": "sand_game",
  "video": true,
  "duration": 5,
  "fps": 15
}
```

### Slime Mold Network

```json
{
  "headline": "LIVING SYSTEMS",
  "emotion": "awe",
  "effect": "slime_dish",
  "video": true
}
```

### Dynamic Energy

```json
{
  "headline": "MOMENTUM",
  "emotion": "excitement",
  "effect": "dyna",
  "params": {"attractor_count": 6}
}
```

---

## Composition & Deformation

### Alien Donut (deformation params)

```json
{
  "effect": "donut",
  "emotion": "awe",
  "params": {"surface_noise": 0.6, "twist": 1.5, "asymmetry_x": 1.5}
}
```

### Warped Plasma

```json
{
  "effect": "plasma",
  "emotion": "euphoria",
  "params": {"self_warp": 0.5, "noise_injection": 0.3}
}
```

### Multi-Center Moire

```json
{
  "effect": "moire",
  "emotion": "volatile",
  "params": {"distortion": 0.4, "multi_center": 3}
}
```

### Deformed Wireframe

```json
{
  "effect": "wireframe_cube",
  "emotion": "anxiety",
  "params": {"vertex_noise": 0.5, "morph": 0.6}
}
```

### Multi-Center Spiral

```json
{
  "effect": "chroma_spiral",
  "emotion": "excitement",
  "params": {"multi_center": 3, "distortion": 0.3, "arms": 5}
}
```

Note: Domain transforms (mirror, kaleidoscope, tile), PostFX (vignette, scanlines, edge detect), spatial masks, and structural variants are auto-selected by the grammar system. No need to specify them manually.

---

## Advanced Techniques

### Custom VAD (Fine-tuned Emotion)

When predefined emotions don't match, specify exact VAD:

```json
{
  "vad": [0.3, 0.7, -0.2],
  "headline": "Excited but Uncertain"
}
```

VAD ranges: Valence (-1 to +1), Arousal (-1 to +1), Dominance (-1 to +1)

### Effect Overlay

Layer two effects together:

```json
{
  "emotion": "serenity",
  "effect": "noise_field",
  "overlay": {
    "effect": "wave",
    "blend": "SCREEN",
    "mix": 0.25
  }
}
```

### Multiple Variants

Generate 5 variations with different seeds:

```json
{
  "emotion": "joy",
  "headline": "Celebration",
  "variants": 5
}
```

Output: 5 PNG files with seeds 1-5, same emotion but different visual arrangements.

### Reproducible Output

Lock the exact output with seed:

```json
{
  "emotion": "euphoria",
  "seed": 12345
}
```

Same seed + same input = identical output every time.

---

## CLI Alternative

All JSON fields can also be passed via CLI args:

```bash
# Equivalent to JSON example
python3 viz.py generate \
  --emotion euphoria \
  --headline "BTC BREAKS 100K" \
  --metrics "ETH: $5.2k" "SOL: $300" \
  --seed 42

# Animation
python3 viz.py generate \
  --emotion panic \
  --video \
  --duration 5 \
  --fps 20
```

CLI args override stdin JSON values if both provided.

---

## Output Handling

### Parse stdout JSON

```python
import subprocess
import json

result = subprocess.run(
    ['python3', 'viz.py', 'generate'],
    input='{"emotion": "joy"}',
    capture_output=True,
    text=True
)

output = json.loads(result.stdout)
if output['status'] == 'ok':
    image_path = output['results'][0]['path']
    print(f"Generated: {image_path}")
```

### Batch Generation

```bash
for emotion in joy fear calm panic; do
  echo "{\"emotion\": \"$emotion\"}" | python3 viz.py generate
done
```
