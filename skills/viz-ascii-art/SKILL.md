---
name: viz-ascii-art
description: "Generate ASCII art visualizations with kaomoji, procedural effects, and emotion-driven styles. Renders 1080x1080 PNG/GIF/MP4 (variable resolution up to 3840px). Use when users want to create visualizations, ASCII art, emotion-based graphics, or kaomoji art."
---

# VIZ ASCII Art Generator

AI handles intent, data, and emotion; VIZ renders ASCII art.

Preferred CLI: `viz` (installed via `pip install aaajiao-viz`). Repo-local fallback: `python3 viz.py`.

## Protocol

```bash
echo '<JSON>' | viz generate --output-dir <dir>
```

`--output-dir` is **required** for both `generate` and `convert`.

### Input (JSON via stdin, all fields optional)

| Field | Type | Description |
|-------|------|-------------|
| `emotion` | string | One of 26 emotions (run `viz capabilities` to list) |
| `headline` | string | Main text overlay |
| `metrics` | list[str] | Data lines |
| `body` | string | Body text (fallback for emotion inference) |
| `title` | string | Title overlay |
| `vad` | str/list | Direct VAD vector `[V,A,D]` each -1 to +1, bypasses emotion name |
| `effect` | string | Background effect name |
| `seed` | int | Reproducibility seed -- **vary it**, don't always use 42 |
| `video` | bool | Output GIF animation |
| `mp4` | bool | Also output MP4 (requires FFmpeg) |
| `width` / `height` | int | Output size 120-3840px (default 1080) |
| `variants` | int | Generate N variants with different seeds |

More fields (overlay, color_scheme, palette, transforms, postfx, composition, mask, variant, params, vocabulary) available for advanced control. See **references/** for details.

### Output (stdout JSON)

**Success** (exit code 0):
```json
{"status":"ok","results":[{"path":"./runs/out/viz_20260203_s42.png","seed":42,"format":"png"}],"emotion":"euphoria","resolution":[1080,1080]}
```

**Success with sanitization warnings** (exit code 0):
```json
{"status":"ok","results":[...],"warnings":["duration clamped from 100.0 to 30.0 (range 0.1-30.0)"]}
```

**Error** (exit code 1):
```json
{"status":"error","message":"Invalid --vad: vad requires exactly 3 values (V,A,D), got 2"}
```

Always check **both** exit code and `status` field.

### Discover Options at Runtime

```bash
viz capabilities --format json
```

Returns all available emotions, effects, gradients, color schemes, layouts, decorations, transforms, postfx, masks, composition modes, variants, and input/output schemas. **Prefer this over hardcoded lists** -- it reflects the installed version.

## Quick Examples

```bash
# Minimal
echo '{"emotion":"joy"}' | viz generate --output-dir ./runs/joy

# Market data
echo '{"headline":"BTC $95K","emotion":"euphoria","metrics":["ETH: $4.2k"]}' | viz generate --output-dir ./runs/market

# Animated GIF
echo '{"emotion":"panic","video":true,"duration":3}' | viz generate --output-dir ./runs/panic

# Director Mode -- precise control over composition
echo '{"emotion":"euphoria","effect":"plasma","variant":"warped","transforms":[{"type":"kaleidoscope","segments":6}],"postfx":[{"type":"vignette","strength":0.5}],"composition":"radial_masked"}' | viz generate --output-dir ./runs/director
```

## References (load on demand)

| File | When to load |
|------|-------------|
| **references/EMOTIONS.md** | Need VAD values for all 26 emotions or custom VAD usage |
| **references/EFFECTS.md** | Need effect parameters, ranges, or overlay/blend details |
| **references/COMPOSITION.md** | Need Director Mode: transforms, postfx, masks, variants, deformation params |
| **references/VISUAL_OPTIONS.md** | Need layouts, decorations, gradients, color schemes, vocabulary overrides |
| **references/EXAMPLES.md** | Need complete worked examples for various use cases |
