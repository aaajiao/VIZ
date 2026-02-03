# VIZ Emotion Reference

Complete VAD (Valence-Arousal-Dominance) values for all 25 emotions.

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
| **panic** | -0.8 | 0.9 | -0.6 | High-energy negative |
| **fear** | -0.64 | 0.6 | -0.43 | High-energy negative |
| **anxiety** | -0.51 | 0.6 | -0.33 | High-energy negative |
| **anger** | -0.51 | 0.59 | 0.25 | High-energy negative |
| **volatile** | -0.1 | 0.8 | -0.2 | High-energy negative |
| **sadness** | -0.63 | -0.27 | -0.33 | Low-energy negative |
| **despair** | -0.8 | -0.4 | -0.7 | Low-energy negative |
| **melancholy** | -0.3 | -0.3 | -0.2 | Low-energy negative |
| **boredom** | -0.2 | -0.6 | -0.2 | Low-energy negative |
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
