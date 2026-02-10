---
name: viz-ascii-art
description: Generate 1080x1080 ASCII art visualizations with kaomoji, procedural effects, and emotion-driven styles. Use when users want to create visualizations, ASCII art images, emotion-based graphics, market mood images, or generate kaomoji art. Supports PNG, animated GIF, and MP4 output. Trigger words: visualization, ASCII art, kaomoji, emotion image, mood graphic, market visualization, generate viz.
metadata: {"openclaw": {"requires": {"bins": ["python3"]}, "emoji": "🎨", "homepage": "https://github.com/aaajiao/VIZ", "install": [{"id": "git", "kind": "download", "url": "https://github.com/aaajiao/VIZ", "label": "Clone VIZ repository"}]}}
---

# VIZ - ASCII Art Visualization Generator

VIZ is an AI-backend for generating emotion-driven ASCII art visualizations. AI handles intent, data, and content; VIZ renders.

## Installation (REQUIRED FIRST)

**Before using VIZ, ensure it is installed:**

```bash
# Check if VIZ is available
which viz.py || python3 -c "import viz" 2>/dev/null

# If not found, clone and install:
git clone https://github.com/aaajiao/VIZ.git ~/.local/share/viz
cd ~/.local/share/viz && pip install pillow

# Add to PATH (optional, for global access)
echo 'export VIZ_PATH="$HOME/.local/share/viz"' >> ~/.bashrc
```

**Dependency**: Only `pillow` (PIL) is required. No NumPy.

**After installation**, run VIZ commands from the VIZ directory:
```bash
cd ~/.local/share/viz  # or wherever VIZ is cloned
python3 viz.py generate --emotion joy
```

Or use absolute path:
```bash
python3 ~/.local/share/viz/viz.py generate --emotion joy
```

## Quick Start

```bash
# Minimal: just emotion
echo '{"emotion":"joy"}' | python3 viz.py generate

# Market data visualization
echo '{"source":"market","headline":"BTC $95K","emotion":"euphoria","metrics":["ETH: $4.2k"]}' | python3 viz.py generate

# Animated GIF
echo '{"emotion":"panic","video":true}' | python3 viz.py generate
```

## Input Protocol (JSON via stdin)

All fields are **optional**. VIZ auto-infers missing parameters.

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `emotion` | string | Emotion name (see list below) |
| `source` | string | Content source: `market` / `art` / `news` / `mood` |
| `headline` | string | Main headline text |
| `metrics` | list[string] | Data metrics (e.g., `["BTC: $92k", "ETH: $4.2k"]`) |
| `body` | string | Body text (fallback for emotion inference) |
| `title` | string | Overlay title |
| `timestamp` | string | Timestamp display |

### Advanced Fields

| Field | Type | Description |
|-------|------|-------------|
| `vad` | string/list | Direct VAD vector, e.g., `"0.8,0.5,0.3"` or `[0.8, 0.5, 0.3]` |
| `effect` | string | Background effect name |
| `seed` | int | Random seed (reproducible) |
| `layout` | string | Layout algorithm |
| `decoration` | string | Decoration style |
| `gradient` | string | ASCII gradient name |

### Output Control

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `video` | bool | false | Output GIF animation |
| `mp4` | bool | false | Also output MP4 (requires FFmpeg) |
| `duration` | float | 3.0 | GIF duration (seconds) |
| `fps` | int | 15 | Frames per second |
| `variants` | int | 1 | Generate multiple variants |

## Emotions (25 predefined)

Emotions are VAD (Valence-Arousal-Dominance) vectors in 3D space:

**High-energy positive**: `euphoria`, `excitement`, `joy`, `surprise`, `awe`
**Low-energy positive**: `calm`, `serenity`, `love`, `hope`, `trust`, `nostalgia`
**High-energy negative**: `panic`, `fear`, `anxiety`, `anger`, `volatile`
**Low-energy negative**: `sadness`, `despair`, `melancholy`, `boredom`
**Special**: `bull`, `bear`, `neutral`, `contempt`, `disgust`

### Emotion Priority
1. `emotion` field specified → use directly
2. `vad` field specified → use VAD vector
3. `headline` + `body` text → infer from keywords
4. None → default `neutral`

## Content Sources

Source determines visual vocabulary (particles, kaomoji style, atmosphere):

| Source | Particles | Kaomoji Style | Atmosphere |
|--------|-----------|---------------|------------|
| `market` | `$¥€₿↑↓▲▼` | bull/bear | HODL, PUMP / SELL, EXIT |
| `art` | `✦◆●▽△○◇` | love/thinking | CREATE, EXHIBIT |
| `news` | `►◆■●▶` | surprised/thinking | BREAKING, ALERT |
| `mood` | `·˚✧∘○◦` | all emotions | BREATHE, PEACE |

