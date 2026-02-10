# CLI 使用指南 — viz.py

`viz.py` 是唯一的命令行入口，提供 3 个子命令。设计为 AI 调用的渲染后端。

## 子命令总览

| 子命令 | 用途 | 输入 | 输出 |
|--------|------|------|------|
| `generate` | 生成 1080×1080 可视化 | 情绪/VAD + 可选内容数据 | PNG/GIF + stdout JSON |
| `convert` | 图片转 ASCII 艺术 | 图片路径 | PNG |
| `capabilities` | 查询能力（AI 发现用） | 无 | JSON schema |

---

## 1. generate — 生成可视化

### 基本用法

```bash
# 从情绪名生成（纯视觉）
python3 viz.py generate --emotion euphoria --seed 42

# 从文本推断情绪
python3 viz.py generate --text "市场暴跌 恐慌蔓延"

# 直接指定 VAD 向量
python3 viz.py generate --vad 0.5,-0.3,0.2
```

### AI 集成（stdin JSON）

AI 通过 stdin 传入结构化 JSON，CLI 作为纯渲染后端：

```bash
# 市场数据可视化
echo '{"source":"market","headline":"DOW +600","emotion":"bull","metrics":["BTC: $92k","ETH: $4.2k"]}' | python3 viz.py generate

# 艺术新闻可视化
echo '{"source":"art","headline":"Venice Biennale 2026","emotion":"love","body":"immersive installations"}' | python3 viz.py generate

# 情绪日记
echo '{"source":"mood","emotion":"calm","title":"Sunday Morning"}' | python3 viz.py generate --video
```

stdin JSON 字段全部可选，CLI 参数会覆盖 stdin 中的同名值。

### stdout 输出

```json
{"status": "ok", "results": [{"path": "/home/user/VIZ/media/viz_20260203_120000.png", "seed": 42, "format": "png"}], "emotion": "euphoria", "source": "market"}
```

### 完整参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `--emotion` | str | 推断 | 情绪名称（joy, fear, panic, bull, bear, ...） |
| `--source` | str | 无 | 内容来源（market, art, news, mood） |
| `--title` | str | 无 | 标题叠加文字 |
| `--text` | str | 无 | 文本（用于情绪推断兜底） |
| `--headline` | str | 无 | 主标题文字 |
| `--metrics` | list | 无 | 指标列表（空格分隔） |
| `--vad` | str | 无 | VAD 向量（如 `0.8,0.9,0.7`） |
| `--effect` | str | 自动 | 背景效果名 |
| `--seed` | int | 随机 | 随机种子（可复现） |
| `--video` | flag | false | 输出 GIF 而非 PNG |
| `--duration` | float | 3.0 | GIF 时长（秒） |
| `--fps` | int | 15 | 帧率 |
| `--variants` | int | 1 | 变体数量 |
| `--layout` | str | 自动 | 布局算法名 |
| `--decoration` | str | 自动 | 装饰风格 |
| `--gradient` | str | 自动 | ASCII 梯度名 |
| `--transforms` | list | 自动 | 域变换链，如 `kaleidoscope:segments=6 tile:cols=3` |
| `--postfx` | list | 自动 | 后处理链，如 `vignette:strength=0.5 scanlines:spacing=4` |
| `--blend-mode` | str | 自动 | 混合模式：`ADD` / `SCREEN` / `OVERLAY` / `MULTIPLY` |
| `--overlay` | str | 自动 | 叠加效果名（如 `wave`、`plasma`） |
| `--overlay-mix` | float | 自动 | 叠加混合比 0.0-1.0 |
| `--composition` | str | 自动 | 合成模式：`blend` / `masked_split` / `radial_masked` / `noise_masked` |
| `--mask` | str | 自动 | 遮罩类型+参数，如 `radial:center_x=0.5,radius=0.3` |
| `--variant` | str | 自动 | 强制效果变体名（如 `warped`、`alien`） |
| `--output-dir` | str | ./media | 输出目录 |
| `--mp4` | flag | false | 同时输出 MP4（需要系统 FFmpeg） |

### 模式

**单帧**（默认）：
```bash
python3 viz.py generate --emotion joy --seed 42
# → media/viz_20260203_120000.png
```

**多变体**：
```bash
python3 viz.py generate --text "hope" --variants 5
# → 5 张不同种子的 PNG，相同情绪不同视觉组合
```

**动画 GIF**：
```bash
python3 viz.py generate --emotion calm --video --duration 3 --fps 15
# → media/viz_20260203_120000.gif
```

**动画 MP4**（需要系统安装 FFmpeg）：
```bash
python3 viz.py generate --emotion euphoria --video --mp4
# → media/viz_20260203_120000.gif + media/viz_20260203_120000.mp4
```

### 导演模式（Director Mode）

精确控制合成系统的所有维度——域变换、后处理链、合成模式、遮罩、变体：

