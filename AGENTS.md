# viz - Market & Art ASCII Visualization Toolkit

A Python-based visualization system that generates stylized ASCII art images for market data, art news, and mood tracking. Produces Instagram-ready 1080x1080 PNG images with kaomoji, glitch effects, and emotional color schemes.

## Tech Stack

- **Language**: Python 3
- **Core Library**: Pillow (PIL) for image generation
- **External Dependency**: `/workspace/lib/kaomoji_library.py` (shared library)
- **Optional**: `/workspace/scripts/perplexity-search.sh` for news fetching

## Project Structure

```
viz/
├── universal_viz_system.py    # Main entry - multi-type visualization
├── market_viz_complete.py     # Market-specific with sentiment analysis
├── emotional_market_viz.py    # Emotion-driven design (5 moods)
├── stock_pixel_ascii.py       # Image-to-ASCII converter
├── procedural/                # Procedural generation engine
│   ├── engine.py              # Main procedural engine
│   ├── layers.py              # Layer composition system
│   ├── effects/               # Effect implementations
│   ├── core/                  # Core utilities
│   ├── palette.py             # Color palette management
│   ├── params.py              # Parameter definitions
│   ├── renderer.py            # Rendering pipeline
│   ├── types.py               # Type definitions
│   └── __init__.py            # Package initialization
├── lib/                       # Shared libraries
│   └── kaomoji_library.py     # Kaomoji graphics library
├── archive/                   # Archived/deprecated code
├── README.md                  # Chinese documentation
└── AGENTS.md                  # Code style guidelines
```

### 程序化生成引擎 (Procedural Engine)

`procedural/` 目录包含动态背景效果和视频生成系统：

