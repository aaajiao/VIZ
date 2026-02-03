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

## Flexible Output System (千变万化)

打破刚性的一一对应映射，实现从同一输入生成无限视觉变体。

### 设计理念

```
旧系统: 文本 → 3 个离散类别 → 固定效果 → 固定配色 → ~3 种输出
新系统: 文本 → VAD 连续向量 → 文法组合 → 噪声调制 → 无限输出
```

### 快速使用

```bash
# 从文本生成（自动推断情绪）
python3 viz/demo_flexible.py --text "market crash fears rising"

# 从情绪名称生成
python3 viz/demo_flexible.py --emotion euphoria

# 同一输入，不同种子 = 不同变体
python3 viz/demo_flexible.py --text "hope" --variants 5

# 生成动画
python3 viz/demo_flexible.py --emotion joy --video --duration 3

# 指定 VAD 向量 (valence,arousal,dominance)
python3 viz/demo_flexible.py --vad 0.5,-0.3,0.2

# 分析文本的 VAD 向量（不生成图片）
python3 viz/demo_flexible.py --analyze --text "暴涨 狂热 突破"

# 列出所有预定义情绪
python3 viz/demo_flexible.py --list-emotions
```

### Python API

```python
from procedural.flexible import FlexiblePipeline, EmotionVector

pipe = FlexiblePipeline(seed=42)

# 方式 1: 从文本
img = pipe.generate(text="市场暴跌 恐慌蔓延")

# 方式 2: 从情绪名称
img = pipe.generate(emotion="euphoria")

# 方式 3: 从 VAD 向量（精确控制）
ev = EmotionVector(valence=-0.5, arousal=0.8, dominance=-0.3)
img = pipe.generate(emotion_vector=ev)

# 方式 4: 批量变体（同一情绪，不同诠释）
variants = pipe.generate_variants(text="hope", count=10)

# 方式 5: 动画
pipe.generate_video(emotion="calm", duration=3.0, output_path="out.gif")
```

### 核心模块

| 模块 | 作用 | 替代 |
|------|------|------|
| `EmotionVector` | VAD 三维连续情感空间 (24 种锚点情绪) | 旧系统 3 个离散类别 |
| `ContinuousColorSpace` | warmth/saturation/brightness 连续配色 | 旧系统 5 种固定调色板 |
| `NoiseModulator` | 噪声驱动参数漂移 + Domain Warping | 旧系统静态参数 |
| `VisualGrammar` | 概率产生式规则组合场景 | 旧系统固定效果映射 |
| `CPPNEffect` | 神经网络生成唯一图案 (每个种子不同) | 旧系统 6 种效果 |
| `FlexiblePipeline` | 编排所有模块的统一管线 | 旧系统各脚本独立 |

### VAD 情感模型

每种情绪是三维空间中的一个点，而非离散标签：

| 维度 | 范围 | 含义 |
|------|------|------|
| **Valence** (效价) | -1 ↔ +1 | 消极 ↔ 积极 |
| **Arousal** (唤醒度) | -1 ↔ +1 | 平静 ↔ 激动 |
| **Dominance** (支配度) | -1 ↔ +1 | 顺从 ↔ 掌控 |

情感向量直接驱动视觉参数——高 Arousal 提升频率和速度，高 Valence 偏向暖色，高 Dominance 增加结构性。中间地带产生旧系统无法表达的微妙情绪（如"淡淡的焦虑"或"冷静的愉悦"）。

### 多样性来源

| 维度 | 变化数量 | 机制 |
|------|---------|------|
| 背景效果 | 7 种 (含 CPPN) | 文法概率选择 |
| 叠加效果 | 0-1 层 × 6 种 | 概率触发 |
| 混合模式 | 4 种 | ADD/SCREEN/OVERLAY/MULTIPLY |
| 布局算法 | 5 种 | scatter/grid/spiral/force/preset |
| ASCII 梯度 | 5 种 | classic/blocks/smooth/matrix/plasma |
| 装饰风格 | 5 种 × 12 种字符 | 概率选择 |
| 连续参数 | ∞ | 情绪驱动 + 噪声调制 |
| **组合总数** | **235,000+ 离散 × ∞ 连续** | |

---

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
| `cppn` | 神经网络生成图案 | num_hidden, layer_size, seed |

### 动态布局算法

| 算法 | 描述 |
|------|------|
| `random_scatter` | 均匀随机分布 |
| `grid_with_jitter` | 网格 + 随机抖动 |
| `spiral_layout` | 费马螺旋 |
| `force_directed` | 力导向布局（斥力模型） |

### 效果混合

支持多层效果叠加（可嵌套），可用模式：
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

# 支持嵌套: 三层效果
noise = get_effect('noise_field')
triple = CompositeEffect(composite, noise, BlendMode.ADD, mix=0.3)
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

20 个情绪分类，300+ 个独特颜文字，覆盖从狂喜到恐慌的完整情感光谱。

### 情绪分类

**正面情绪 (Positive)**

