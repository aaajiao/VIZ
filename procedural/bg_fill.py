"""
背景填充第二渲染通道 - Background Fill Second Render Pass

在临时 buffer 上跑一个真实 effect（带 variant + transform），提取 char_idx 作为强度值，
通过 color scheme 着色后 dim，作为主 buffer 的背景。

Background fill runs a second effect on a temporary buffer, extracts char_idx
as intensity, maps through color scheme, dims, and writes to main buffer bg.

用法::

    from procedural.bg_fill import bg_fill

    bg_fill(buffer, w, h, seed, spec)
"""

import random

from procedural.types import Context, Cell, Buffer
from procedural.effects import EFFECT_REGISTRY, get_effect
from procedural.palette import value_to_color, value_to_color_continuous

# 轻量级 effect 候选池 (纯逐像素数学，优先选择)
# 排除 game_of_life, sand_game, slime_dish, dyna (pre() 跑模拟，太重)
_LIGHTWEIGHT_EFFECTS = {
    "plasma", "wave", "noise_field", "moire", "mod_xor",
    "chroma_spiral", "wobbly", "ten_print", "sdf_shapes", "cppn",
}
_MIDWEIGHT_EFFECTS = {"flame", "donut", "wireframe_cube"}
_HEAVY_EFFECTS = {"game_of_life", "sand_game", "slime_dish", "dyna"}


def bg_fill(buffer, w, h, seed, spec):
    """
    背景填充第二渲染通道 - Background fill via second render pass

    Args:
        buffer: 主 buffer (会被修改, 仅修改 bg=None 的 cell)
        w: buffer 宽度
        h: buffer 高度
        seed: 随机种子
        spec: bg_fill 规格 dict，包含:
            - effect: 背景 effect 名称
            - effect_params: effect 参数 dict
            - transforms: 变换列表 [{type, ...}]
            - postfx: 后处理列表 [{type, ...}]
            - mask: 遮罩规格 {type, ...} 或 None
            - color_mode: "scheme" 或 "continuous"
            - color_scheme: 颜色方案名称
            - warmth: 色温
            - saturation: 饱和度
            - dim: 亮度衰减系数 (0~1)
    """
    if not spec:
        return

    effect_name = spec.get("effect", "noise_field")
    effect_params = spec.get("effect_params", {})
    transforms = spec.get("transforms", [])
    postfx_list = spec.get("postfx", [])
    mask_spec = spec.get("mask")
    color_mode = spec.get("color_mode", "scheme")
    color_scheme = spec.get("color_scheme", "heat")
    warmth = spec.get("warmth", 0.5)
    saturation = spec.get("saturation", 0.9)
    dim = spec.get("dim", 0.30)
    time = spec.get("_time", 0.0)

    # 1. 实例化背景 effect
    bg_effect = _create_effect(effect_name, seed)
    if bg_effect is None:
        return

    # 2. 用 TransformedEffect 包装变换
    if transforms:
        bg_effect = _wrap_transforms(bg_effect, transforms)

    # 3. 创建临时 buffer 和 Context
    bg_seed = seed ^ 0xBF11  # 确保背景与前景图案不同但可重现
    rng = random.Random(bg_seed)
    ctx = Context(
        width=w,
        height=h,
        time=time,
        frame=0,
        seed=bg_seed,
        rng=rng,
        params=effect_params,
    )

    tmp_buffer = [
        [Cell(char_idx=0, fg=(0, 0, 0), bg=None) for _ in range(w)]
        for _ in range(h)
    ]

    # 4. 跑 bg_effect.pre() + 逐像素 bg_effect.main()
    state = bg_effect.pre(ctx, tmp_buffer)
    if state is None:
        state = {}

    for y in range(h):
        for x in range(w):
            cell = bg_effect.main(x, y, ctx, state)
            if cell is not None:
                tmp_buffer[y][x] = cell

    bg_effect.post(ctx, tmp_buffer, state)

    # 5. 对临时 buffer 施加 postfx
    if postfx_list:
        from procedural.postfx import POSTFX_REGISTRY
        for fx in postfx_list:
            fx_type = fx.get("type", "")
            fx_fn = POSTFX_REGISTRY.get(fx_type)
            if fx_fn:
                fx_kwargs = {k: v for k, v in fx.items() if k != "type"}
                fx_kwargs["_time"] = time
                fx_fn(tmp_buffer, **fx_kwargs)

    # 6. 生成 mask 强度图 (可选)
    mask_buffer = None
    if mask_spec:
        mask_buffer = _generate_mask(mask_spec, w, h, ctx)

    # 7. 遍历主 buffer，对 bg=None 的 cell 填充背景
    for y in range(h):
        for x in range(w):
            cell = buffer[y][x]
            if cell.bg is not None:
                continue

            # 从临时 buffer 读取 char_idx 归一化为 value
            tmp_cell = tmp_buffer[y][x]
            value = tmp_cell.char_idx / 9.0
            value = max(0.0, min(1.0, value))

            # mask 调制
            if mask_buffer is not None:
                mask_val = mask_buffer[y][x].char_idx / 9.0
                # mask 调制: 高 mask 值保留更多背景强度
                value = value * (0.3 + 0.7 * mask_val)

            # 着色
            if color_mode == "continuous":
                rgb = value_to_color_continuous(value, warmth, saturation)
            else:
                rgb = value_to_color(value, color_scheme)

            # dim 到指定亮度
            r, g, b = rgb
            r = int(r * dim)
            g = int(g * dim)
            b = int(b * dim)

            # 与 fg 暗色按 8:2 混合
            fr, fg_, fb = cell.fg
            dr, dg, db = fr >> 3, fg_ >> 3, fb >> 3
            r = int(r * 0.8 + dr * 0.2)
            g = int(g * 0.8 + dg * 0.2)
            b = int(b * 0.8 + db * 0.2)

            # 确保不全黑
            if r + g + b < 15:
                r = max(r, 5)
                g = max(g, 5)
                b = max(b, 5)

            cell.bg = (r, g, b)


