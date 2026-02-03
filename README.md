# viz - ASCII Art Visualization Toolkit

ASCII 艺术可视化工具集，用于市场数据、艺术新闻和心情追踪。生成 1080x1080 PNG/GIF 图像，支持颜文字、故障效果和情绪化配色。

灵感来源：[play.ertdfgcvb.xyz](https://play.ertdfgcvb.xyz) - 基于文本的实时代码环境

## 快速开始

```bash
# 生成静态图像
python3 viz/universal_viz_system.py mood --seed 42

# 生成带动画的 GIF
python3 viz/universal_viz_system.py mood --video --duration 3 --fps 15

# 生成情绪化可视化
python3 viz/emotional_market_viz.py euphoria --seed 42
```

## 核心工具

### `universal_viz_system.py` - 通用系统

支持多种内容类型的统一可视化系统。

```bash
python3 viz/universal_viz_system.py <类型> [查询] [选项]
```

**支持类型：**
| 类型 | 描述 | 示例 |
|------|------|------|
| `market` | 市场与经济 | `python3 viz/universal_viz_system.py market` |
| `art` | 艺术与文化 | `python3 viz/universal_viz_system.py art "Venice Biennale"` |
| `mood` | 个人心情 | `python3 viz/universal_viz_system.py mood` |
| `news` | 通用新闻 | `python3 viz/universal_viz_system.py news "AI"` |

**选项：**
| 参数 | 默认值 | 描述 |
|------|--------|------|
| `--video` | false | 输出 GIF 视频而非静态图片 |
| `--duration N` | 5 | 视频时长（秒） |
| `--fps N` | 15 | 帧率 |
| `--effect NAME` | plasma | 背景效果 |
| `--seed N` | random | 随机种子（可复现结果） |

### `emotional_market_viz.py` - 情绪化设计版

基于情绪心理学的可视化设计，5 种情绪状态：

| 情绪 | 配色 | 效果 |
|------|------|------|
| `euphoria` | 纯绿 | 故障效果 + 呼吸动画 |
| `excitement` | 矩阵绿 | 浮动动画 |
| `anxiety` | 橙色 | 闪电装饰 |
| `fear` | 红色 | 下箭头 |
| `panic` | 血红 | 强故障效果 |

```bash
python3 viz/emotional_market_viz.py <emotion> [--seed N] [--video]
```

### `market_viz_complete.py` - 市场专用版

专门针对市场数据优化，自动获取新闻并分析情绪。

```bash
python3 viz/market_viz_complete.py "US stock market today"
```

### `stock_pixel_ascii.py` - 像素转 ASCII

将真实图像逐像素转换为 ASCII 艺术。

```python
from viz.stock_pixel_ascii import generate_stock_ascii_viz

generate_stock_ascii_viz(
    source_image='path/to/image.png',
    market_data={...},
    output_path='output.png',
    emotion='bull'
)
```

## 程序化生成引擎

### 可用效果

| 效果 | 描述 | 参数 |
|------|------|------|
| `plasma` | 等离子体干涉波纹 | frequency, speed, color_phase |
| `flame` | Doom 风格火焰 | intensity |
| `wave` | 多频率正弦叠加 | wave_count, frequency, amplitude |
| `moire` | 径向莫尔干涉 | freq_a, freq_b, speed_a, speed_b |
| `sdf_shapes` | 有符号距离场形状 | shape_count, radius, smoothness |
| `noise_field` | Perlin 噪声场 | scale, octaves, lacunarity |

### 动态布局算法

| 算法 | 描述 |
|------|------|
| `random_scatter` | 均匀随机分布 |
| `grid_with_jitter` | 网格 + 随机抖动 |
| `spiral_layout` | 费马螺旋 |
| `force_directed` | 力导向布局（斥力模型） |

### 效果混合

支持两个效果的混合，可用模式：
- `ADD` - 加法混合
- `MULTIPLY` - 乘法混合
- `SCREEN` - 滤色混合
- `OVERLAY` - 叠加混合

```python
from procedural.compositor import CompositeEffect, BlendMode
from procedural.effects import get_effect

plasma = get_effect('plasma')
wave = get_effect('wave')
composite = CompositeEffect(plasma, wave, BlendMode.SCREEN, mix=0.5)
```

## 精灵动画

视频模式下支持以下动画效果：

| 动画 | 描述 | 参数 |
|------|------|------|
| `breathing` | 呼吸缩放 | amp (幅度), speed (速度) |
| `floating` | 上下浮动 | amp (像素), speed, phase |
| `color_cycle` | 色相循环 | base_hue, speed, saturation |

```python
from procedural.layers import KaomojiSprite, TextSprite

sprite = KaomojiSprite('bull', x=100, y=100, animations=[
    {'type': 'breathing', 'amp': 0.1, 'speed': 2.0},
    {'type': 'floating', 'amp': 15, 'speed': 1.0}
])
```

## 颜文字系统

### 支持的情绪

| 情绪 | 示例 |
|------|------|
| `bull` | (^o^), (≧▽≦), \(^o^)/ |
| `bear` | (;_;), (x_x), (╥﹏╥) |
| `neutral` | (._.), (o_o), (-_-) |
| `euphoria` | ٩(◕‿◕)۶, ☆*:.｡.o(≧▽≦)o.｡.:*☆ |
| `panic` | (ﾟДﾟ;), Σ(°△°|||) |

### 用法

```python
from lib.kaomoji import draw_kaomoji
from lib.kaomoji_data import KAOMOJI_SINGLE, get_kaomoji

# 绘制颜文字（size 1-50 可读）
draw_kaomoji(draw, x, y, 'bull', color, outline_color, size=20)

# 获取单行颜文字
face = get_kaomoji('euphoria', format='single')
```

## 项目结构

```
viz/
├── universal_viz_system.py    # 主入口 - CLI 统一接口
├── market_viz_complete.py     # 市场专用版
├── emotional_market_viz.py    # 情绪化设计版
├── stock_pixel_ascii.py       # 图像转 ASCII
├── lib/
│   ├── kaomoji.py             # 颜文字绘制（draw_kaomoji）
│   ├── kaomoji_data.py        # 颜文字数据（单行格式）
│   └── effects.py             # 发光文字、故障效果
├── procedural/                # 程序化生成引擎
│   ├── engine.py              # 渲染编排器
│   ├── layers.py              # 精灵动画系统
│   ├── layouts.py             # 动态布局算法
│   ├── compositor.py          # 效果混合器
│   ├── params.py              # 参数随机化
│   ├── effects/               # 可插拔效果
│   │   ├── plasma.py, flame.py, wave.py...
│   └── core/                  # 数学原语
│       ├── vec.py, sdf.py, noise.py, mathx.py
└── archive/                   # 已弃用 - 仅供参考
```

## 依赖

```
Pillow>=9.0.0
requests  # 可选，用于 stock_pixel_ascii.py
```

## 输出

- **格式**: PNG (quality=95) 或 GIF
- **尺寸**: 1080x1080 像素
- **位置**: `/workspace/media/`

## 可复现性

使用 `--seed` 参数确保相同输入产生相同输出：

```bash
# 两次运行产生完全相同的结果
python3 viz/universal_viz_system.py mood --seed 42
python3 viz/universal_viz_system.py mood --seed 42

# 不同 seed 产生不同结果
python3 viz/universal_viz_system.py mood --seed 99
```

## 示例

### 生成市场可视化

```bash
# 静态图像
python3 viz/universal_viz_system.py market --seed 42

# 带火焰效果的视频
python3 viz/universal_viz_system.py market --video --effect flame --duration 5
```

### 生成情绪化可视化

```bash
# 狂喜状态（带故障效果）
python3 viz/emotional_market_viz.py euphoria --seed 42

# 恐慌状态（血红配色）
python3 viz/emotional_market_viz.py panic --video --duration 3
```

### 程序化使用

```python
from procedural import Engine
from procedural.effects import get_effect
from procedural.layers import KaomojiSprite, TextSprite

# 创建引擎
engine = Engine(internal_size=(160, 160), output_size=(1080, 1080))
effect = get_effect('plasma')

# 创建精灵
sprites = [
    KaomojiSprite('bull', x=80, y=80, animations=[
        {'type': 'breathing', 'amp': 0.1}
    ]),
    TextSprite('MARKET', x=80, y=20, color='#00ff00')
]

# 渲染视频
frames = engine.render_video(effect, duration=3.0, fps=15, sprites=sprites, seed=42)
engine.save_gif(frames, '/workspace/media/output.gif', fps=15)
```

## 一键发布

使用 `scripts/post_market_viz.sh` 自动生成并发布到 Instagram。

## 参考

- [play.ertdfgcvb.xyz](https://play.ertdfgcvb.xyz) - 灵感来源
- [play.core](https://github.com/ertdfgcvb/play.core) - 核心参考实现
