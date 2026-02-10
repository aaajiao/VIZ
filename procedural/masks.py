"""
空间遮罩 - Spatial Masks

为复合效果提供空间遮罩，控制两个效果在不同区域的混合方式。
遮罩的 char_idx 值 (0-9) 代表混合权重: 0 = 完全效果A, 9 = 完全效果B。

Spatial mask generators for composite effects. The mask's char_idx
value (0-9) represents blend weight: 0 = fully effect_a, 9 = fully effect_b.
"""

import math

from procedural.types import Context, Cell, Buffer
from procedural.core.mathx import clamp, smoothstep
from procedural.core.noise import ValueNoise


class HorizontalSplitMask:
    """水平分割遮罩 - Top vs bottom split"""

    def pre(self, ctx, buffer):
        split = ctx.params.get("mask_split", 0.5)
        softness = ctx.params.get("mask_softness", 0.1)
        anim_speed = ctx.params.get("mask_anim_speed", 0.0)
        if anim_speed > 0 and ctx.time > 0:
            split += 0.15 * math.sin(ctx.time * anim_speed * math.pi * 2)
            split = max(0.1, min(0.9, split))
        return {"split": split, "softness": softness}

    def main(self, x, y, ctx, state):
        v = y / max(ctx.height - 1, 1)
        split = state["split"]
        softness = state["softness"]
        if softness > 0.001:
            t = smoothstep(split - softness, split + softness, v)
        else:
            t = 0.0 if v < split else 1.0
        idx = int(clamp(t * 9, 0, 9))
        gray = int(clamp(t * 255, 0, 255))
        return Cell(char_idx=idx, fg=(gray, gray, gray), bg=None)

    def post(self, ctx, buffer, state):
        pass


class VerticalSplitMask:
    """垂直分割遮罩 - Left vs right split"""

    def pre(self, ctx, buffer):
        split = ctx.params.get("mask_split", 0.5)
        softness = ctx.params.get("mask_softness", 0.1)
        anim_speed = ctx.params.get("mask_anim_speed", 0.0)
        if anim_speed > 0 and ctx.time > 0:
            split += 0.15 * math.sin(ctx.time * anim_speed * math.pi * 2)
            split = max(0.1, min(0.9, split))
        return {"split": split, "softness": softness}

    def main(self, x, y, ctx, state):
        u = x / max(ctx.width - 1, 1)
        split = state["split"]
        softness = state["softness"]
        if softness > 0.001:
            t = smoothstep(split - softness, split + softness, u)
        else:
            t = 0.0 if u < split else 1.0
        idx = int(clamp(t * 9, 0, 9))
        gray = int(clamp(t * 255, 0, 255))
        return Cell(char_idx=idx, fg=(gray, gray, gray), bg=None)

    def post(self, ctx, buffer, state):
        pass


class DiagonalMask:
    """对角分割遮罩 - Diagonal split from top-left to bottom-right"""

    def pre(self, ctx, buffer):
        split = ctx.params.get("mask_split", 0.5)
        softness = ctx.params.get("mask_softness", 0.15)
        angle = ctx.params.get("mask_angle", 0.0)
        anim_speed = ctx.params.get("mask_anim_speed", 0.0)
        if anim_speed > 0 and ctx.time > 0:
            angle += ctx.time * anim_speed * 0.5
        return {"split": split, "softness": softness, "angle": angle}

    def main(self, x, y, ctx, state):
        u = x / max(ctx.width - 1, 1)
        v = y / max(ctx.height - 1, 1)
        angle = state["angle"]
        if abs(angle) > 0.001:
            ca = math.cos(angle)
            sa = math.sin(angle)
            d = (u - 0.5) * ca + (v - 0.5) * sa + 0.5
        else:
            d = (u + v) / 2.0
        split = state["split"]
        softness = state["softness"]
        if softness > 0.001:
            t = smoothstep(split - softness, split + softness, d)
        else:
            t = 0.0 if d < split else 1.0
        idx = int(clamp(t * 9, 0, 9))
        gray = int(clamp(t * 255, 0, 255))
        return Cell(char_idx=idx, fg=(gray, gray, gray), bg=None)

    def post(self, ctx, buffer, state):
        pass


