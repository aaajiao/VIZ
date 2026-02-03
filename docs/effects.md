# Effects System

程序化效果系统，通过 `pre() → main(x, y) → post()` 三阶段协议生成 ASCII 纹理。

## Effect Protocol

所有效果继承 `BaseEffect`（`procedural/effects/base.py`），实现三个方法：

```python
class BaseEffect:
    def pre(self, ctx: Context, buffer: Buffer) -> dict:
        """预处理：初始化状态（噪声、热量图等），返回 state 字典"""

    def main(self, x: int, y: int, ctx: Context, state: dict) -> Cell:
        """逐像素渲染：返回 Cell(char_idx, fg, bg)"""

    def post(self, ctx: Context, buffer: Buffer, state: dict) -> None:
        """后处理：对整个 buffer 做全局操作（当前所有效果为空）"""
```

- `char_idx`：0-9 整数，渲染器通过 `char_idx / 9.0` 归一化后映射到 ASCII 字符梯度
- `fg`：前景色 `(r, g, b)` 元组，0-255
- `bg`：背景色，`None` 表示透明

## Effect Registry

`procedural/effects/__init__.py` 维护全局注册表：

```python
EFFECT_REGISTRY = {
    'plasma':      PlasmaEffect,
    'flame':       DoomFlameEffect,
    'sdf_shapes':  SDFShapesEffect,
    'noise_field': NoiseFieldEffect,
    'wave':        WaveEffect,
    'moire':       MoireEffect,
    'cppn':        CPPNEffect,
}

effect = get_effect('plasma')  # 工厂函数，返回实例
```

## 七种核心效果

### 1. PlasmaEffect (`procedural/effects/plasma.py`)

等离子体干涉图案 — 四层正弦波叠加产生旋转、脉动的连续梯度。

**算法：**
1. 旋转波：`sin(dot(coord, direction) * 10 * freq + t)` — 方向随时间旋转
2. 径向波：`cos(distance_from_center * 40 * freq + t * 0.7)` — 同心环
3. 网格波：`sin(u * 10 * freq + t) + sin(v * 13 * freq + t * 0.7)` — 正交干涉
4. 对角波：`sin(sqrt(u² + v²) * 15 * freq + t * 1.2)` — 距离场

最终值 = 四层平均，归一化到 [0, 1]。

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `frequency` | 0.01-0.2 | 0.05 | 波纹密度 |
| `speed` | 0.1-5.0 | 1.0 | 动画速度 |
| `color_phase` | 0.0-1.0 | 0.0 | 颜色偏移 |
| `warmth` | 0.0-1.0 | — | 连续色温（柔性管线） |
| `saturation` | 0.0-1.0 | — | 连续饱和度（柔性管线） |

**默认配色：** `"plasma"`（彩虹色系）

---

### 2. DoomFlameEffect (`procedural/effects/flame.py`)

经典 Doom 风格火焰 — 热量从底部生成，向上传播并随机衰减。

**算法：**
1. **底部生成：** `noise(x * 0.05, t) * 40 * intensity + random() * 10 * intensity`
2. **向上传播：** 从下方取样（带 ±1 水平随机偏移）
3. **随机衰减：** `heat[x,y] = max(0, heat[x+1, y+1] - random()*2 - 0.5)`

跨帧维持 heat_map 状态，产生时间连贯性。

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `intensity` | 0.5-3.0 | 1.0 | 火焰强度 |
| `warmth` | 0.0-1.0 | — | 连续色温 |
| `saturation` | 0.0-1.0 | — | 连续饱和度 |

**字符梯度：** `"  ..::░░▒▒▓▓██"`（空白到实心）

**默认配色：** `"heat"`（黑 → 深红 → 红 → 橙 → 黄 → 白）

---

### 3. WaveEffect (`procedural/effects/wave.py`)

多频率正弦波叠加 — 类似水面波纹或声波干涉。

**算法：**
- 对每个波 `i`：`freq_i = frequency * (1 + i * 0.4)`
- 叠加：`wave_sum = Σ sin(y * freq_i + t * speed_i) * amplitude`
- 归一化到 [0, 1]

以 Y 轴为主方向，产生水平波纹效果。

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `wave_count` | 1-10 | 5 | 叠加波数 |
| `frequency` | 0.01-0.2 | 0.1 | 基础频率 |
| `amplitude` | 0.5-3.0 | 1.0 | 波幅 |
| `speed` | 0.1-5.0 | 1.0 | 动画速度 |
| `color_scheme` | — | `"ocean"` | 配色方案 |

---

### 4. MoireEffect (`procedural/effects/moire.py`)

莫尔干涉图案 — 两个径向/角度波场的乘积产生拍频图案。

**算法：**
- 场 A：`cos(atan2(dy_a, dx_a) * freq_a + t * speed_a)`
- 场 B：`cos(atan2(dy_b, dx_b) * freq_b + t * speed_b)`
- 干涉：`value = (wave_a × wave_b + 1) / 2`

