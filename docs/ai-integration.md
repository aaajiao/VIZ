# AI 集成指南 — VIZ as Your Paintbrush

**一页纸让 AI 完全掌握 VIZ。**

VIZ 是面向 AI 的 ASCII 艺术可视化后端。AI 负责理解用户意图、获取数据、组织内容；VIZ 只负责渲染。

```
用户请求 → AI 分析 → 构造 JSON → echo '...' | python3 viz.py generate → stdout JSON
```

---

## 快速开始

```bash
# 最小示例：只需情绪
echo '{"emotion":"joy"}' | python3 viz.py generate

# 完整示例：市场数据可视化
echo '{"source":"market","headline":"BTC $95,000","emotion":"euphoria","metrics":["ETH: $4.2k","SOL: $180"]}' | python3 viz.py generate

# 动画 GIF
echo '{"emotion":"panic","video":true}' | python3 viz.py generate
```

**stdout 返回**:
```json
{"status":"ok","results":[{"path":"media/viz_20260203_120000.png","seed":42,"format":"png"}],"emotion":"euphoria","source":"market"}
```

---

## 输入协议 (JSON via stdin)

所有字段**可选**。VIZ 会自动推断缺失的参数。

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `emotion` | string | 情绪名称（见下方列表） |
| `source` | string | 内容来源：`market` / `art` / `news` / `mood` |
| `headline` | string | 主标题文字 |
| `metrics` | list[string] | 数据指标（如 `["BTC: $92k", "ETH: $4.2k"]`） |
| `body` | string | 正文文本（用于情绪推断兜底） |
| `title` | string | 叠加标题 |
| `timestamp` | string | 时间戳显示 |

### 进阶字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `vad` | string / list | 直接 VAD 向量，如 `"0.8,0.5,0.3"` 或 `[0.8, 0.5, 0.3]` |
| `effect` | string | 背景效果名称 |
| `seed` | int | 随机种子（可复现） |
| `layout` | string | 布局算法 |
| `decoration` | string | 装饰风格 |
| `gradient` | string | ASCII 字符梯度 |
| `overlay` | object | 叠加效果：`{"effect":"wave","blend":"SCREEN","mix":0.3}` |
| `params` | object | 效果参数微调 |

### 导演模式（Director Mode）

域变换、后处理链、空间遮罩、合成模式和效果变体现在可以通过 JSON 字段直接控制：

| 字段 | 类型 | 说明 |
|------|------|------|
| `transforms` | list[dict] | 域变换链，如 `[{"type":"kaleidoscope","segments":6}]`；参数可为动画规格 |
| `postfx` | list[dict] | 后处理链，如 `[{"type":"vignette","strength":0.5,"pulse_speed":0.5}]` |
| `composition` | string | 合成模式：`blend` / `masked_split` / `radial_masked` / `noise_masked` |
| `mask` | string | 遮罩类型+参数（CLI 格式：`radial:center_x=0.5,radius=0.3`） |
| `variant` | string | 强制效果变体名（如 `warped`、`alien`、`turbulent`） |

不指定时，文法系统根据情绪参数自动选择最优组合。指定时，精确覆盖文法选择。

**GIF/视频动画增强：** 合成层（transforms、PostFX、masks）在动画模式下自动产生帧间变化。Transforms 支持动画 kwargs（旋转、缩放随时间变化），PostFX 支持滚动/脉动/漂移参数，masks 支持 `mask_anim_speed` 控制边界动画。Grammar 根据 energy 自动注入动画参数；Director Mode 也可手动指定。

`params` 字段可用于微调效果的**变形参数**（deformation params），这些参数直接传递给效果：

```json
{"params": {"surface_noise": 0.5, "twist": 1.2}}
{"params": {"self_warp": 0.3, "noise_injection": 0.4}}
{"params": {"distortion": 0.6, "multi_center": 3}}
{"params": {"vertex_noise": 0.4, "morph": 0.7}}
```

