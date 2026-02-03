# VIZ Usage Examples

Complete examples for common use cases.

## Market Visualizations

### Bull Market Celebration

```json
{
  "source": "market",
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
  "source": "market",
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
  "source": "market",
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
  "source": "art",
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
  "source": "art",
  "headline": "Summer Memories",
  "emotion": "nostalgia",
  "effect": "noise_field",
  "gradient": "organic"
}
```

### Love Letter

```json
{
  "source": "art",
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
  "source": "news",
  "headline": "BREAKING: Major Policy Change",
  "emotion": "surprise",
  "body": "Federal Reserve announces unexpected rate decision",
  "effect": "plasma"
}
```

### Crisis Alert

```json
{
  "source": "news",
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
  "source": "mood",
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
  "source": "mood",
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
  "source": "mood",
  "emotion": "hope",
  "headline": "Things Will Get Better",
  "effect": "wave",
  "gradient": "smooth"
}
```

---

## Advanced Techniques

### Custom VAD (Fine-tuned Emotion)

When predefined emotions don't match, specify exact VAD:

```json
{
  "vad": [0.3, 0.7, -0.2],
  "headline": "Excited but Uncertain",
  "source": "mood"
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
  --source market \
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