| 分类 | 示例 | 描述 |
|------|------|------|
| `happy` | (◠‿◠) (◕‿◕) (⌒‿⌒) | 开心、愉悦 |
| `euphoria` | \\(≧∇≦)/ ヽ(>∀<☆)ノ (ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ | 狂喜、极度兴奋 |
| `excitement` | (*^_^*) ヾ(^▽^)ノ ♪(´▽｀) | 兴奋、活力 |
| `love` | (♡˙︶˙♡) (◕‿◕)♡ (灬♥ω♥灬) | 爱意、心动 |
| `proud` | (•̀ᴗ•́)و (`・ω・´) (⌐■_■) | 自豪、得意 |
| `relaxed` | (´ー`) (◡‿◡✿) ( ˘ω˘ ) | 放松、惬意 |

**负面情绪 (Negative)**

| 分类 | 示例 | 描述 |
|------|------|------|
| `sad` | (ಥ_ಥ) (╥﹏╥) (ノД`)・゜・。 | 悲伤、难过 |
| `angry` | (╬ Ò﹏Ó) (ノಠ益ಠ)ノ ヽ(`Д´)ノ | 愤怒、暴躁 |
| `anxiety` | (´；ω；`) (°△°\|\|\|) (⊙﹏⊙) | 焦虑、不安 |
| `fear` | Σ(°△°\|\|\|)︴ ((((；゜Д゜))) (ʘᗩʘ') | 恐惧、害怕 |
| `panic` | (×_×;） (✖╭╮✖) Σ(ﾟДﾟ;≡;ﾟдﾟ) | 恐慌、崩溃 |
| `disappointed` | (ー_ー)!! ┐(´д`)┌ (；￣Д￣) | 失望、沮丧 |
| `lonely` | (◞‸◟) (ノω・、) (•̩̩̩̩_•̩̩̩̩) | 孤独、寂寞 |

**中性 / 其他 (Neutral / Other)**

| 分类 | 示例 | 描述 |
|------|------|------|
| `neutral` | (._.) (-_-) (・_・) | 平静、无表情 |
| `confused` | (？_？) (•ิ_•ิ)? щ(゜ロ゜щ) | 困惑、疑问 |
| `surprised` | Σ(ﾟДﾟ) (ﾟoﾟ) w(°o°)w | 惊讶、吃惊 |
| `sleepy` | (=_=) zzZ (-.-)Zzz・・・ (_ _).。o○ | 困倦、想睡 |
| `thinking` | ( ˘_˘ ) (◔_◔) ( ˇ‸ˇ ) | 思考、沉思 |
| `embarrassed` | (〃▽〃) (*/ω＼*) (*ﾉ▽ﾉ) | 害羞、尴尬 |
| `bored` | (￢_￢) ( ´_ゝ`) (-_-)旦~ | 无聊、厌倦 |

**经典别名**: `bull` (= happy 精选) / `bear` (= sad 精选)，向后兼容。

### 架构

```
kaomoji_data.py (唯一数据源: 20 分类 × 15 颜文字)
     ↓ import
kaomoji.py (渲染器: 精确匹配优先 → 父类兜底)
     ↓ draw_kaomoji()
layers.py (KaomojiSprite 精灵 + 动画)
     ↓
pipeline.py (6 档效价梯度 → 细分情绪选择)
```

渲染策略：传入 `mood="love"` 时直接命中 love 分类的 15 个专属颜文字，而非被压缩到 bull 的 5 个。

### 用法

```python
from lib.kaomoji import draw_kaomoji
from lib.kaomoji_data import KAOMOJI_SINGLE, get_kaomoji

# 绘制颜文字（size 1-50 可读）
draw_kaomoji(draw, x, y, 'love', color, outline_color, size=20)

# 获取特定情绪的颜文字列表
faces = get_kaomoji('embarrassed', format='single')  # 15 个害羞颜文字

# 经典用法仍然有效
draw_kaomoji(draw, x, y, 'bull', color, outline_color, size=20)
```

## 项目结构

```
viz/
├── demo_flexible.py               # Flexible Output System 演示脚本
├── universal_viz_system.py        # 主入口 - CLI 统一接口
├── market_viz_complete.py         # 市场专用版
├── emotional_market_viz.py        # 情绪化设计版
├── stock_pixel_ascii.py           # 图像转 ASCII
├── lib/
│   ├── kaomoji.py                 # 颜文字绘制（draw_kaomoji）
│   ├── kaomoji_data.py            # 颜文字数据（单行格式）
│   └── effects.py                 # 发光文字、故障效果
├── procedural/                    # 程序化生成引擎
│   ├── engine.py                  # 渲染编排器
│   ├── layers.py                  # 精灵动画系统
│   ├── layouts.py                 # 动态布局算法
│   ├── compositor.py              # 效果混合器（支持嵌套）
│   ├── params.py                  # 参数随机化
│   ├── effects/                   # 可插拔效果
│   │   ├── plasma.py, flame.py, wave.py, moire.py...
│   ├── core/                      # 数学原语
│   │   ├── vec.py, sdf.py, noise.py, mathx.py
│   └── flexible/                  # 千变万化输出系统
│       ├── emotion.py             # VAD 连续情感空间
│       ├── color_space.py         # 连续颜色空间
│       ├── modulator.py           # 噪声参数调制器
│       ├── grammar.py             # 随机视觉文法
│       ├── cppn.py                # CPPN 神经网络图案
│       └── pipeline.py            # 柔性管线编排器
└── archive/                       # 已弃用 - 仅供参考
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
