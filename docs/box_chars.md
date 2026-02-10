# Box-Drawing & Semigraphic Character System（制图符号与半图形字符系统）

Unicode 制图符号和半图形字符库，穿透整个管线——从底层 ASCII 梯度到精灵装饰到粒子效果。

## 设计背景

传统 ASCII 艺术依赖有限的可打印字符（`" .:-=+*#%@"`），表现力受限。Unicode 提供了丰富的制图和几何字符：

| Unicode 区块 | 范围 | 用途 |
|---|---|---|
| Box Drawing | U+2500–U+257F | 线条、角落、交叉、T 形接头 |
| Block Elements | U+2580–U+259F | 半方块、阴影、填充 |
| Geometric Shapes | U+25A0–U+25FF | 圆、方、三角、菱形 |
| Braille Patterns | U+2800–U+28FF | 2×4 点阵（256 级密度） |
| Misc Symbols | 散布 | 箭头、星号、数学符号 |

参考资源：
- [Box-drawing characters (Wikipedia)](https://en.wikipedia.org/wiki/Box-drawing_characters)
- [play.ertdfgcvb.xyz](https://play.ertdfgcvb.xyz/abc.html) — character set philosophy
- CP437 / PETSCII semigraphics tradition

---

## 文件结构

| 文件 | 职责 |
|---|---|
| `lib/box_chars.py` | 中央字符库：字符集、梯度、边框、情绪选取 API |
| `procedural/palette.py` | ASCII 梯度定义（20 种，含 14 种新增） |
| `procedural/flexible/grammar.py` | 文法规则中的字符选择（装饰、粒子、文字） |
| `procedural/flexible/pipeline.py` | 装饰精灵渲染（frame、grid_lines、circuit） |
| `lib/effects.py` | 粒子字符集（10 种命名集） |

---

## 1. 字符集分类（CHARSETS）

`lib/box_chars.py` 定义 37 个命名字符集，按视觉语义分类：

### Box Drawing — 线条

| 名称 | 字符 | 说明 |
|---|---|---|
| `box_light` | `─│┌┐└┘├┤┬┴┼` | 细线 |
| `box_heavy` | `━┃┏┓┗┛┣┫┳┻╋` | 粗线 |
| `box_double` | `═║╔╗╚╝╠╣╦╩╬` | 双线 |
| `box_round` | `─│╭╮╰╯├┤┬┴┼` | 圆角 |
| `box_mixed` | `┍┑┕┙┝┥┯┷┿╃╄╅╆╇╈╉╊` | 混合粗细 |
| `box_arc` | `╭╮╯╰` | 圆弧角 |
| `box_diagonal` | `╱╲╳` | 对角线 |

**虚线变体：**

| 名称 | 字符 |
|---|---|
| `box_light_h` | `─┄┈╌` |
| `box_light_v` | `│┆┊╎` |
| `box_heavy_h` | `━┅┉╍` |
| `box_heavy_v` | `┃┇┋╏` |
| `box_dash_light` | `┄┆┈┊` |
| `box_dash_heavy` | `┅┇┉┋` |

### Block Elements — 方块填充

| 名称 | 字符 | 说明 |
|---|---|---|
| `blocks_full` | `░▒▓█` | 阴影梯度 |
| `blocks_half` | `▀▄▌▐` | 半方块 |
| `blocks_quarter` | `▖▗▘▙▚▛▜▝` | 象限方块 |
| `blocks_shade` | `░▒▓` | 三级阴影 |

### Geometric Shapes — 几何形

| 名称 | 字符 | 说明 |
|---|---|---|
| `geometric_filled` | `■▪▮●▲▼◆` | 实心 |
| `geometric_outline` | `□▫▯○△▽◇` | 空心 |
| `geometric_small` | `▪▫▸▹►◄▴▵▾▿` | 小型 |
| `geometric_circles` | `●○◉◎◦◌◍◐◑` | 圆形变体 |
| `geometric_triangles` | `▲△▴▵▶▷▸▹►▻▼▽▾▿◀◁◂◃◄◅` | 全方向三角 |

### Braille, Dots, Stars

| 名称 | 字符 | 说明 |
|---|---|---|
| `braille` | `⠀⠁⠂⠃⠄⠅⠆⠇⡀⡁⣀⣁...⣿` | 盲文点阵 (256 patterns) |
| `dots` | `·∙•◦○◎◉●` | 点的密度梯度 |
| `stars` | `✦✧★☆✶✴✹✻✼✽` | 星形 |
| `sparkles` | `⁺⁎∗✦✧✩✫✬✭✮✯✰` | 闪烁 |

### 其他

| 名称 | 字符 | 说明 |
|---|---|---|
| `math_operators` | `±×÷∓∞≈≠≤≥≡∝∑∏∫` | 数学运算符 |
| `arrows` | `←↑→↓↔↕↖↗↘↙⇐⇑⇒⇓` | 箭头 |
| `data` | `0123456789ABCDEF` | 十六进制 |
| `cp437_box` | 完整 CP437 制图符号 | 复古 |
| `cp437_misc` | `♠♣♥♦•◘○◙♂♀♪♫☼...` | CP437 杂项 |

### 使用

```python
from lib.box_chars import get_charset

chars = get_charset("box_light")   # → "─│┌┐└┘├┤┬┴┼"
chars = get_charset("braille")     # → "⠀⠁⠂⠃⠄⠅⠆⠇⡀⡁..."
```

---

## 2. 密度梯度（GRADIENTS）

从空/稀疏到密/实的字符序列，用于 `char_at_value()` 映射。共 67 种梯度，覆盖 428 个 Unicode 字符。

### 全部梯度一览

#### 经典 ASCII (5)

| 名称 | 梯度 | 风格 |
|---|---|---|
| `classic` | ` .:-=+*#%@` | 经典 ASCII |
| `smooth` | ` .':;!>+*%@#█` | 细腻 (13 级) |
| `matrix` | ` .:-=+*@#` | 黑客风 |
| `plasma` | `$?01▄abc+-><:.` | Plasma 效果 |
| `default` | ` .:-=+*#%@` | classic 别名 |

#### 方块填充 (8)

| 名称 | 梯度 | 风格 |
|---|---|---|
| `blocks` | ` ░▒▓█` | 方块 (5 级) |
| `blocks_fine` | ` ·░▒▓█` | 方块精细 (6 级) |
| `blocks_ultra` | ` ·⠁░▒▓▓█` | 方块+盲文 |
| `glitch` | ` ·░▒▓█▀▄▌▐` | 故障 |
| `vbar` | ` ▏▎▍▌▋▊▉█` | 垂直条填充 |
| `hbar` | ` ▁▂▃▄▅▆▇█` | 水平条填充 |
| `quadrant` | ` ▖▗▘▝▞▚▙▟█` | 四分块 |
| `halves` | ` ▔▕▁▖▌▀▐▙▛▜█` | 半块混合 |

#### Box-Drawing 线框 (20)

| 名称 | 梯度 | 风格 |
|---|---|---|
| `box_density` | ` ·┄─┈━░▒▓█` | 水平线密度 |
| `box_vertical` | ` ·┆│┊┃░▒▓█` | 垂直线密度 |
| `box_cross` | ` ·+┼╋╬░▒▓█` | 交叉密度 |
| `box_thin` | ` ╶╴╌─│├┤┬┴┼█` | 细线接头 |
| `box_thin_corner` | ` ╵╷│┌┐└┘├┤█` | 细线角 |
| `box_thick` | ` ╺╸╍━┃┣┫┳┻╋█` | 粗线接头 |
| `box_thick_corner` | ` ╹╻┃┏┓┗┛┣┫█` | 粗线角 |
| `box_double` | ` ═║╠╣╦╩╬╔╗█` | 双线接头 |
| `box_double_corner` | ` ═║╚╝╠╣╦╩╬█` | 双线角 |
| `box_rounded` | ` ·╭╮╯╰○◎●█` | 圆角 |
| `box_mixed_dh` | ` ╘╒╛╕╪╞╡╧╤█` | 混合: 双横细纵 |
| `box_mixed_dv` | ` ╙╓╜╖╫╟╢╨╥█` | 混合: 双纵细横 |
| `box_mixed_a` | ` ┍┑┕┙┿┝┥┷┯█` | 混合: 粗细 A |
| `box_mixed_b` | ` ┎┒┖┚╂┠┨┸┰█` | 混合: 粗细 B |
| `box_complex_a` | ` ┽┾╀╁╃╄╅╆╇╈█` | 复杂交叉 A |
| `box_complex_b` | ` ┞┟┡┢┦┧┩┪╉█` | 复杂交叉 B |
| `box_complex_c` | ` ┭┮┱┲┵┶┹┺╊█` | 复杂交叉 C |
| `box_ends` | ` ╼╾╽╿╌╍╎╏▒█` | 线端+混合粗细 |
| `box_weight` | ` ╎│╏┃║░▒▓█` | 线重递增 |
| `diagonal` | ` ╱╲╳▞▚░▒▓█` | 对角线 |

#### 几何/点阵 (14)

| 名称 | 梯度 | 风格 |
|---|---|---|
| `dots_density` | ` ·∙•◦○◎◉●█` | 圆点密度 |
| `geometric` | ` ·▪□▫▮■▓█` | 几何密度 |
| `braille_density` | ` ⠁⠃⠇⡇⣇⣧⣷⣿` | 盲文密度 |
| `circles` | ` ·◦○◎◉●◕█` | 圆形填充 |
| `circles_half` | ` ◜◝◞◟◐◑◒◓●` | 半圆弧 |
| `circles_arc` | ` ·◠◡◚◛◙◕◖◗█` | 圆弧段 |
| `squares` | ` ▫▪□▢▣▬▭▮▯■█` | 方形变体 |
| `diamonds` | ` ·◇◆◊▪■▓█` | 菱形 |
| `triangles` | ` ·◢◣◤◥▖▙▟█` | 三角形 |
| `quarters_geo` | ` ◰◱◲◳◴◵◶◷◧◨◩◪◫█` | 几何四分 |
| `squares_fill` | ` ◽◻▤▥▦▧▨▩◼◾█` | 填充方块 |
| `arrows_sm` | ` ▵▴▹▸▿▾◃◂▰▱█` | 小三角/箭头 |
| `arrows_lg` | ` △▷▽◁▻◅▲▶▼◀►◄█` | 大三角/箭头 |
| `geo_misc` | ` ◌◍◈◔◘◬◭◮◯◸◹◺◿█` | 几何杂项 |

#### 文字/排版 (15)

| 名称 | 梯度 | 风格 |
|---|---|---|
| `punctuation` | ` .,;:¿?¡!"@#%‰&*'█` | 标点密度 |
| `editorial` | ` ·†‡•−–_¯…█` | 编辑符号 |
| `math` | ` ·+-×÷±≈∞∫√█` | 数学运算 |
| `math_rel` | ` ·~≈≠=≤≥<>¬█` | 数学关系 |
| `brackets` | ` ·()[]{}&#124;/⁄\█` | 括号/分隔 |
| `greek` | ` ·μπ∂∆∑∏◊Ω█` | 希腊/学术 |
| `currency` | ` ¢$€£¥¤▪■▓█` | 货币符号 |
| `symbols` | ` ·¦¶§©®™°▓█` | 版权/排版 |
| `superscript` | ` ·ªº¹²³¼½¾█` | 上标/分数 |
| `quotes` | ` ''‚""„‹›«»█` | 引号 |
| `ligature` | ` ·æœßøəﬁﬂÆŒ█` | 连字/特殊 |
| `diacritics` | ` ·^¨`Əə°Øø█` | 变音符 |
| `digits` | ` 0123456789` | 数字 |
| `alpha_lower` | ` ijltrcfs...qmw█` | 小写字母 (按视觉重量) |
| `alpha_upper` | ` IJLTCFSE...QMW█` | 大写字母 (按视觉重量) |

#### 混合表现力 (5)

| 名称 | 梯度 | 风格 |
|---|---|---|
| `tech` | ` .·:;+*░▒▓█` | 技术风 |
| `cyber` | ` ·-=≡░▒▓█` | 赛博风 |
| `organic` | ` ·∙•○◎●▒▓█` | 有机风 |
| `noise` | ` ·⠁⠃░▒▓▓█` | 噪点风 |
| `circuit` | ` ·┄─├┼╋▒▓█` | 电路风 |

### 在管线中的使用

梯度名称通过 `grammar.py` 的 `_choose_gradient()` 选择（44 个进入自动选择池），由 `energy` 和 `structure` 参数驱动权重：

```
高 energy + 高 structure → box_thick, box_cross, diagonal, blocks
低 energy + 低 structure → organic, circles, editorial, braille_density
高 energy + 低 structure → glitch, cyber, arrows_lg, quadrant
低 energy + 高 structure → dots_density, geometric, vbar, hbar, box_double
```

其余梯度可通过 Director Mode（CLI `--gradient` 或 JSON `gradient` 字段）精确指定。

渲染时，`renderer.py` 的 `char_at_value(value, gradient_name)` 将 0.0–1.0 的值映射到梯度中的字符：

```python
# value=0.0 → 空格 (空)
# value=0.5 → 中间字符
# value=1.0 → 最密字符 (█ 或 ⣿)
char = gradient[int(value * (len(gradient) - 1))]
```

---

## 3. 边框字符集（BORDER_SETS）

完整的矩形边框绘制所需字符，含 11 个键位：

```
tl ─── h ─── tt ─── h ─── tr
│                           │
v              cross        v
│                           │
lt ─── h ─── cross── h ─── rt
│                           │
v                           v
│                           │
bl ─── h ─── bt ─── h ─── br
```

### 6 种边框风格

| 风格 | 角 | 水平 | 垂直 | 交叉 | 视觉 |
|---|---|---|---|---|---|
| `light` | `┌┐└┘` | `─` | `│` | `┼` | 细线 |
| `heavy` | `┏┓┗┛` | `━` | `┃` | `╋` | 粗线 |
| `double` | `╔╗╚╝` | `═` | `║` | `╬` | 双线 |
| `round` | `╭╮╰╯` | `─` | `│` | `┼` | 圆角 |
| `dash_light` | `┌┐└┘` | `┄` | `┆` | `┼` | 虚线 |
| `dash_heavy` | `┏┓┗┛` | `┅` | `┇` | `╋` | 粗虚线 |

### 使用

```python
from lib.box_chars import get_border_set

bs = get_border_set("double")
# → {"h": "═", "v": "║", "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
#    "lt": "╠", "rt": "╣", "tt": "╦", "bt": "╩", "cross": "╬"}

# 绘制 5 字宽的头部
header = f'{bs["tl"]}{bs["h"]*3}{bs["tr"]}'  # → "╔═══╗"
```

### build_box_frame_chars()

生成矩形边框的完整坐标列表：

```python
from lib.box_chars import build_box_frame_chars

chars = build_box_frame_chars(width=10, height=5, border_style="round")
# → [(0,0,"╭"), (9,0,"╮"), (0,4,"╰"), (9,4,"╯"),
#    (1,0,"─"), (2,0,"─"), ..., (0,1,"│"), ...]
```

---

## 4. 情绪驱动的字符选取

`get_chars_for_mood()` 根据三维参数 (energy, structure, warmth) 返回完整的字符调色板：

```python
from lib.box_chars import get_chars_for_mood

palette = get_chars_for_mood(energy=0.8, structure=0.3, warmth=0.5)
# → {
#     "gradient":   "glitch",           # 推荐梯度
#     "decoration": ["█", "▀", "▄", "▌", "▐"],  # 装饰字符
#     "particles":  "░▒▓█▀▄",           # 粒子字符
#     "border":     "double",           # 推荐边框
#     "fill":       "blocks_ultra",     # 填充梯度
# }
```

### 8 种字符调色板

| 名称 | energy | structure | warmth | 梯度 | 边框 |
|---|---|---|---|---|---|
| `calm_structured` | 低 | 高 | — | `dots_density` | round |
| `calm_organic` | 低 | 低 | — | `organic` | dash_light |
| `energetic_structured` | 高 | 高 | — | `circuit` | heavy |
| `energetic_chaotic` | 高 | 低 | — | `glitch` | double |
| `warm_gentle` | 中 | — | 高 | `blocks_fine` | round |
| `cold_sharp` | 中 | — | 低 | `cyber` | heavy |
| `data_dense` | 中 | 高 | 中 | `tech` | double |
| `minimal` | 中 | 低 | 中 | `blocks` | light |

### 选取逻辑

```
energy > 0.6 ?
  ├─ structure > 0.5 → energetic_structured (╋┼═║╬)
  └─ else           → energetic_chaotic     (█▀▄▌▐)
energy < 0.3 ?
  ├─ structure > 0.5 → calm_structured      (·○◎─│)
  └─ else           → calm_organic          (~≈◦○·)
else (0.3-0.6):
  ├─ warmth > 0.55  → warm_gentle           (◉●◎○◦)
  ├─ warmth < 0.35  → cold_sharp            (┃━╋╳┼)
  ├─ structure > 0.5 → data_dense           (░▒▓█┼)
  └─ else           → minimal               (·─│+)
```

15% 概率随机变异到其他调色板，增加多样性。

---

## 5. 装饰风格（Decoration Styles）

`grammar.py` 的 `_choose_decoration_style()` 现在支持 8 种风格：

| 风格 | 说明 | structure 偏向 |
|---|---|---|
| `corners` | 四角装饰 | 高 |
| `edges` | 四边等分装饰 | 高 |
| `scattered` | 随机散布 | 低 |
| `minimal` | 对角两点 | — |
| `none` | 无装饰 | — |
| **`frame`** | **Box-drawing 边框** | **高** |
| **`grid_lines`** | **交叉网格** | **高** |
| **`circuit`** | **电路板线路** | **低** |

### frame — Box-drawing 边框

在画面边缘绘制完整的矩形边框：

```
 ┌──────────────────────────────────┐
 │                                  │
 │     (ASCII art content)          │
 │                                  │
 ├──────────────┬───────────────────┤
 │              │                   │
 └──────────────┴───────────────────┘
```

- 边框粗细根据 energy 选择（高→heavy, 中→light/round, 低→dash/round）
- 四角 + 等分水平/垂直边 + 随机 T 形接头
- 角落带 breathing 动画

### grid_lines — 交叉网格

在画面内部绘制 2–5 × 2–5 的网格结构：

```
       │         │         │
  ─────┼─────────┼─────────┼─────
       │         │         │
  ─────┼─────────┼─────────┼─────
       │         │         │
```

- 交叉点使用 `cross` 字符（┼/╋/╬），带 breathing 动画
- 线段使用 dim color（比装饰色暗 40）
- 随机选择 light/heavy/dash_light 风格

### circuit — 电路板线路

生成 PCB 走线风格的节点+线路网络：

```
                ┤
                │
    ┼───────────┼──────·
                │
                │
    ·───────────┬──────────┤
                │
                └
```

- 4–10 个随机节点，使用交叉/T 形字符
- 每个节点延伸 2–6 段水平或垂直线路
- 线路末端使用角落字符或点作为端点
- 节点带 breathing 动画

---

## 6. 粒子字符集（Particle Charsets）

### lib/effects.py — 命名粒子集

`create_data_particles()` 支持 10 种命名字符集：

| 名称 | 字符 | 风格 |
|---|---|---|
| `data` | `0123456789.,:;-+*` | 数据（默认） |
| `hex` | `0123456789ABCDEF.:;` | 十六进制 |
| `binary` | `01 01 01·` | 二进制 |
| `box` | `─│┼┄┆━┃╋` | Box-drawing |
| `blocks` | `░▒▓█▀▄▌▐` | 方块 |
| `dots` | `·∙•◦○◎◉` | 圆点 |
| `braille` | `⠁⠂⠃⠄⠅⠆⠇⡀⣀⣿` | 盲文 |
| `geometric` | `▪▫□■◆◇△▽` | 几何 |
| `cross` | `┼╋╬╳+×` | 交叉 |
| `mixed` | `·░▒01┼╳○□` | 混合 |

```python
from lib.effects import create_data_particles

# 使用命名字符集
create_data_particles(draw, w, h, color, density=50, charset="box")

# 使用自定义字符串
create_data_particles(draw, w, h, color, density=50, charset="╱╲╳")
```

### grammar.py — 文法粒子选择

`_choose_particle_chars()` 根据 energy/warmth 从 25+ 组字符中选择：

```
高 energy (>0.7) → box-drawing 线段 + 方块
中 energy (0.4-0.7) → 经典 + 几何 + box 混合
低 energy + 高 warmth → 几何 + 盲文
低 energy + 低 warmth → 经典 + 几何 + 盲文
```

---

## 7. 文字元素中的 Semigraphic 符号

`grammar.py` 的 `_choose_text_elements()` 在各情绪词池中加入了制图符号：

| 情绪区间 | 新增符号示例 |
|---|---|
| 正面高唤醒 | `━━▶` `╱╲╱` `◉` `█▀█` `⣿` |
| 正面低唤醒 | `╭─╮` `≈≈` `◌` `⠿` `·∙·` |
| 中性 | `─┄─` `┈┈┈` `╌╌╌` `◦◦◦` |
| 负面高唤醒 | `╳╳╳` `┃┃┃` `▓▓▓` `╋╋╋` |
| 负面低唤醒 | `┄┄┄` `░░░` `┆┆┆` `⠁⠂⠄` |
| 极端负面高唤醒 | `█▄█` `━━╋` `▓█▓` `╬╬╬` |
| 极端负面低唤醒 | `░░░` `┈┈┈` `⠀⠀⠀` `···` |

这些符号作为氛围文字散布在画面中，与传统文字混合出现。

---

## 8. 装饰字符的情绪选取

`grammar.py` 的 `_choose_decoration_chars()` 现在有 60+ 种字符组合，按情绪维度组织：

### 高能量 (energy > 0.7)

偏向粗重和几何——box 角落 + 交叉 + 方块：

```python
["┏", "┓", "┗", "┛"]      # 粗角
["╔═", "═╗", "╚═", "═╝"]  # 双线角
["╋", "╋", "╋", "╋"]       # 粗交叉
["▛", "▜", "▙", "▟"]       # 象限方块
["●", "○", "●", "○"]       # 实/空圆
```

### 中等能量 (0.4–0.7)

经典 ASCII + box 角 + 线条混合：

```python
["┌─", "─┐", "└─", "─┘"]  # 细线角
["├", "┤", "┬", "┴"]       # T 形接头
["═", "═", "║", "║"]       # 双线
```

### 低能量 + 暖色 (warmth > 0.6)

圆润和点状：

```python
["·", "·", "·", "·"]       # 小点
["╭", "╮", "╰", "╯"]       # 圆角
["•", "◦", "•", "◦"]       # 圆点
```

### 低能量 + 冷色

细线和虚线：

```python
["─", "─", "│", "│"]       # 细线
["┄", "┄", "┆", "┆"]       # 虚线
["∙", "∙", "∙", "∙"]       # 微点
```

---

## 9. 完整字符流动路径

```
输入: text="volatile crash"

1. text_to_emotion()
   → VAD = (-0.7, +0.8, -0.4)

2. to_visual_params()
   → energy=0.85, warmth=0.15, structure=0.30

3. VisualGrammar.generate()
   ├── _choose_gradient(0.85, 0.30)
   │   → "glitch" (权重: 0.05 + 0.85*0.15 = 0.18)
   │
   ├── _choose_decoration_style(0.30)
   │   → "circuit" (权重: 0.08 + 0.70*0.08 = 0.14)
   │
   ├── _choose_decoration_chars(0.85, 0.15)
   │   → ["╋", "╋", "╋", "╋"] (高能量→交叉集)
   │
   ├── _choose_particle_chars(0.15, 0.85)
   │   → "━┃╋┅┇" (高能量→box 线段)
   │
   └── _choose_text_elements(-0.7, +0.8)
       → ["╳╳╳", "SELL", "▼"]

4. Pipeline._build_decoration_sprites()
   → circuit 风格: 6 个节点 + 线路 + 端点

5. Engine.render_frame()
   ├── buffer[y][x] = Cell(char_idx, fg, bg)
   │   char_idx → palette.char_at_value() → "glitch" 梯度
   │   → " ·░▒▓█▀▄▌▐" 中的字符
   │
   ├── buffer_to_image() → 低分辨率 PIL Image
   ├── upscale → 1080×1080
   └── 渲染精灵: circuit 装饰 + "━┃╋" 粒子 + "╳╳╳" 文字

最终输出: 充满 box-drawing 字符的电路板风格画面
```

---

## 10. 字体兼容性

所有字符均选自 **DejaVu Sans Mono** 字体的覆盖范围。该字体是系统默认等宽字体，支持：

- 完整 Box Drawing 区块 (U+2500–U+257F)
- Block Elements (U+2580–U+259F)
- Geometric Shapes (U+25A0–U+25FF)
- Braille Patterns (U+2800–U+28FF)
- 常用数学符号

如果遇到字符显示为方框（□），通常是字体不支持该码位。可通过以下方式验证：

```python
from PIL import ImageFont
font = ImageFont.truetype("DejaVuSansMono.ttf", 12)
bbox = font.getbbox("╔═╗")  # 如果返回非零尺寸，表示支持
```

---

## 11. 组合空间扩展

本次更新对组合空间的影响：

| 维度 | 旧 | 新 | 增长 |
|---|---|---|---|
| ASCII 梯度 | 5 种 | 20 种 | ×4 |
| 装饰风格 | 5 种 | 8 种 | ×1.6 |
| 装饰字符组 | 12 组 | 60+ 组 | ×5 |
| 粒子字符组 | 9 组 | 25+ 组 | ×2.8 |
| 命名粒子集 | 1 种 | 10 种 | ×10 |
| 氛围文字池 | ~50 | ~100 | ×2 |
| 边框风格 | 0 种 | 6 种 | 新增 |

**理论离散组合：** 从 ~235,000 增长到 **~3,000,000+** 种。

加上连续参数（warmth, saturation, energy, structure, ...）和 15% 随机变异概率 → 实际变体空间趋近无限。