- **engine.py** - 核心引擎，协调所有组件
- **layers.py** - 图层合成系统，支持多层效果叠加
- **effects/** - 效果实现（plasma, flame, wave, moire, sdf_shapes, noise_field）
- **renderer.py** - 渲染管道，输出 PNG 或 GIF
- **palette.py** - 颜色调色板管理
- **params.py** - 参数定义和验证
- **types.py** - 类型定义和数据结构

### CLI 规范

所有可视化工具使用 `argparse` 标准 CLI：

```python
import argparse

parser = argparse.ArgumentParser(description='...')
parser.add_argument('type', help='Visualization type')
parser.add_argument('--video', action='store_true', help='Output GIF video')
parser.add_argument('--effect', default='plasma', help='Background effect')
parser.add_argument('--duration', type=int, default=5, help='Video duration in seconds')
parser.add_argument('--fps', type=int, default=30, help='Frames per second')
parser.add_argument('--seed', type=int, help='Random seed for reproducibility')

args = parser.parse_args()
```

## Commands

### Run Visualizers

```bash
# Universal system (recommended entry point)
python3 viz/universal_viz_system.py <type> [query]
# Types: market, art, mood, news

# Examples
python3 viz/universal_viz_system.py market
python3 viz/universal_viz_system.py art "Venice Biennale"
python3 viz/universal_viz_system.py mood

# Market-specific
python3 viz/market_viz_complete.py "US stock market today"

# Emotional market (test emotions)
python3 viz/emotional_market_viz.py euphoria
python3 viz/emotional_market_viz.py panic

# Pixel-to-ASCII (test)
python3 viz/stock_pixel_ascii.py bull
python3 viz/stock_pixel_ascii.py bear
```

### No Build/Lint/Test

This is a script-based project with no formal build system, linter config, or test suite. Each `.py` file is standalone and executable.

## Code Style Guidelines

### Imports

```python
# Standard order: stdlib, then third-party, then local
import math
import random
import re
import subprocess
import sys
from datetime import datetime
from io import BytesIO

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

# Local imports with path manipulation (for shared libs)
sys.path.insert(0, '/workspace/lib')
from kaomoji_library import draw_kaomoji, get_moods_by_category
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Constants | SCREAMING_SNAKE_CASE | `COLOR_SCHEMES`, `ASCII_GRADIENT` |
| Functions | snake_case | `draw_glow_text`, `analyze_sentiment` |
| Variables | snake_case | `output_path`, `char_width` |
| Dict keys | snake_case strings | `'colors_bull'`, `'key_info'` |

### Type Hints

Not used in this codebase. Function parameters documented via docstrings instead.

### Docstrings

Use triple-quoted strings with Chinese + English mixed documentation:

```python
def generate_emotional_viz(market_data, output_path):
    """
    生成情绪化市场可视化
    
    market_data = {
        'emotion': 'euphoria' | 'excitement' | 'anxiety' | 'fear' | 'panic',
        'headline': '主标题',
        'metrics': ['指标1', '指标2', '指标3'],
        'timestamp': '时间',
        'change_pct': +2.5 (百分比变化)
    }
    """
```

### Constants & Configuration

Define configuration as module-level dicts:

```python
COLOR_SCHEMES = {
    'euphoria': {
        'bg': ['#000000', '#0a0000'],
        'primary': '#00ff00',
        'secondary': '#00ff88',
        'accent': '#ffff00',
        'glow': '#88ff88',
        'emotion': 'BULLISH'
    },
    # ...
}

ASCII_SYMBOLS = {
    'rocket': [
        '    /\\    ',
        '   /  \\   ',
        # Multi-line ASCII art as list of strings
    ],
}
```

### Image Generation Patterns

Standard canvas setup:

```python
WIDTH, HEIGHT = 1080, 1080  # Instagram square format
img = Image.new('RGB', (WIDTH, HEIGHT), colors['bg'])
draw = ImageDraw.Draw(img)
```

Text rendering with "glow" effect (draw multiple times with offset):

```python
def draw_glow_text(draw, x, y, text, color, glow_color, size=1):
    # Outer glow (multiple layers)
    for offset in range(size + 3, 0, -1):
        for dx in [-offset, 0, offset]:
            for dy in [-offset, 0, offset]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, fill=glow_color)
    # Main text (bold via multiple draws)
    for dx in range(size):
        for dy in range(size):
            draw.text((x + dx, y + dy), text, fill=color)
```

### Error Handling

Minimal - use try/except only for pixel manipulation:

```python
try:
    pixels[x + i, y] = pixels[x + i, (y + shift) % HEIGHT]
except:
    pass  # Silent fail for out-of-bounds
```

For subprocess calls, check return code:

```python
result = subprocess.run([...], capture_output=True, text=True, timeout=30)
return result.stdout if result.returncode == 0 else None
```

### Output Path Convention

Always use absolute paths with timestamp:

```python
output_path = f'/workspace/media/{content_type}_viz_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
```

### Main Entry Pattern

```python
if __name__ == "__main__":
    # Parse sys.argv
    if len(sys.argv) < 2:
        print("Usage: ...")
        sys.exit(1)
    
    # Execute main logic
    main()
```

## Key Patterns

### Sentiment Analysis

Simple keyword counting for market sentiment:

```python
bull_words = ['up', 'gain', 'rise', 'rally', 'surge', 'high', 'bull', 'positive', 'record']
bear_words = ['down', 'fall', 'drop', 'decline', 'crash', 'bear', 'negative', 'loss']

bull_count = sum(1 for word in bull_words if word in text_lower)
bear_count = sum(1 for word in bear_words if word in text_lower)

if bull_count > bear_count + 2:
    return 'bull'
elif bear_count > bull_count + 2:
    return 'bear'
return 'neutral'
```

### Glitch Effect

Applied for extreme emotions (euphoria/panic):

```python
if emotion in ['euphoria', 'panic']:
    pixels = img.load()
    for _ in range(glitch_intensity):
        x = random.randint(0, WIDTH - 80)
        y = random.randint(0, HEIGHT - 1)
        w = random.randint(20, 100)
        shift = random.randint(-12, 12)
        for i in range(w):
            if x + i < WIDTH and 0 <= (y + shift) < HEIGHT:
                try:
                    pixels[x + i, y] = pixels[x + i, (y + shift) % HEIGHT]
                except:
                    pass
```

### Post-Processing

Always apply sharpen + contrast enhancement:

```python
img = img.filter(ImageFilter.SHARPEN)
img = ImageEnhance.Contrast(img).enhance(1.4)
img.save(output_path, 'PNG', quality=95)
```

## Dependencies

Required pip packages:

```
Pillow>=9.0.0
requests  # Only for stock_pixel_ascii.py
```

## Output

- Format: PNG, quality=95
- Size: 1080x1080 pixels (Instagram square)
- Location: `/workspace/media/`
