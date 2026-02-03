# CLI Entry Points（命令行入口）

项目提供 5 个独立入口脚本，各自面向不同使用场景。

## 入口总览

| 脚本 | 用途 | 管线 |
|------|------|------|
| `demo_flexible.py` | 柔性系统演示（推荐） | FlexiblePipeline |
| `universal_viz_system.py` | 通用可视化（4 种内容类型） | Engine + 手动编排 |
| `emotional_market_viz.py` | 市场情绪专用（5 种状态） | Engine + 手动编排 |
| `market_viz_complete.py` | 完整市场管线（含新闻获取） | Engine + 手动编排 |
| `stock_pixel_ascii.py` | 图片转 ASCII | PIL 像素处理 |

---

## 1. demo_flexible.py

**推荐入口** — 展示柔性输出系统的完整能力。

### 基本用法

```bash
# 从情绪名生成
python3 demo_flexible.py --emotion euphoria --seed 42

# 从文本推断情绪
python3 demo_flexible.py --text "市场暴跌 恐慌蔓延"

# 直接指定 VAD 向量
python3 demo_flexible.py --vad 0.5,-0.3,0.2
```

### 模式

**单帧模式**（默认）：
```bash
python3 demo_flexible.py --emotion joy --seed 42
# → media/flexible_20260203_120000.png
```

**多变体模式**：
```bash
python3 demo_flexible.py --text "hope" --variants 5
# → 5 张不同种子的 PNG，相同情绪不同组合
```

**动画模式**：
```bash
python3 demo_flexible.py --emotion calm --video --duration 3 --fps 15
# → media/flexible_20260203_120000.gif
```

**分析模式**（不生成图片）：
```bash
python3 demo_flexible.py --analyze --text "暴涨 狂热 突破"
# 输出:
#   VAD 向量:
#     Valence:  +0.750
#     Arousal:  +0.800
#     Dominance: +0.350
#   视觉参数:
#     warmth       0.875
#     saturation   0.900
#     ...
```

**列出所有情绪**：
```bash
python3 demo_flexible.py --list-emotions
```

### 完整参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `--text` | str | — | 输入文本（自动推断情绪） |
| `--emotion` | str | — | 情绪名称（joy, fear, panic, ...） |
| `--vad` | str | — | VAD 向量（逗号分隔，如 `0.5,-0.3,0.2`） |
| `--seed` | int | auto | 随机种子 |
| `--variants` | int | 1 | 变体数量 |
| `--video` | flag | — | 生成 GIF 动画 |
| `--duration` | float | 3.0 | 动画时长（秒） |
| `--fps` | int | 15 | 动画帧率 |
| `--title` | str | auto | 标题文字 |
| `--output-dir` | str | ./media | 输出目录 |
| `--list-emotions` | flag | — | 列出预定义情绪 |
| `--analyze` | flag | — | 分析模式（不生成图片） |

---

## 2. universal_viz_system.py

通用可视化系统，支持 4 种内容类型，手动编排引擎和精灵。

### 基本用法

```bash
# 市场可视化
python3 universal_viz_system.py market

# 艺术可视化
python3 universal_viz_system.py art "Venice Biennale"

# 情绪可视化
python3 universal_viz_system.py mood --seed 42

# 新闻可视化（含动画）
python3 universal_viz_system.py news "AI breakthroughs" --video --duration 5
```

### 内容类型

| 类型 | 配色 | 颜文字 | 场景 |
|------|------|--------|------|
| `market` | 牛市绿/熊市红/中性橙 | 情绪驱动 | 股市数据 |
| `art` | 品红/青色 | 艺术表情 | 文化展览 |
| `mood` | 蓝/青色 | happy/sad/thinking | 个人情绪 |
| `news` | 绿/青色 | neutral/thinking/surprised | 新闻资讯 |