可用变形参数因效果而异，详见 [composition.md](composition.md#structural-variants)。

### 输出控制

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `video` | bool | false | 输出 GIF 动画 |
| `duration` | float | 3.0 | GIF 时长（秒） |
| `fps` | int | 15 | 帧率 |
| `variants` | int | 1 | 生成多个变体 |

---

## 情绪系统 (25 种预定义)

情绪不是离散标签，而是 VAD 三维空间中的点：

| 维度 | 范围 | 含义 |
|------|------|------|
| **Valence** | -1 ↔ +1 | 消极 ↔ 积极 |
| **Arousal** | -1 ↔ +1 | 平静 ↔ 激动 |
| **Dominance** | -1 ↔ +1 | 顺从 ↔ 掌控 |

### 可用情绪名称

**高能量正面** (V+, A+):
- `euphoria` — 狂喜 (0.9, 0.85, 0.6)
- `excitement` — 兴奋 (0.62, 0.75, 0.38)
- `joy` — 喜悦 (0.76, 0.48, 0.35)
- `surprise` — 惊喜 (0.4, 0.67, -0.13)
- `awe` — 敬畏 (0.5, 0.55, -0.3)

**低能量正面** (V+, A-):
- `calm` — 平静 (0.3, -0.6, 0.2)
- `serenity` — 安详 (0.5, -0.4, 0.3)
- `love` — 爱 (0.85, 0.35, 0.25)
- `hope` — 希望 (0.55, 0.2, 0.15)
- `trust` — 信任 (0.6, -0.1, 0.4)
- `nostalgia` — 怀旧 (0.2, -0.2, -0.1)

**高能量负面** (V-, A+):
- `panic` — 恐慌 (−0.8, 0.9, −0.6)
- `fear` — 恐惧 (−0.64, 0.6, −0.43)
- `anxiety` — 焦虑 (−0.51, 0.6, −0.33)
- `anger` — 愤怒 (−0.51, 0.59, 0.25)
- `volatile` — 动荡 (−0.1, 0.8, −0.2)

**低能量负面** (V-, A-):
- `sadness` — 悲伤 (−0.63, −0.27, −0.33)
- `despair` — 绝望 (−0.8, −0.4, −0.7)
- `melancholy` — 忧郁 (−0.3, −0.3, −0.2)
- `boredom` — 无聊 (−0.2, −0.6, −0.2)

**特殊**:
- `bull` — 牛市 (0.7, 0.5, 0.4)
- `bear` — 熊市 (−0.6, 0.4, −0.3)
- `neutral` — 中性 (0, −0.1, 0)
- `contempt` — 蔑视 (−0.4, 0.1, 0.5)
- `disgust` — 厌恶 (−0.6, 0.35, 0.2)

### 情绪推断优先级

1. `emotion` 字段指定 → 直接使用
2. `vad` 字段指定 → 直接使用 VAD 向量
3. `headline` + `body` 文本 → 关键词匹配推断 VAD
4. 都没有 → 默认 `neutral`

---

## 内容来源 (Source Vocabulary)

来源决定视觉词汇（粒子、颜文字风格、氛围词），**而非固定模板**：

| 来源 | 粒子字符 | 颜文字风格 | 氛围词 |
|------|---------|-----------|--------|
| `market` | `0123456789$#%↑↓±` | euphoria/anxiety/panic | BULL, RISE / BEAR, SELL / HOLD, WAIT |
| `art` | `◆◇○●□■△▽✧✦` | love/thinking/proud | CREATE, VISION / VOID, FADE / FORM, SHAPE |
| `news` | `ABCDEFG!?#@&` | neutral/surprised/confused | BREAKING, UPDATE / ALERT, WARN / NEWS, REPORT |
| `mood` | `·˚✧♪♫∞~○◦` | happy/sad/love/relaxed | FEEL, FLOW / EMPTY, LOST / THINK, DRIFT |

---

## 可用效果 (17 种)

| 效果 | 描述 | 最佳场景 |
|------|------|---------|
| `plasma` | 等离子体干涉波纹 | 高能量情绪 |
| `flame` | Doom 风格火焰 | panic, anger |
| `wave` | 多频率正弦叠加 | 流动感 |
| `moire` | 径向莫尔干涉 | 神秘、迷幻 |
| `sdf_shapes` | 距离场几何形状 | 结构性、现代 |
| `noise_field` | Perlin 噪声场 | 有机、自然 |
| `cppn` | 神经网络图案 | 每个种子独特 |
| `ten_print` | C64 迷宫图案 (10 PRINT) | 复古、怀旧 |
| `game_of_life` | Conway 生命游戏 | 有机复杂性 |
| `donut` | 旋转 3D 甜甜圈 | 未来感、技术 |
| `mod_xor` | 位运算分形图案 | 数学、抽象 |
| `wireframe_cube` | 3D 旋转线框立方体 | 几何、科技 |
| `chroma_spiral` | 色差螺旋 | 迷幻、催眠 |
| `wobbly` | 域扭曲流体 | 梦幻、柔和 |
| `sand_game` | 落沙粒子模拟 | 冥想、平静 |
| `slime_dish` | 黏菌智能体模拟 | 生物、有机 |
| `dyna` | 动态吸引子干涉波 | 动感、活力 |

VIZ 会根据情绪自动选择效果，也可用 `effect` 字段强制指定。

---

## 布局算法 (5 种)

| 布局 | 描述 |
|------|------|
| `random_scatter` | 随机散布 |
| `grid_jitter` | 网格 + 随机偏移 |
| `spiral` | 螺旋排列 |
| `force_directed` | 力导向（互斥） |
| `preset` | 预设位置 |

---

## 装饰风格 (8 种)

`corners` / `edges` / `scattered` / `minimal` / `none` / `frame` / `grid_lines` / `circuit`

---

## ASCII 梯度 (67 种)

**经典 ASCII:** `classic` / `smooth` / `matrix` / `plasma` / `default`

**方块填充:** `blocks` / `blocks_fine` / `blocks_ultra` / `glitch` / `vbar` / `hbar` / `quadrant` / `halves`

**Box-Drawing 线框:** `box_density` / `box_vertical` / `box_cross` / `box_thin` / `box_thin_corner` / `box_thick` / `box_thick_corner` / `box_double` / `box_double_corner` / `box_rounded` / `box_mixed_dh` / `box_mixed_dv` / `box_mixed_a` / `box_mixed_b` / `box_complex_a` / `box_complex_b` / `box_complex_c` / `box_ends` / `box_weight` / `diagonal`

**几何/点阵:** `dots_density` / `geometric` / `braille_density` / `circles` / `circles_half` / `circles_arc` / `squares` / `diamonds` / `triangles` / `quarters_geo` / `squares_fill` / `arrows_sm` / `arrows_lg` / `geo_misc`

**文字/排版:** `punctuation` / `editorial` / `math` / `math_rel` / `brackets` / `greek` / `currency` / `symbols` / `superscript` / `quotes` / `ligature` / `diacritics` / `digits` / `alpha_lower` / `alpha_upper`

**混合表现力:** `tech` / `cyber` / `organic` / `noise` / `circuit`

---

## 混合模式 (叠加效果用)

`ADD` / `SCREEN` / `OVERLAY` / `MULTIPLY`

---

## 完整示例

### 1. 市场暴涨

```bash
echo '{
  "source": "market",
  "headline": "BTC BREAKS $100K",
  "emotion": "euphoria",
  "metrics": ["ETH: $5.2k", "SOL: $300", "Volume: $89B"],
  "seed": 42
}' | python3 viz.py generate
```

### 2. 艺术展览

```bash
echo '{
  "source": "art",
  "headline": "Venice Biennale 2026",
  "emotion": "awe",
  "body": "immersive digital installations"
}' | python3 viz.py generate
```

### 3. 恐慌动画

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

### 4. 直接指定 VAD

```bash
echo '{
  "vad": [0.8, -0.3, 0.5],
  "headline": "Custom Emotion"
}' | python3 viz.py generate
```

### 5. 导演模式：精确控制合成维度

```bash
echo '{
  "emotion": "euphoria",
  "effect": "plasma",
  "variant": "warped",
  "transforms": [{"type": "kaleidoscope", "segments": 6}],
  "postfx": [{"type": "vignette", "strength": 0.5, "pulse_speed": 0.5, "pulse_amp": 0.2}, {"type": "color_shift", "hue_shift": 0.1, "drift_speed": 0.3}],
  "composition": "radial_masked",
  "seed": 100
}' | python3 viz.py generate
```

### 8. 动画合成增强（GIF 模式）

```bash
echo '{
  "emotion": "euphoria",
  "video": true,
  "transforms": [{"type": "rotate", "angle": {"base": 0.0, "speed": 0.3, "mode": "linear"}}],
  "postfx": [{"type": "scanlines", "spacing": 4, "darkness": 0.3, "scroll_speed": 2.0}],
  "params": {"mask_anim_speed": 1.0}
}' | python3 viz.py generate
```

### 6. 强制效果 + 叠加

```bash
echo '{
  "emotion": "calm",
  "effect": "noise_field",
  "overlay": {"effect": "wave", "blend": "SCREEN", "mix": 0.2},
  "gradient": "organic"
}' | python3 viz.py generate
```

### 7. 多变体

```bash
echo '{"emotion": "joy", "variants": 5}' | python3 viz.py generate
# → 5 张不同种子的图片，同一情绪不同视觉组合
```

---

## 输出规格

| 项 | 值 |
|----|------|
| 格式 | PNG (quality=95) 或 GIF |
| 尺寸 | 1080 × 1080 像素 |
| 内部渲染 | 160 × 160（最近邻上采样），背景通过第二渲染通道生成纹理（~320k 种组合） |
| 默认目录 | `./media/` |
| 文件命名 | `viz_{timestamp}.{png\|gif}` |

---

## stdout 输出格式

**成功**:
```json
{
  "status": "ok",
  "results": [
    {"path": "media/viz_20260203_120000.png", "seed": 42, "format": "png"}
  ],
  "emotion": "euphoria",
  "source": "market"
}
```

**多变体**:
```json
{
  "status": "ok",
  "results": [
    {"path": "media/viz_20260203_120000_v0.png", "seed": 42, "format": "png"},
    {"path": "media/viz_20260203_120000_v1.png", "seed": 43, "format": "png"},
    {"path": "media/viz_20260203_120000_v2.png", "seed": 44, "format": "png"}
  ],
  "emotion": "joy",
  "source": null
}
```

**错误**:
```json
{"status": "error", "message": "Invalid emotion name: xyz"}
```

---

## 能力查询

AI 可随时查询 VIZ 的完整能力：

```bash
python3 viz.py capabilities --format json
```

返回所有可用情绪、效果、来源、布局、装饰、梯度、输入输出 schema。

---

## CLI 参数 (备选)

stdin JSON 是首选，但 CLI 参数也可用（会覆盖 stdin 同名值）：

```bash
python3 viz.py generate --emotion panic --source market --headline "CRASH" --video --seed 42
```

---

## AgentSkills 集成

VIZ 提供 [AgentSkills](https://agentskills.io) 兼容的 skill，让 AI 助手自动学会使用 VIZ。

### 安装 Skill

**OpenClaw / OpenCode:**
```bash
# 全局安装
cp -r skills/viz-ascii-art ~/.openclaw/skills/

# 或在 VIZ 项目目录工作时自动发现
```

**Claude Code / Claude.ai:**
上传 `skills/viz-ascii-art/` 文件夹。

### Skill 结构

```
skills/viz-ascii-art/
├── SKILL.md              # 主指令（AI 激活时加载）
├── README.md             # 安装说明
└── references/           # 详细参考（按需加载）
    ├── EMOTIONS.md       # 25 种情绪的 VAD 值
    ├── EFFECTS.md        # 17 种效果及参数
    └── EXAMPLES.md       # 完整使用示例
```

安装后，AI 在用户提及 "visualization"、"ASCII art"、"kaomoji"、"emotion image" 等关键词时会自动激活此 skill。

---

## 设计原则

1. **AI 是大脑，VIZ 是画笔** — 数据获取、内容组织、情感判断由 AI 完成
2. **输入宽松，输出确定** — 所有字段可选，VIZ 自动推断缺失参数
3. **同一输入，千变万化** — 相同情绪 + 不同种子 = 无限视觉变体（背景纹理由第二渲染通道自动生成，不需要额外输入）
4. **结构化输出** — stdout 始终返回 JSON，便于程序解析
5. **可复现** — 指定 `seed` 即可精确复现任何输出
