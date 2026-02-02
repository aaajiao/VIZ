# Visualizers
可视化生成器目录

## 核心工具

### `universal_viz_system.py` - 通用系统
支持多种内容类型的统一可视化系统。

**用法：**
```bash
python3 viz/universal_viz_system.py <类型> [查询]
```

**支持类型：**
- `market` - 市场与经济
- `art` - 艺术与文化
- `mood` - 个人心情
- `news` - 通用新闻

**示例：**
```bash
python3 viz/universal_viz_system.py market
python3 viz/universal_viz_system.py art "Venice Biennale"
python3 viz/universal_viz_system.py mood
```

### `market_viz_complete.py` - 市场专用版
专门针对市场数据优化的可视化工具。

**特点：**
- 自动获取美股新闻
- 情绪分析（bull/bear/neutral）
- 提取指标（百分比、指数）
- 丰富的 ASCII 装饰

**用法：**
```bash
python3 viz/market_viz_complete.py "US stock market today"
```

### `emotional_market_viz.py` - 情绪化设计版
基于情绪心理学的可视化设计。

**5种情绪状态：**
- euphoria（狂喜）- 纯绿 + 火箭
- excitement（兴奋）- 矩阵绿 + 上箭头  
- anxiety（焦虑）- 橙色 + 闪电
- fear（恐惧）- 红色 + 下箭头
- panic（恐慌）- 血红 + 强故障效果

**特点：**
- 发光文字效果
- 能量波纹
- 故障艺术
- 强烈视觉冲击

### `stock_pixel_ascii.py` - 像素转ASCII
将真实图像逐像素转换为 ASCII 艺术。

**方法：**
- 基于 Ascify-Art 技术
- 逐像素灰度映射
- 保留原图色彩
- 自定义字符集

**用法：**
```python
from viz.stock_pixel_ascii import generate_stock_ascii_viz

generate_stock_ascii_viz(
    source_image='path/to/image.png',
    market_data={...},
    output_path='output.png',
    emotion='bull'
)
```

### 程序化生成引擎

支持动态背景效果和视频输出：

**用法：**
```bash
# 输出 GIF 视频 (5秒, 30fps)
python3 viz/universal_viz_system.py market --video

# 指定效果和时长
python3 viz/universal_viz_system.py mood --video --effect flame --duration 3

# 可复现的结果
python3 viz/universal_viz_system.py art --seed 42
```

**可用效果：**
- `plasma` - 等离子体效果
- `flame` - 火焰效果
- `wave` - 波浪效果
- `moire` - 莫尔纹效果
- `sdf_shapes` - 有符号距离场形状
- `noise_field` - 噪声场效果

**参数说明：**
- `--video` - 输出 GIF 视频而非静态图片
- `--duration N` - 视频时长（秒，默认5）
- `--fps N` - 帧率（默认30）
- `--effect NAME` - 指定背景效果
- `--seed N` - 随机种子（用于可复现结果）

## 依赖

所有可视化工具依赖：
- `lib/kaomoji_library.py` - 颜文字图形库
- `PIL/Pillow` - 图像处理
- `scripts/perplexity-search.sh` - 新闻搜索（可选）

## 输出

生成的图片默认保存在 `/workspace/media/`

## 一键发布

使用 `scripts/post_market_viz.sh` 自动生成并发布到 Instagram。