### 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `<type>` | 位置参数 | 必选 | market / art / mood / news |
| `[query]` | 位置参数 | — | 搜索关键词 |
| `--video` | flag | — | 输出 GIF |
| `--duration` | float | 5.0 | 视频时长 |
| `--fps` | int | 30 | 帧率 |
| `--effect` | str | plasma | 背景效果名 |
| `--seed` | int | auto | 随机种子 |

### 视觉组成

- 程序化背景效果（6 种可选）
- 6 个分布式颜文字 + 1 个中心大颜文字
- ASCII 纹理层 + 粒子装饰
- 网格背景 + 角落装饰

---

## 3. emotional_market_viz.py

5 种市场情绪状态的专用可视化。

### 用法

```bash
python3 emotional_market_viz.py euphoria --seed 42
python3 emotional_market_viz.py panic --video --duration 3 --fps 15
```

### 情绪配色

| 情绪 | 颜色 | 符号 | 含义 |
|------|------|------|------|
| `euphoria` | 绿/黄 | 🚀 | 强势牛市 |
| `excitement` | 亮绿 | ↑ | 温和上涨 |
| `anxiety` | 橙色 | ⚡ | 市场波动 |
| `fear` | 红色 | ↓ | 下跌趋势 |
| `panic` | 深红 | ⚠️ | 市场崩盘 |

---

## 4. market_viz_complete.py

端到端市场管线：获取新闻 → 情绪分析 → 生成可视化。

### 用法

```bash
# 默认市场关键词
python3 market_viz_complete.py

# 自定义查询
python3 market_viz_complete.py "S&P 500 rally today"

# 动画版本
python3 market_viz_complete.py "Bitcoin surge" --video --fps 20
```

内置情绪分析判断 bull/bear/neutral，自动选取对应配色和颜文字。

可选外部依赖：`/workspace/scripts/perplexity-search.sh`（新闻获取）。

---

## 5. stock_pixel_ascii.py

将真实股票图表图片转换为 ASCII 艺术。

### 字符集

| 名称 | 字符 | 风格 |
|------|------|------|
| `classic` | 完整 ASCII 梯度 | 经典 |
| `simple` | ` .:-=+*#%@` | 简约 |
| `blocks` | `░▒▓█` | 方块 |
| `bull` | ` .+*$↑▲🚀` | 牛市主题 |
| `bear` | ` .+*$↓▼📉` | 熊市主题 |
| `numbers` | `0123456789` | 数字 |
| `money` | `¥$€£₿` | 货币符号 |

### 用法

```python
from stock_pixel_ascii import generate_stock_ascii_viz

generate_stock_ascii_viz(
    source_image='chart.png',
    market_data={'symbol': 'SPY', 'sentiment': 'bull'},
    output_path='output.png',
    emotion='bull'
)
```

---

## 输出规格

所有入口共用：

| 项 | 值 |
|------|------|
| 输出格式 | PNG (quality=95) 或 GIF |
| 画布尺寸 | 1080 × 1080 像素 |
| 默认目录 | `./media/` |
| 文件命名 | `{type}_{timestamp}.{png\|gif}` |
| 可复现性 | `--seed` 参数控制 |

---

## 入口选择指南

| 需求 | 推荐入口 | 命令 |
|------|----------|------|
| 从情绪生成单张图 | `demo_flexible.py` | `--emotion euphoria` |
| 同情绪多变体 | `demo_flexible.py` | `--text "hope" --variants 5` |
| 情绪动画 | `demo_flexible.py` | `--emotion joy --video` |
| 分析文本情绪 | `demo_flexible.py` | `--analyze --text "暴涨"` |
| 市场/艺术/情绪/新闻 | `universal_viz_system.py` | `market` / `art` / `mood` / `news` |
| 市场情绪专题 | `emotional_market_viz.py` | `euphoria` / `panic` |
| 完整市场管线 | `market_viz_complete.py` | `"SPY rally"` |
| 图片转 ASCII | `stock_pixel_ascii.py` | Python API |