```bash
# 万花筒 + 暗角后处理
python3 viz.py generate --emotion joy --seed 42 \
  --transforms kaleidoscope:segments=6 \
  --postfx vignette:strength=0.5 scanlines:spacing=4

# 完整导演模式：指定所有合成维度
python3 viz.py generate --emotion euphoria --seed 100 \
  --effect plasma --overlay wave --blend-mode SCREEN --overlay-mix 0.4 \
  --composition radial_masked --mask radial:center_x=0.5,radius=0.3 \
  --transforms mirror_quad --postfx color_shift:hue_shift=0.1 --variant warped
```

复合参数格式：`name:key=val,key=val`，如 `kaleidoscope:segments=6`。

stdin JSON 同样支持：`transforms`、`postfx`、`composition`、`mask`、`variant` 字段。

### 内容来源词汇（Source Vocabulary）

不同来源通过视觉词汇（粒子、颜文字、符号）区分身份，而非固定模板：

| 来源 | 粒子 | 颜文字风格 | 氛围词 |
|------|------|-----------|--------|
| `market` | `$¥€₿↑↓▲▼` | bull/bear 情绪 | HODL, PUMP, APE IN / SELL, EXIT |
| `art` | `✦◆●▽△○◇` | love/思考 | CREATE, EXHIBIT / SILENCE |
| `news` | `►◆■●▶` | surprised/thinking | BREAKING, ALERT / UNCLEAR |
| `mood` | `·˚✧∘○◦` | 全情绪 | BREATHE, PEACE / ALONE |

---

## 2. convert — 图片转 ASCII

将真实图片逐像素转换为 ASCII 艺术。

```bash
# 基本转换
python3 viz.py convert image.png

# 指定字符集和情绪
python3 viz.py convert chart.png --charset blocks --emotion bull
```

### 字符集

| 名称 | 字符 | 风格 |
|------|------|------|
| `classic` | 完整 ASCII 梯度 | 经典 |
| `simple` | ` .:-=+*#%@` | 简约 |
| `blocks` | `░▒▓█` | 方块 |
| `bull` | ` .+*$↑▲🚀` | 牛市 |
| `bear` | ` .+*$↓▼📉` | 熊市 |
| `numbers` | `0123456789` | 数字 |
| `money` | `¥$€£₿` | 货币 |

---

## 3. capabilities — 能力查询

AI 用此命令发现 VIZ 支持的所有选项：

```bash
python3 viz.py capabilities
python3 viz.py capabilities --format json  # 默认 JSON
```

返回：

```json
{
  "emotions": {"joy": {"valence": 0.76, "arousal": 0.48, "dominance": 0.35}, "...": "..."},
  "effects": ["cppn", "flame", "moire", "noise_field", "plasma", "sdf_shapes", "wave", "..."],
  "sources": ["art", "market", "mood", "news"],
  "layouts": ["random_scatter", "grid_jitter", "spiral", "force_directed", "preset"],
  "decorations": ["corners", "edges", "scattered", "minimal", "none", "frame", "grid_lines", "circuit"],
  "gradients": ["classic", "smooth", "matrix", "plasma", "default", "blocks", "..."],
  "transforms": ["mirror_x", "mirror_y", "mirror_quad", "kaleidoscope", "tile", "rotate", "zoom", "spiral_warp", "polar_remap"],
  "postfx": ["threshold", "invert", "edge_detect", "scanlines", "vignette", "pixelate", "color_shift"],
  "masks": ["horizontal_split", "vertical_split", "diagonal", "radial", "noise", "sdf"],
  "composition_modes": ["blend", "masked_split", "radial_masked", "noise_masked"],
  "variants": {"plasma": ["classic", "warped", "noisy", "turbulent", "slow_morph"], "...": "..."},
  "input_schema": {"emotion": "string", "source": "string", "transforms": "list[{type, ...params}]", "postfx": "list[{type, ...params}]", "composition": "string", "mask": "string", "variant": "string", "...": "..."},
  "output_schema": {"status": "string", "results": "list[{path, seed, format}]", "...": "..."}
}
```

---

## 输出规格

| 项 | 值 |
|----|------|
| 输出格式 | PNG (quality=95)、GIF 或 MP4 (via FFmpeg) |
| 画布尺寸 | 1080 × 1080 像素 |
| 内部渲染 | 160 × 160（最近邻上采样） |
| 默认目录 | `./media/` |
| 文件命名 | `viz_{timestamp}.{png\|gif}` |
| 可复现性 | `--seed` 参数控制 |

---

## 数据流

```
AI 分析用户请求
    │
    ▼
构造 JSON（emotion + 可选内容数据）
    │
    ▼
echo '...' | python3 viz.py generate
    │
    ▼
VIZ 渲染（FlexiblePipeline）
    │
    ▼
stdout JSON（results 数组 + emotion + source）
```

VIZ 是纯渲染后端。数据获取、情感分析、内容组织由 AI 负责。
