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
    'plasma':          PlasmaEffect,
    'flame':           DoomFlameEffect,
    'sdf_shapes':      SDFShapesEffect,
    'noise_field':     NoiseFieldEffect,
    'wave':            WaveEffect,
    'moire':           MoireEffect,
    'cppn':            CPPNEffect,
    'ten_print':       TenPrintEffect,
    'game_of_life':    GameOfLifeEffect,
    'donut':           DonutEffect,
    'mod_xor':         ModXorEffect,
    'wireframe_cube':  WireframeCubeEffect,
    'chroma_spiral':   ChromaSpiralEffect,
    'wobbly':          WobblyEffect,
    'sand_game':       SandGameEffect,
    'slime_dish':      SlimeDishEffect,
    'dyna':            DynaEffect,
}

effect = get_effect('plasma')  # 工厂函数，返回实例
```

## 基础效果（1-7）

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

## 扩展效果（8-17）

### 8. TenPrintEffect (`procedural/effects/ten_print.py`)

经典 Commodore 64 迷宫 — `10 PRINT CHR$(205.5+RND(1)); : GOTO 10` 的 ASCII 实现。

**算法：**
1. 屏幕分割为 `cell_size × cell_size` 网格
2. ValueNoise 为每个网格单元选择 `/` 或 `\` 对角线
3. 逐像素计算到对角线距离，映射为亮度
4. 列方向时间偏移实现滚动动画

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `cell_size` | 4-12 | 6 | 网格单元大小 |
| `probability` | 0.3-0.7 | 0.5 | 选择 `\` 的概率 |
| `speed` | 0.1-5.0 | 1.0 | 动画速度 |

**默认配色：** `"matrix"`

---

### 9. GameOfLifeEffect (`procedural/effects/game_of_life.py`)

Conway 生命游戏 — B3/S23 规则细胞自动机，追踪存活年龄映射颜色亮度。

**算法：**
1. ValueNoise 生成有机分布的初始种子（`density` 控制填充比例）
2. 每帧按 `speed` 推进若干代（B3/S23 规则，环形拓扑）
3. 存活细胞年龄递增 → 年龄越大字符越亮
4. 死亡细胞周围有微弱辉光（基于邻居数）

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `density` | 0.3-0.7 | 0.4 | 初始填充比例 |
| `speed` | 1.0-20.0 | 5.0 | 每秒代数 |
| `wrap` | bool | True | 环形拓扑（边界环绕） |

**默认配色：** `"matrix"`

---

### 10. DonutEffect (`procedural/effects/donut.py`)

旋转甜甜圈 — 经典 `donut.c` 算法的 ASCII 缓冲区实现。

**算法：**
1. pre() 遍历环面参数空间 (theta × phi)
2. 3D 旋转变换（绕 X、Z 轴）+ 透视投影到 2D
3. Z-buffer 去遮挡，表面法线点积光源方向 → 亮度
4. main() 查表输出字符和颜色

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `R1` | 0.5-3.0 | 1.0 | 小半径（截面半径） |
| `R2` | 1.0-5.0 | 2.0 | 大半径（环心距） |
| `rotation_speed` | 0.1-5.0 | 1.0 | 旋转速度 |
| `light_x/y/z` | — | 0, 1, -1 | 光源方向分量 |

**默认配色：** `"heat"`

---

### 11. ModXorEffect (`procedural/effects/mod_xor.py`)

模运算/异或分形 — 整数位运算产生自相似分形图案（如 Sierpinski 三角形）。

**算法：**
- 核心：`(x OP y) % modulus`，OP 为 XOR/AND/OR
- 多层叠加：每层不同模数偏移 `modulus + layer * 7`
- 时间偏移坐标实现滚动动画

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `modulus` | 2-64 | 16 | 模数 |
| `operation` | xor/and/or | xor | 位运算类型 |
| `layers` | 1-3 | 1 | 叠加层数 |
| `speed` | 0.1-5.0 | 0.5 | 动画速度 |
| `zoom` | 0.5-3.0 | 1.0 | 缩放级别 |

**默认配色：** `"rainbow"`

---

### 12. WireframeCubeEffect (`procedural/effects/wireframe_cube.py`)

3D 线框立方体 — 距离场渲染旋转线框几何体。

**算法：**
1. 8 个顶点经三轴旋转 → 透视投影到 2D
2. 逐像素计算到 12 条投影棱的最小 SDF 距离
3. 距离 < thickness 为全亮，之后按距离衰减

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `rotation_speed_x` | 0.1-3.0 | 0.7 | X 轴旋转速度 |
| `rotation_speed_y` | 0.1-3.0 | 1.0 | Y 轴旋转速度 |
| `rotation_speed_z` | 0.1-3.0 | 0.3 | Z 轴旋转速度 |
| `scale` | 0.1-0.6 | 0.3 | 立方体缩放 |
| `edge_thickness` | 0.005-0.05 | 0.015 | 边线粗细 |

**默认配色：** `"cool"`

---

### 13. ChromaSpiralEffect (`procedural/effects/chroma_spiral.py`)

色差螺旋 — 极坐标螺旋加 RGB 通道色差分离。

**算法：**
1. 坐标转极坐标 `(radius, angle)`
2. 螺旋值：`fract(angle/TAU * arms + radius * tightness + t)`
3. RGB 三通道各施加不同半径/角度偏移 → 色差效果
4. Smoothstep 曲线锐化过渡

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `arms` | 1-8 | 3 | 螺旋臂数 |
| `tightness` | 0.1-2.0 | 0.5 | 螺旋紧密度 |
| `speed` | 0.1-5.0 | 1.0 | 动画速度 |
| `chroma_offset` | 0.0-0.3 | 0.1 | 色差偏移量 |

**默认配色：** 直接 RGB（独立计算三通道）

---

### 14. WobblyEffect (`procedural/effects/wobbly.py`)

域扭曲 — 迭代噪声位移产生有机流体扭曲（参考 Inigo Quilez warp 技术）。

**算法：**
1. 归一化坐标乘以 `warp_freq`
2. 迭代 `iterations` 次：用两个独立噪声实例采样 (dx, dy) 位移
3. 累加位移 `px += dx * warp_amount`
4. 在扭曲后的坐标处采样 FBM 噪声（3 层）得到最终值

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `warp_amount` | 0.1-1.0 | 0.4 | 位移幅度 |
| `warp_freq` | 0.01-0.1 | 0.03 | 扭曲噪声频率 |
| `iterations` | 1-3 | 2 | 扭曲迭代次数 |
| `speed` | 0.1-5.0 | 0.5 | 动画速度 |

**默认配色：** `"ocean"`

---

### 15. SandGameEffect (`procedural/effects/sand_game.py`)

落沙游戏 — 粒子下落与堆积模拟。

**算法：**
1. 每帧在顶行随机生成粒子（`spawn_rate` 概率）
2. 从底向上扫描，随机化水平顺序避免方向偏差
3. 物理规则：下方空 → 直落；下方占 → 尝试左下/右下滑落；全堵 → 静止
4. 粒子类型决定颜色（暖沙/红沙/蓝灰三种）

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `spawn_rate` | 0.1-0.8 | 0.3 | 生成概率 |
| `gravity_speed` | 1-5 | 2 | 每帧物理步数 |
| `particle_types` | 1-3 | 2 | 颜色类型数量 |

**默认配色：** 固定三种沙色（暖沙/红沙/蓝灰）

---

### 16. SlimeDishEffect (`procedural/effects/slime_dish.py`)

黏菌模拟 — Physarum 多头绒泡菌的代理模拟，产生有机分支网络。

**算法：**
1. N 个代理各有位置和朝向角
2. 每步：感知前方三方向（前、左前、右前）化学轨迹浓度 → 转向信号最强方向 → 前进 → 沉积
3. 轨迹地图：3×3 均值模糊扩散 + 衰减率衰减
4. 轨迹浓度映射到字符密度和颜色

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `agent_count` | 500-5000 | 2000 | 代理数量 |
| `sensor_distance` | 3-15 | 9 | 感知距离 |
| `sensor_angle` | 0.2-1.0 | 0.4 | 感知器张角（弧度） |
| `decay_rate` | 0.9-0.99 | 0.95 | 轨迹衰减率 |
| `speed` | 1-5 | 3 | 每帧模拟步数 |

**默认配色：** `"cool"`

---

### 17. DynaEffect (`procedural/effects/dyna.py`)

动态吸引子波干涉 — 多个运动吸引子产生正弦波叠加干涉图案。

**算法：**
1. N 个吸引子各有位置和速度，在画布内弹跳或环绕移动
2. 每像素：计算到所有吸引子的距离
3. 叠加 `sin(distance * frequency * TAU / width)` 得到干涉值
4. 归一化到 [0, 1] 映射字符和颜色

**参数：**

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `attractor_count` | 2-8 | 4 | 吸引子数量 |
| `frequency` | 0.1-2.0 | 0.5 | 波频率 |
| `speed` | 0.1-5.0 | 1.0 | 吸引子移动速度 |
| `bounce` | bool | True | 弹跳(true)或环绕(false) |

**默认配色：** `"plasma"`

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
