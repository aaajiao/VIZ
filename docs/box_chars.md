# Box-Drawing & Semigraphic Character System（制图符号与半图形字符系统）

Unicode 制图符号和半图形字符库，穿透整个管线——从底层 ASCII 梯度到精灵装饰到粒子效果。

## 设计背景

传统 ASCII 艺术依赖有限的可打印字符（`" .:-=+*#%@"`），表现力受限。Unicode 提供了丰富的制图和几何字符：

| Unicode 区块 | 范围 | 用途 |
|---|---|---|
| Box Drawing | U+2500-U+257F | 线条、角落、交叉、T 形接头 |
| Block Elements | U+2580-U+259F | 半方块、阴影、填充 |
| Geometric Shapes | U+25A0-U+25FF | 圆、方、三角、菱形 |
| Braille Patterns | U+2800-U+28FF | 2x4 点阵（256 级密度） |
| Misc Symbols | 散布 | 箭头、星号、数学符号 |

参考资源：
- [Box-drawing characters (Wikipedia)](https://en.wikipedia.org/wiki/Box-drawing_characters)
- [play.ertdfgcvb.xyz](https://play.ertdfgcvb.xyz/abc.html) — character set philosophy
- CP437 / PETSCII semigraphics tradition

---

## 文件结构

| 文件 | 职责 |
|---|---|
| `lib/box_chars.py` | 中央字符库：字符集、梯度、边框、情绪选取 API（**唯一数据源**） |
| `procedural/palette.py` | 从 box_chars 导入 `GRADIENTS` 为 `ASCII_GRADIENTS`，提供颜色函数 |
| `procedural/flexible/grammar.py` | 从 box_chars 导入 `CHARSETS`/`BORDER_SETS`，文法规则中的字符选择 |
| `procedural/flexible/pipeline.py` | 装饰精灵渲染（frame、grid_lines、circuit） |
| `lib/effects.py` | 粒子字符集（10 种命名集） |

---

## 1. 字符集（CHARSETS）

`lib/box_chars.py` 定义 37 个命名字符集，按视觉语义分类。一个例子从每类：

| 类别 | 示例名称 | 字符示例 |
|---|---|---|
| Box Drawing 线条 | `box_light` | `─│┌┐└┘├┤┬┴┼` |
| Block Elements | `blocks_full` | `░▒▓█` |
| Geometric Shapes | `geometric_filled` | `■▪▮●▲▼◆` |
| Braille/Dots | `braille` | `⠀⠁⠂⠃⠄⠅⠆⠇⡀⡁...⣿` |
| Typography | `math_operators` | `±×÷∓∞≈≠≤≥≡∝∑∏∫` |
| Mixed | `cp437_box` | 完整 CP437 制图符号 |

```python
from lib.box_chars import get_charset
chars = get_charset("box_light")   # -> "─│┌┐└┘├┤┬┴┼"
```

Run `viz capabilities --format json` for the complete list of all 37 charset definitions.

---

## 2. 密度梯度（GRADIENTS）

从空/稀疏到密/实的字符序列，用于 `char_at_value()` 映射。共 73 种梯度（含 default 别名），覆盖 450+ 个 Unicode 字符。

### char_idx 到字符的映射

渲染时，`renderer.py` 的 `char_at_value(value, gradient_name)` 将 0.0-1.0 的值映射到梯度中的字符：

```python
# value=0.0 -> 空格 (空)
# value=0.5 -> 中间字符
# value=1.0 -> 最密字符 (█ 或 ⣿)
char = gradient[int(value * (len(gradient) - 1))]
```

### 梯度分类示例

| 类别 | 数量 | 示例名称 | 示例梯度 |
|---|---|---|---|
| 经典 ASCII | 5 | `classic` | ` .:-=+*#%@` |
| 方块填充 | 8 | `blocks` | ` ░▒▓█` |
| Box-Drawing | 20 | `box_density` | ` ·┄─┈━░▒▓█` |
| 几何/点阵 | 14 | `braille_density` | ` ⠁⠃⠇⡇⣇⣧⣷⣿` |
| 文字/排版 | 15 | `punctuation` | ` .,;:?!@#%&*█` |
| 混合表现力 | 5 | `cyber` | ` ·-=≡░▒▓█` |

Run `viz capabilities --format json` for the complete list of 73 gradients and all charset/border set definitions.

### 在管线中的使用

梯度名称通过 `grammar.py` 的 `_choose_gradient()` 选择（全部 73 种均在自动选择池中），由 `energy` 和 `structure` 参数驱动权重：

```
高 energy + 高 structure -> box_thick, box_cross, diagonal, blocks
低 energy + 低 structure -> organic, circles, braille_density, sparkles
高 energy + 低 structure -> glitch, cyber, arrows_lg, cp437_retro
低 energy + 高 structure -> dots_density, geometric, vbar, hbar
```

也可通过 Director Mode（CLI `--gradient` 或 JSON `gradient` 字段）精确指定。

---

## 3. 边框字符集（BORDER_SETS）

完整的矩形边框绘制所需字符，含 11 个键位（tl, tr, bl, br, h, v, lt, rt, tt, bt, cross）。

### 6 种边框风格

| 风格 | 角 | 水平 | 垂直 | 交叉 |
|---|---|---|---|---|
| `light` | `┌┐└┘` | `─` | `│` | `┼` |
| `heavy` | `┏┓┗┛` | `━` | `┃` | `╋` |
| `double` | `╔╗╚╝` | `═` | `║` | `╬` |
| `round` | `╭╮╰╯` | `─` | `│` | `┼` |
| `dash_light` | `┌┐└┘` | `┄` | `┆` | `┼` |
| `dash_heavy` | `┏┓┗┛` | `┅` | `┇` | `╋` |

```python
from lib.box_chars import get_border_set
bs = get_border_set("double")
# -> {"h": "═", "v": "║", "tl": "╔", "tr": "╗", ...}
```

---

## 4. 情绪驱动的字符选取

`get_chars_for_mood()` 根据三维参数 (energy, structure, warmth) 返回完整的字符调色板：

```python
from lib.box_chars import get_chars_for_mood
palette = get_chars_for_mood(energy=0.8, structure=0.3, warmth=0.5)
# -> {"gradient": "glitch", "decoration": [...], "particles": "...",
#     "border": "double", "fill": "blocks_ultra"}
```

8 种字符调色板按情绪维度组织（calm_structured, calm_organic, energetic_structured, energetic_chaotic, warm_gentle, cold_sharp, data_dense, minimal），15% 概率随机变异增加多样性。

---

## 5. 装饰与粒子

Grammar 从 `CHARSETS`/`BORDER_SETS` 构建装饰字符池和粒子字符池：

- **装饰字符** (`_choose_decoration_chars()`): 70+ 种组合，按 energy/structure/warmth 分为 8 个池
- **粒子字符** (`_choose_particle_chars()`): 30+ 组字符，7 个池（经典/几何/box/方块/盲文/星星/箭头）
- **命名粒子集** (`lib/effects.py`): 10 种（data, hex, binary, box, blocks, dots, braille, geometric, cross, mixed）