## Effects (17 types)

| Effect | Description | Best For |
|--------|-------------|----------|
| `plasma` | Plasma interference waves | High-energy emotions |
| `flame` | Doom-style fire | panic, anger |
| `wave` | Multi-frequency sine | Flowing feel |
| `moire` | Radial interference | Mysterious, psychedelic |
| `sdf_shapes` | Distance field geometry | Structural, modern |
| `noise_field` | Perlin-like noise | Organic, natural |
| `cppn` | Neural network patterns | Unique per seed |
| `ten_print` | C64 maze pattern (10 PRINT) | Retro, nostalgic |
| `game_of_life` | Conway's cellular automaton | Organic complexity |
| `donut` | Rotating 3D torus with lighting | Futuristic, technical |
| `mod_xor` | Bitwise fractal patterns | Mathematical, abstract |
| `wireframe_cube` | 3D rotating wireframe cube | Geometric, tech |
| `chroma_spiral` | Chromatic aberration spiral | Psychedelic, hypnotic |
| `wobbly` | Domain-warped fluid distortion | Dreamy, soft |
| `sand_game` | Falling sand particle sim | Meditative, calm |
| `slime_dish` | Physarum slime mold agents | Biological, organic |
| `dyna` | Moving attractor wave interference | Dynamic, energetic |

## Other Options

**Layouts**: `random_scatter`, `grid_jitter`, `spiral`, `force_directed`, `preset`

**Decorations**: `corners`, `edges`, `scattered`, `minimal`, `none`, `frame`, `grid_lines`, `circuit`

**Gradients**: `classic`, `smooth`, `matrix`, `plasma`, `blocks`, `glitch`, `circuit`, `cyber`, `organic`, etc.

**Blend modes** (for overlay): `ADD`, `SCREEN`, `OVERLAY`, `MULTIPLY`

## Output

**stdout JSON on success**:
```json
{
  "status": "ok",
  "results": [{"path": "media/viz_20260203_120000.png", "seed": 42, "format": "png"}],
  "emotion": "euphoria",
  "source": "market"
}
```

**On error**:
```json
{"status": "error", "message": "Invalid emotion name: xyz"}
```

## Examples

### Market Surge
```bash
echo '{
  "source": "market",
  "headline": "BTC BREAKS $100K",
  "emotion": "euphoria",
  "metrics": ["ETH: $5.2k", "SOL: $300"],
  "seed": 42
}' | python3 viz.py generate
```

### Art Exhibition
```bash
echo '{
  "source": "art",
  "headline": "Venice Biennale 2026",
  "emotion": "awe",
  "body": "immersive digital installations"
}' | python3 viz.py generate
```

### Panic Animation (GIF)
```bash
echo '{
  "source": "market",
  "headline": "MARKET CRASH",
  "emotion": "panic",
  "video": true,
  "duration": 5,
  "fps": 20
}' | python3 viz.py generate
```

### MP4 for Instagram (requires FFmpeg)
```bash
echo '{
  "source": "market",
  "headline": "BULL RUN",
  "emotion": "euphoria",
  "video": true,
  "mp4": true
}' | python3 viz.py generate
# → outputs both .gif and .mp4
```

### Direct VAD
```bash
echo '{
  "vad": [0.8, -0.3, 0.5],
  "headline": "Custom Emotion"
}' | python3 viz.py generate
```

### Multiple Variants
```bash
echo '{"emotion": "joy", "variants": 5}' | python3 viz.py generate
```

## Query Capabilities

AI can query all available options:
```bash
python3 viz.py capabilities --format json
```

Returns all emotions, effects, sources, layouts, decorations, gradients, and I/O schema.

## Output Specs

| Item | Value |
|------|-------|
| Format | PNG (quality=95), GIF, or MP4 (via FFmpeg) |
| Size | 1080 × 1080 pixels |
| Internal | 160 × 160 (nearest-neighbor upscale) |
| Default dir | `./media/` |
| Naming | `viz_{timestamp}.{png\|gif}` |

## Design Principles

1. **AI is brain, VIZ is paintbrush** — Data acquisition, content organization, emotion judgment by AI
2. **Loose input, deterministic output** — All fields optional, VIZ auto-infers
3. **Same input, infinite variations** — Same emotion + different seed = unique visuals
4. **Structured output** — stdout always JSON for parsing
5. **Reproducible** — Specify `seed` for exact reproduction