class RadialMask:
    """径向遮罩 - Center vs edges radial gradient"""

    def pre(self, ctx, buffer):
        cx = ctx.params.get("mask_center_x", 0.5)
        cy = ctx.params.get("mask_center_y", 0.5)
        radius = ctx.params.get("mask_radius", 0.5)
        softness = ctx.params.get("mask_softness", 0.15)
        invert = ctx.params.get("mask_invert", False)
        anim_speed = ctx.params.get("mask_anim_speed", 0.0)
        if anim_speed > 0 and ctx.time > 0:
            radius += 0.1 * math.sin(ctx.time * anim_speed * math.pi * 2)
            radius = max(0.05, min(0.9, radius))
        return {
            "cx": cx, "cy": cy, "radius": radius,
            "softness": softness, "invert": invert,
        }

    def main(self, x, y, ctx, state):
        u = x / max(ctx.width - 1, 1)
        v = y / max(ctx.height - 1, 1)
        dx = u - state["cx"]
        dy = v - state["cy"]
        dist = math.sqrt(dx * dx + dy * dy)
        radius = state["radius"]
        softness = state["softness"]
        if softness > 0.001:
            t = smoothstep(radius - softness, radius + softness, dist)
        else:
            t = 0.0 if dist < radius else 1.0
        if state["invert"]:
            t = 1.0 - t
        idx = int(clamp(t * 9, 0, 9))
        gray = int(clamp(t * 255, 0, 255))
        return Cell(char_idx=idx, fg=(gray, gray, gray), bg=None)

    def post(self, ctx, buffer, state):
        pass


class NoiseMask:
    """噪声遮罩 - Organic blobs via ValueNoise fbm"""

    def pre(self, ctx, buffer):
        scale = ctx.params.get("mask_noise_scale", 0.05)
        octaves = ctx.params.get("mask_noise_octaves", 3)
        threshold = ctx.params.get("mask_threshold", 0.5)
        softness = ctx.params.get("mask_softness", 0.15)
        seed_offset = ctx.params.get("mask_seed_offset", 777)
        anim_speed = ctx.params.get("mask_anim_speed", 0.0)
        noise = ValueNoise(seed=ctx.seed + seed_offset)
        # Time offset for organic drifting
        time_offset = ctx.time * anim_speed * 10.0 if anim_speed > 0 else 0.0
        return {
            "noise": noise, "scale": scale, "octaves": octaves,
            "threshold": threshold, "softness": softness,
            "time_offset": time_offset,
        }

    def main(self, x, y, ctx, state):
        noise = state["noise"]
        t_off = state["time_offset"]
        val = noise.fbm(x * state["scale"] + t_off, y * state["scale"] + t_off * 0.7,
                        octaves=state["octaves"])
        threshold = state["threshold"]
        softness = state["softness"]
        if softness > 0.001:
            t = smoothstep(threshold - softness, threshold + softness, val)
        else:
            t = 0.0 if val < threshold else 1.0
        idx = int(clamp(t * 9, 0, 9))
        gray = int(clamp(t * 255, 0, 255))
        return Cell(char_idx=idx, fg=(gray, gray, gray), bg=None)

    def post(self, ctx, buffer, state):
        pass


class SDFMask:
    """SDF形状遮罩 - Circle/box/ring geometric shapes"""

    def pre(self, ctx, buffer):
        shape = ctx.params.get("mask_sdf_shape", "circle")
        cx = ctx.params.get("mask_center_x", 0.5)
        cy = ctx.params.get("mask_center_y", 0.5)
        size = ctx.params.get("mask_sdf_size", 0.3)
        softness = ctx.params.get("mask_softness", 0.05)
        invert = ctx.params.get("mask_invert", False)
        thickness = ctx.params.get("mask_sdf_thickness", 0.05)
        anim_speed = ctx.params.get("mask_anim_speed", 0.0)
        if anim_speed > 0 and ctx.time > 0:
            size += 0.08 * math.sin(ctx.time * anim_speed * math.pi * 2)
            size = max(0.05, min(0.8, size))
        return {
            "shape": shape, "cx": cx, "cy": cy, "size": size,
            "softness": softness, "invert": invert, "thickness": thickness,
        }

    def main(self, x, y, ctx, state):
        u = x / max(ctx.width - 1, 1)
        v = y / max(ctx.height - 1, 1)
        dx = u - state["cx"]
        dy = v - state["cy"]
        shape = state["shape"]
        size = state["size"]

        if shape == "box":
            ax = abs(dx) - size
            ay = abs(dy) - size
            outside = math.sqrt(max(ax, 0.0) ** 2 + max(ay, 0.0) ** 2)
            inside = min(max(ax, ay), 0.0)
            dist = outside + inside
        elif shape == "ring":
            radius = size
            thickness = state["thickness"]
            dist = abs(math.sqrt(dx * dx + dy * dy) - radius) - thickness
        else:
            dist = math.sqrt(dx * dx + dy * dy) - size

        softness = state["softness"]
        if softness > 0.001:
            t = smoothstep(-softness, softness, dist)
        else:
            t = 0.0 if dist < 0.0 else 1.0

        if state["invert"]:
            t = 1.0 - t

        idx = int(clamp(t * 9, 0, 9))
        gray = int(clamp(t * 255, 0, 255))
        return Cell(char_idx=idx, fg=(gray, gray, gray), bg=None)

    def post(self, ctx, buffer, state):
        pass


MASK_REGISTRY = {
    "horizontal_split": HorizontalSplitMask,
    "vertical_split": VerticalSplitMask,
    "diagonal": DiagonalMask,
    "radial": RadialMask,
    "noise": NoiseMask,
    "sdf": SDFMask,
}