def _create_effect(name, seed):
    """创建 effect 实例 - Create effect instance"""
    if name == "cppn":
        try:
            from procedural.flexible.cppn import CPPNEffect
            return CPPNEffect(seed=seed ^ 0xCE, num_hidden=3, layer_size=8)
        except ImportError:
            pass

    if name in EFFECT_REGISTRY:
        return get_effect(name)

    # fallback
    if "noise_field" in EFFECT_REGISTRY:
        return get_effect("noise_field")
    return None


def _wrap_transforms(effect, transforms):
    """用 TransformedEffect 包装变换 - Wrap effect with transforms"""
    from procedural.transforms import TransformedEffect, TRANSFORM_REGISTRY

    chain = []
    for t in transforms:
        t_type = t.get("type", "")
        t_fn = TRANSFORM_REGISTRY.get(t_type)
        if t_fn:
            kwargs = {k: v for k, v in t.items() if k != "type"}
            chain.append((t_fn, kwargs))

    if chain:
        return TransformedEffect(inner_effect=effect, transforms=chain)
    return effect


def _generate_mask(mask_spec, w, h, ctx):
    """生成 mask buffer - Generate mask buffer"""
    from procedural.masks import MASK_REGISTRY

    mask_type = mask_spec.get("type", "radial")
    mask_cls = MASK_REGISTRY.get(mask_type)
    if mask_cls is None:
        return None

    # 将 mask 参数注入 ctx.params
    mask_ctx_params = dict(ctx.params)
    for k, v in mask_spec.items():
        if k != "type":
            mask_ctx_params["mask_" + k] = v
    mask_ctx = Context(
        width=w,
        height=h,
        time=ctx.time,
        frame=ctx.frame,
        seed=ctx.seed,
        rng=random.Random(ctx.seed ^ 0xAA),
        params=mask_ctx_params,
    )

    mask_inst = mask_cls()
    mask_buffer = [
        [Cell(char_idx=0, fg=(0, 0, 0), bg=None) for _ in range(w)]
        for _ in range(h)
    ]

    state = mask_inst.pre(mask_ctx, mask_buffer)
    if state is None:
        state = {}

    for y in range(h):
        for x in range(w):
            cell = mask_inst.main(x, y, mask_ctx, state)
            if cell is not None:
                mask_buffer[y][x] = cell

    mask_inst.post(mask_ctx, mask_buffer, state)
    return mask_buffer