使用互质频率（如 8 和 13）避免周期性重复。

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `freq_a` | 1-20 | 8.0 | 场 A 频率 |
| `freq_b` | 1-20 | 13.0 | 场 B 频率 |
| `speed_a` | -5 ~ 5 | 0.5 | 场 A 旋转速度 |
| `speed_b` | -5 ~ 5 | -0.3 | 场 B 旋转速度 |
| `offset_a/b` | -0.5 ~ 0.5 | 0.0 | 中心偏移（不对称） |

**默认配色：** `"rainbow"`

---

### 5. SDFShapesEffect (`procedural/effects/sdf_shapes.py`)

SDF（有符号距离场）几何体 — 多个圆/方块的平滑混合。

**算法：**
1. 随机生成形状位置和半径
2. 逐像素计算 SDF 距离（circle: `length(p - center) - radius`）
3. 平滑并集：`op_smooth_union(d, d_shape, smoothness)` 迭代混合
4. 映射：`value = clamp(1.0 - distance * 5.0, 0, 1)` — 内部亮，外部暗

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `shape_count` | 1-10 | 5 | 形状数量 |
| `shape_type` | circle/box | circle | 形状类型 |
| `radius_min` | 0.02-0.1 | 0.05 | 最小半径 |
| `radius_max` | 0.1-0.3 | 0.15 | 最大半径 |
| `smoothness` | 0.05-0.3 | 0.1 | 混合平滑度 |
| `animate` | bool | True | 启用动画 |
| `speed` | 0.1-5.0 | 1.0 | 动画速度 |

**默认配色：** `"plasma"`

---

### 6. NoiseFieldEffect (`procedural/effects/noise_field.py`)

噪声场可视化 — 支持 FBM（分形布朗运动）和湍流模式。

**三种模式：**
1. **单层噪声** (`octaves=1`)：`noise(nx, ny)` — 平滑斑块
2. **FBM 模式**：多层叠加，频率递增、振幅递减 — 分形细节
3. **湍流模式** (`turbulence=True`)：取绝对值 — 火焰/烟雾效果

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `scale` | 0.01-0.2 | 0.05 | 噪声频率 |
| `octaves` | 1-8 | 4 | FBM 层数 |
| `lacunarity` | 1.5-3.0 | 2.0 | 频率倍增因子 |
| `gain` | 0.3-0.8 | 0.5 | 振幅衰减因子 |
| `animate` | bool | True | 时间动画 |
| `speed` | 0.1-5.0 | 0.5 | 动画速度 |
| `turbulence` | bool | False | 湍流模式 |

**默认配色：** 湍流时 `"fire"`，否则 `"plasma"`

---

### 7. CPPNEffect (`procedural/flexible/cppn.py`)

CPPN（组合模式生成网络）— 随机神经网络产生无限图案变化。

**网络架构：**
- 输入：`[x_norm, y_norm, radius, bias, time_sin, time_cos]`
- 隐藏层：2-5 层 × 4-16 神经元/层
- 输出：4 维 `[char_idx, color1, color2, color3]`
- 激活函数：sin, cos, tanh, abs, identity, gaussian, sigmoid, softplus, sin_abs（每层随机选择）

不需要训练，纯函数映射 `(x, y) → 图案`。不同种子产生完全不同的视觉效果。

---

## 效果组合（CompositeEffect）

`procedural/compositor.py` 提供效果叠加：

```python
composite = CompositeEffect(
    effect_a=PlasmaEffect(),
    effect_b=WaveEffect(),
    mode=BlendMode.SCREEN,
    mix=0.5
)
```

**混合模式：**
- `ADD`：加法混合（c1 + c2，截断到 255）
- `MULTIPLY`：乘法混合（c1 × c2 / 255）
- `SCREEN`：滤色（1 - (1-c1)(1-c2)）
- `OVERLAY`：叠加（按通道条件混合）

`mix` 参数控制 effect_b 的不透明度（0.0-1.0）。

---

## 颜色集成

所有效果支持两种配色方式：

1. **离散色方案**（旧系统）：`value_to_color(value, scheme_name)`
   - 支持：`heat`, `rainbow`, `cool`, `matrix`, `plasma`, `ocean`, `fire`

2. **连续色温**（柔性管线）：`value_to_color_continuous(value, warmth, saturation)`
   - `warmth`：0.0（冷蓝）→ 1.0（暖红）
   - `saturation`：0.0（灰）→ 1.0（纯色）

当 `ctx.params` 包含 `warmth` 时自动切换到连续模式。

## 配色方案详细映射

| 方案 | 渐变路径 |
|------|----------|
| `heat` | 黑 → 深红 → 红 → 橙 → 黄 → 白 |
| `rainbow` | 红 → 橙 → 黄 → 绿 → 蓝 → 紫 |
| `cool` | 黑 → 深蓝 → 青 → 白 |
| `matrix` | 黑 → 深绿 → 绿 → 亮绿 |
| `plasma` | 多色 HSV 循环 |
| `ocean` | 深海蓝 → 青 → 海面白 |
| `fire` | 黑 → 暗红 → 橙红 → 亮黄 → 白黄 |
