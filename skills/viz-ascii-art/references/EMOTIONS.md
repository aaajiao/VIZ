# VIZ Emotion Reference

Complete VAD (Valence-Arousal-Dominance) values for all 34 emotions.

| Emotion | Valence | Arousal | Dominance | Category |
|---------|---------|---------|-----------|----------|
| **euphoria** | 0.9 | 0.85 | 0.6 | High-energy positive |
| **excitement** | 0.62 | 0.75 | 0.38 | High-energy positive |
| **joy** | 0.76 | 0.48 | 0.35 | High-energy positive |
| **surprise** | 0.4 | 0.67 | -0.13 | High-energy positive |
| **awe** | 0.5 | 0.55 | -0.3 | High-energy positive |
| **calm** | 0.3 | -0.6 | 0.2 | Low-energy positive |
| **serenity** | 0.5 | -0.4 | 0.3 | Low-energy positive |
| **love** | 0.85 | 0.35 | 0.25 | Low-energy positive |
| **hope** | 0.55 | 0.2 | 0.15 | Low-energy positive |
| **trust** | 0.6 | -0.1 | 0.4 | Low-energy positive |
| **nostalgia** | 0.2 | -0.2 | -0.1 | Low-energy positive |
| **contentment** | 0.45 | -0.35 | 0.30 | Low-energy positive |
| **gratitude** | 0.65 | -0.25 | 0.15 | Low-energy positive |
| **peace** | 0.40 | -0.55 | 0.35 | Low-energy positive |
| **satisfaction** | 0.55 | -0.45 | 0.45 | Low-energy positive |
| **panic** | -0.8 | 0.9 | -0.6 | High-energy negative |
| **fear** | -0.64 | 0.72 | -0.43 | High-energy negative |
| **anxiety** | -0.51 | 0.50 | -0.33 | High-energy negative |
| **anger** | -0.51 | 0.42 | 0.25 | High-energy negative |
| **rage** | -0.70 | 0.80 | 0.40 | High-energy negative |
| **volatile** | -0.1 | 0.8 | -0.2 | High-energy negative |
| **sadness** | -0.63 | -0.27 | -0.33 | Low-energy negative |
| **despair** | -0.8 | -0.4 | -0.7 | Low-energy negative |
| **melancholy** | -0.3 | -0.3 | -0.2 | Low-energy negative |
| **boredom** | -0.2 | -0.6 | -0.2 | Low-energy negative |
| **resignation** | -0.40 | -0.50 | -0.45 | Low-energy negative |
| **apathy** | -0.15 | -0.70 | -0.35 | Low-energy negative |
| **loneliness** | -0.55 | -0.45 | -0.50 | Low-energy negative |
| **wistfulness** | -0.20 | -0.35 | -0.15 | Low-energy negative |
| **bull** | 0.7 | 0.5 | 0.4 | Special (market) |
| **bear** | -0.6 | 0.4 | -0.3 | Special (market) |
| **neutral** | 0.0 | -0.1 | 0.0 | Special |
| **contempt** | -0.4 | 0.1 | 0.5 | Special |
| **disgust** | -0.6 | 0.35 | 0.2 | Special |

## VAD Dimensions

- **Valence** (-1 to +1): Negative ↔ Positive
- **Arousal** (-1 to +1): Calm ↔ Excited
- **Dominance** (-1 to +1): Submissive ↔ Dominant

## Custom VAD

Specify directly via `vad` field:
```json
{"vad": [0.8, -0.3, 0.5]}
// or
{"vad": "0.8,-0.3,0.5"}
```
