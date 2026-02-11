# Kaomoji System（颜文字系统）

330 颜文字库，22 种情绪分类，支持情感驱动的自动选取和动画渲染。

## 文件结构

| 文件 | 职责 |
|------|------|
| `lib/kaomoji_data.py` | 数据源：22 类 × 15 面孔 + 多行版本 |
| `lib/kaomoji.py` | 渲染引擎：选择 + 绘制 |
| `procedural/layers.py` | 精灵动画：KaomojiSprite 类 |
| `procedural/flexible/grammar.py` | 情绪选取：VAD → mood |

---

## 情绪分类（22 类）

### 正面情绪（6 类，各 15 面孔）

| 类别 | 示例 |
|------|------|
| `happy` | `(^o^)` `(◠‿◠)` `(^_^)` `(◕‿◕)` `(＾▽＾)` |
| `euphoria` | `\(^o^)/` `(≧▽≦)` `ヽ(>∀<☆)ノ` |
| `excitement` | `(*^_^*)` `(^_^)v` `(๑´ڡ`๑)` |
| `love` | `(♡˙︶˙♡)` `(◕‿◕)♡` `(´ε ` )♡` |
| `proud` | `(•̀ᴗ•́)و` `(ง •̀_•́)ง` `` (`・ω・´) `` |
| `relaxed` | `(´ー`)` `(￣▽￣)` `( ˘ω˘ )` |

### 负面情绪（7 类，各 15 面孔）

| 类别 | 示例 |
|------|------|
| `sad` | `(;_;)` `(T_T)` `(ノ_・。)` |
| `angry` | `(╬ Ò﹏Ó)` `(`Д´)` `(＃`Д´)` |
| `anxiety` | `(；´Д`)` `(°△°)` `(´;ω;`)` |
| `fear` | `(ﾟДﾟ;)` `((((；ﾟДﾟ)))` |
| `panic` | `(✖╭╮✖)` `(×_×;)` `Σ(°△°|||)` |
| `disappointed` | `(−_−)` `(-_-;)` `(；一_一)` |
| `lonely` | `(ぼっち)` `(.._.)` `(´・ω・`)` |

### 中性情绪（7 类，各 15 面孔）

| 类别 | 示例 |
|------|------|
| `neutral` | `(._.)` `(-_-)` `(・_・)` |
| `confused` | `(？_？)` `(?_?)` `(⊙_⊙)` |
| `surprised` | `(o.o)` `Σ(゜゜)` `(⊙o⊙)` |
| `sleepy` | `(-.-)zzZ` `( ˘ω˘ )` `(~_~)` |
| `thinking` | `(._.)...` `(・・?)` `(¬_¬)` |
| `embarrassed` | `(*/ω＼*)` `(〃▽〃)` `(^_^;)` |
| `bored` | `(¬_¬)` `(=_=)` `(ー_ー)` |

### 特殊分类（2 类，各 15 面孔）

从正面/负面情绪精选组成的独立分类，用于经典 bull/bear 场景：

| 类别 | 来源 | 示例 |
|------|------|------|
| `bull` | 正面情绪精选 | `(^o^)` `(≧▽≦)` `\\(^o^)/` `(◠‿◠)` `(☆▽☆)` |
| `bear` | 负面情绪精选 | `(;_;)` `(x_x)` `(╥﹏╥)` `(T_T)` `(>_<)` |

---

## 类别归属映射

`MOOD_CATEGORIES` 定义别名归属：

```python
MOOD_CATEGORIES = {
    "bull": ["bull", "happy", "euphoria", "excitement",
             "love", "proud", "relaxed", "excited"],
    "bear": ["bear", "sad", "angry", "fear", "panic",
             "disappointed", "lonely", "anxious"],
    "neutral": ["neutral", "confused", "surprised", "sleepy",
                "thinking", "embarrassed", "bored", "calm",
                "uncertain", "anxiety"],
}
```

---

## 选取流程

### 三级回退策略（`lib/kaomoji.py`）

```
1. 精确匹配 → KAOMOJI_SINGLE[mood]        （15 面孔随机选一）
       ↓ 失败
2. 多行匹配 → KAOMOJI_MULTILINE[mood]     （3 行 ASCII 版本）
       ↓ 失败
3. 父类归属 → _normalize_mood(mood) → bull/bear/neutral
              → KAOMOJI_SINGLE[parent]     （15 面孔随机选一）
```

### VAD → Mood 映射（`grammar.py::_choose_kaomoji_mood`）

3D 最近质心算法：计算输入 (V, A, D) 到 20 个情绪质心的欧几里得距离，选择最近的情绪。

| 情绪 | Valence | Arousal | Dominance |
|------|---------|---------|-----------|
| euphoria | 0.8 | 0.8 | 0.5 |
| happy | 0.6 | 0.0 | 0.3 |
| excitement | 0.5 | 0.7 | 0.4 |
| love | 0.7 | 0.2 | -0.3 |
| proud | 0.5 | 0.3 | 0.8 |
| relaxed | 0.4 | -0.6 | 0.1 |
| angry | -0.6 | 0.7 | 0.7 |
| anxiety | -0.4 | 0.6 | -0.4 |
| fear | -0.7 | 0.7 | -0.7 |
| panic | -0.8 | 0.9 | -0.3 |
| sad | -0.5 | -0.4 | -0.3 |
| lonely | -0.6 | -0.5 | -0.6 |
| disappointed | -0.4 | -0.3 | 0.0 |
| confused | 0.0 | 0.3 | -0.3 |
| surprised | 0.1 | 0.9 | -0.2 |
| thinking | 0.0 | -0.3 | 0.4 |
| embarrassed | -0.2 | 0.3 | -0.6 |
| bored | -0.1 | -0.7 | 0.0 |
| sleepy | 0.1 | -0.8 | -0.3 |
| neutral | 0.0 | 0.0 | 0.0 |

Dominance 轴使情绪选择更精确：高 Dominance 的愤怒与低 Dominance 的焦虑可区分，高 Dominance 的骄傲与低 Dominance 的爱也可区分。

---

## 渲染细节

### 字体

- 主字体：`DejaVuSansMono.ttf`（等宽）
- 字号：`min(200, max(1, 10 * size))`
  - size=1 → 10pt，size=20 → 200pt（上限 200pt）
- 回退：`ImageFont.load_default()`

### 描边效果

1. **轮廓层**：8 方向偏移绘制（`outline_offset = max(1, min(4, 2 * size))`）
   - 颜色：主色的 1/3 亮度（`c // 3`）或自定义 `outline_color`
2. **加粗层**：多次叠加绘制（`bold_range = min(size, 4)`）
   - 颜色：主色

### 多行渲染

- 行高：`max(12, int(10 * size * 1.2))`
- 每行独立描边 + 加粗
- Y 偏移：`current_y = y + line_idx * line_height`

---

## KaomojiSprite 动画

`procedural/layers.py` 中的 `KaomojiSprite` 支持三种动画：

### breathing（呼吸）

```python
scale = 1.0 + amplitude * sin(time * speed)
# 默认: amplitude=0.05, speed=2.0
# 效果: ±5% 大小脉动
```

### floating（浮动）

```python
y_offset = amplitude * sin(time * speed + phase)
# 默认: amplitude=20px, speed=1.0
# 效果: 上下 ±20px 正弦浮动
```

### color_cycle（色彩循环）

```python
hue = (base_hue + time * speed) % 1.0
color = hsv_to_rgb(hue, saturation, value)
# 效果: 色相随时间旋转
```

### 动画组合

精灵可同时应用多个动画（在 `apply_animations(time)` 中依次计算），结果叠加：

```python
anim = sprite.apply_animations(time)
# → {"scale": 1.03, "y_offset": -12.5, "color": (255, 128, 64)}
```

---

## 完整调用链示例

```
输入: text="市场暴跌 恐慌蔓延"

1. text_to_emotion()
   → VAD = (-0.85, +0.80, -0.65)

2. _choose_kaomoji_mood(valence=-0.85, arousal=+0.80, dominance=-0.65)
   → 3D 最近质心: 距 panic(-0.8, 0.9, -0.3) 最近
   → mood = "panic"

3. KAOMOJI_SINGLE["panic"]
   → 15 面孔中随机选一
   → "(×_×;）"

4. KaomojiSprite(x=540, y=540, mood="panic",
                 color=palette["primary"],
                 animations=[floating, breathing])

5. sprite.render(image, time=1.5)
   → 描边 + 加粗 + 浮动偏移
   → 绘制到输出分辨率画布（默认 1080×1080）
```
