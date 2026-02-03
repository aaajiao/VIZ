# viz - ASCII Art Visualization Toolkit

ASCII 艺术可视化工具集，生成 1080x1080 PNG/GIF 图像，支持颜文字、程序化效果和情绪驱动的视觉风格。纯 Python 3 + Pillow，无构建系统。

灵感来源：[play.ertdfgcvb.xyz](https://play.ertdfgcvb.xyz) - 基于文本的实时代码环境

## 快速开始

```bash
# 生成可视化（纯视觉，情绪驱动）
python3 viz.py generate --emotion euphoria --seed 42

# AI 集成：通过 stdin JSON 传入内容数据
echo '{"source":"market","headline":"DOW +600","emotion":"bull","metrics":["BTC: $92k"]}' | python3 viz.py generate

# 图片转 ASCII 艺术
python3 viz.py convert image.png --charset blocks --emotion bull

# 查询能力（AI 发现用）
python3 viz.py capabilities --format json
```

## 架构

`viz.py` 是唯一的 CLI 入口，设计为 **AI 调用的渲染后端**（"画笔"）。AI 负责数据获取和内容组织，VIZ 只负责渲染。

### 子命令

| 命令 | 用途 |
|------|------|
| `viz.py generate` | 生成 1080×1080 可视化（PNG/GIF） |
| `viz.py convert` | 图片逐像素转 ASCII 艺术 |
| `viz.py capabilities` | 输出 JSON schema，供 AI 发现所有可用选项 |

### 数据流

```
AI 分析用户请求 → 构造 JSON → echo '...' | python3 viz.py generate → 渲染 → stdout JSON
```

### AI 集成协议

```bash
# 市场数据
echo '{"source":"market","headline":"DOW +600","emotion":"bull","metrics":["BTC: $92k","ETH: $4.2k"]}' | python3 viz.py generate

# 艺术新闻
echo '{"source":"art","headline":"Venice Biennale 2026","emotion":"love"}' | python3 viz.py generate

# 情绪日记
echo '{"source":"mood","emotion":"calm","title":"Sunday Morning"}' | python3 viz.py generate --video

# stdout 返回
# {"status":"ok","path":"media/viz_20260203_120000.png","seed":42,"format":"png","emotion":"bull","source":"market"}
```

所有 stdin JSON 字段可选。CLI 参数覆盖 stdin 同名值。

## Flexible Output System（千变万化）

打破刚性映射，实现从同一输入生成无限视觉变体。

```
旧系统: 文本 → 3 个离散类别 → 固定效果 → 固定配色 → ~3 种输出
新系统: 文本 → VAD 连续向量 → 文法组合 → 噪声调制 → 无限输出
```

### VAD 情感模型

每种情绪是三维空间中的一个点（24 种预定义锚点），而非离散标签：

| 维度 | 范围 | 含义 |
|------|------|------|
| **Valence** (效价) | -1 ↔ +1 | 消极 ↔ 积极 |
| **Arousal** (唤醒度) | -1 ↔ +1 | 平静 ↔ 激动 |
| **Dominance** (支配度) | -1 ↔ +1 | 顺从 ↔ 掌控 |

情感向量直接驱动视觉参数——高 Arousal 提升频率和速度，高 Valence 偏向暖色，高 Dominance 增加结构性。

### 内容来源词汇（Source Vocabulary）

不同来源通过视觉词汇区分身份，而非固定模板：

| 来源 | 粒子 | 颜文字风格 | 氛围词 |
|------|------|-----------|--------|
| `market` | `$¥€₿↑↓▲▼` | bull/bear | HODL, PUMP / SELL, EXIT |
| `art` | `✦◆●▽△○◇` | love/思考 | CREATE, EXHIBIT / SILENCE |
| `news` | `►◆■●▶` | surprised/thinking | BREAKING, ALERT / UNCLEAR |
| `mood` | `·˚✧∘○◦` | 全情绪 | BREATHE, PEACE / ALONE |

### 多样性来源

| 维度 | 变化数量 | 机制 |
|------|---------|------|
| 背景效果 | 7 种 (含 CPPN) | 文法概率选择 |
| 叠加效果 | 0-1 层 × 6 种 | 概率触发 |
| 混合模式 | 4 种 | ADD/SCREEN/OVERLAY/MULTIPLY |
| 布局算法 | 5 种 | scatter/grid/spiral/force/preset |
| ASCII 梯度 | 20 种 | classic/blocks/smooth/matrix/plasma... |
| 装饰风格 | 8 种 × 60+ 字符组 | 概率选择 |
| 连续参数 | ∞ | 情绪驱动 + 噪声调制 |
| **组合总数** | **3,000,000+ 离散 × ∞ 连续** | |

## 程序化生成引擎

### 可用效果

| 效果 | 描述 |
|------|------|
| `plasma` | 等离子体干涉波纹（4层正弦叠加） |
| `flame` | Doom 风格火焰（热传播 + 衰减） |
| `wave` | 多频率正弦叠加 |
| `moire` | 径向莫尔干涉 |
| `sdf_shapes` | 有符号距离场形状（圆、方、环、十字） |
| `noise_field` | Perlin-like 噪声场 + FBM |
| `cppn` | CPPN 神经网络图案（每个种子唯一） |

### 渲染管线

```
Engine 创建 Context + Buffer (160×160)
  → effect.pre() → state
  → for y,x: buffer[y][x] = effect.main(x, y, ctx, state)
  → effect.post()
  → buffer_to_image() → PIL Image (160×160)
  → sprite.render() for each sprite
  → upscale_image() → 1080×1080 (NEAREST)
  → sharpen + contrast → 最终 PNG/GIF
```

### 效果混合

```python
from procedural.compositor import CompositeEffect, BlendMode
from procedural.effects import get_effect

composite = CompositeEffect(
    get_effect('plasma'), get_effect('wave'),
    BlendMode.SCREEN, mix=0.5
)
```

## 颜文字系统

20 个情绪分类，300+ 个独特颜文字，覆盖从狂喜到恐慌的完整情感光谱。

**正面**: happy, euphoria, excitement, love, proud, relaxed
**负面**: sad, angry, anxiety, fear, panic, disappointed, lonely
**中性**: neutral, confused, surprised, sleepy, thinking, embarrassed, bored

经典别名：`bull` (= happy 精选) / `bear` (= sad 精选)，向后兼容。

## 精灵动画

视频模式下支持：

| 动画 | 描述 |
|------|------|
| `breathing` | 呼吸缩放 |
| `floating` | 上下浮动 |
| `color_cycle` | 色相循环 |

## 项目结构

```
VIZ/
├── viz.py                        # 唯一 CLI 入口（generate / convert / capabilities）
│
├── lib/                          # 共享模块
│   ├── content.py                # Content 数据结构
│   ├── vocabulary.py             # 来源视觉词汇（market / art / news / mood）
│   ├── ascii_convert.py           # 图片转 ASCII 艺术（由 viz.py convert 调用）
│   ├── glow.py                   # 发光文字效果
│   ├── ascii_texture.py          # ASCII 纹理和粒子散布
│   ├── kaomoji.py                # 颜文字渲染（20 分类，300+ 面孔）
│   ├── kaomoji_data.py           # 颜文字数据
│   ├── box_chars.py              # Box-drawing 字符（37 字符集）
│   └── effects.py                # 故障效果、粒子
│
├── procedural/                   # 程序化渲染引擎（160×160 → 1080×1080）
│   ├── engine.py                 # 渲染编排器
│   ├── types.py                  # 核心类型（Context, Cell, Buffer, Effect）
│   ├── renderer.py               # buffer_to_image(), upscale_image()
│   ├── compositor.py             # 效果混合（ADD/MULTIPLY/SCREEN/OVERLAY）
│   ├── layers.py                 # 精灵：TextSprite, KaomojiSprite, 装饰
│   ├── layouts.py                # 布局算法（scatter, grid, spiral, force）
│   ├── params.py                 # ParamSpec, 可复现 RNG
│   ├── palette.py                # 20 ASCII 梯度, 5 配色方案
│   ├── effects/                  # 可插拔效果（7 种内置）
│   │   ├── plasma.py, flame.py, wave.py, moire.py, sdf_shapes.py, noise_field.py
│   │   └── ...
│   ├── core/                     # 数学原语（纯 Python，无 NumPy）
│   │   ├── vec.py, sdf.py, noise.py, mathx.py
│   └── flexible/                 # 柔性输出系统
│       ├── emotion.py            # VAD 连续情感空间（24 锚点）
│       ├── color_space.py        # 连续色温/饱和度/亮度
│       ├── modulator.py          # 噪声调制 + Domain Warping
│       ├── grammar.py            # 概率文法 + 内容放置
│       ├── cppn.py               # CPPN 神经网络图案
│       └── pipeline.py           # 主管线（编排所有模块）
│
├── docs/                         # 详细文档
│   ├── usage.md                  # CLI 使用指南
│   ├── rendering.md              # 渲染管线
│   ├── flexible.md               # 柔性输出系统
│   ├── effects.md                # 效果参考
│   ├── kaomoji.md                # 颜文字系统
│   └── box_chars.md              # Box-drawing 字符系统
│
└── archive/                      # 已弃用 — 仅供参考，请勿修改
```

## 依赖

```
Pillow>=9.0.0
```

所有数学运算纯 Python stdlib，禁止 NumPy。唯一外部依赖是 Pillow。

## 参考

- [play.ertdfgcvb.xyz](https://play.ertdfgcvb.xyz) - 灵感来源
- [play.core](https://github.com/ertdfgcvb/play.core) - 核心参考实现
