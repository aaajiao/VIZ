"""
柔性管线 - Flexible Pipeline

编排所有 flexible 模块，实现从文本输入到千变万化输出的完整流程。

流程::

    text / emotion_name / EmotionVector
        ↓
    EmotionVector (VAD 连续空间)
        ↓
    to_visual_params() (连续参数)
        ↓  + NoiseModulator (参数漂移)
    VisualGrammar.generate() (文法组合)
        ↓
    SceneSpec (完整渲染规格)
        ↓
    Engine.render_frame/render_video (渲染)
        ↓
    PNG / GIF 输出

用法::

    from procedural.flexible.pipeline import FlexiblePipeline

    pipe = FlexiblePipeline(seed=42)

    # 方式 1: 从文本生成
    img = pipe.generate(text="market crash fears rising")

    # 方式 2: 从情绪名称生成
    img = pipe.generate(emotion="euphoria")

    # 方式 3: 从 VAD 向量生成
    from procedural.flexible.emotion import EmotionVector
    ev = EmotionVector(valence=-0.5, arousal=0.8, dominance=-0.3)
    img = pipe.generate(emotion_vector=ev)

    # 方式 4: 生成动画
    frames = pipe.generate_video(text="volatile market", duration=3.0, fps=15)

    # 方式 5: 批量生成不同变体
    for i in range(10):
        img = pipe.generate(text="hope", seed=i)
        img.save(f"variant_{i}.png")
"""

from __future__ import annotations

import os
import random
import sys
from datetime import datetime
from typing import Any, cast

from PIL import Image

from procedural.engine import Engine
from procedural.effects import EFFECT_REGISTRY, get_effect
from procedural.compositor import CompositeEffect, MaskedCompositeEffect, BlendMode
from procedural.transforms import TransformedEffect, TRANSFORM_REGISTRY
from procedural.masks import MASK_REGISTRY
from procedural.layouts import (
    random_scatter,
    grid_with_jitter,
    spiral_layout,
    force_directed_layout,
    LAYOUT_PRESETS,
)
from procedural.layers import TextSprite, KaomojiSprite

from .emotion import (
    EmotionVector,
    text_to_emotion,
    emotion_from_name,
    VAD_ANCHORS,
)
from .color_space import ContinuousColorSpace
from .modulator import modulate_visual_params
from .grammar import VisualGrammar, SceneSpec
from .cppn import CPPNEffect
from .decorations import build_decoration_sprites


class FlexiblePipeline:
    """
    柔性管线 - 编排所有模块实现千变万化输出

    属性:
        seed: 主随机种子
        internal_size: 内部渲染分辨率
        output_size: 输出分辨率
        drift_amount: 参数漂移强度 (0=无漂移, 1=最大)
    """

    def __init__(
        self,
        seed: int | None = None,
        internal_size: tuple[int, int] = (160, 160),
        output_size: tuple[int, int] = (1080, 1080),
        drift_amount: float = 0.2,
    ):
        if seed is None:
            seed = random.randint(0, 999999)
        self.seed = seed
        self.internal_size = internal_size
        self.output_size = output_size
        self.drift_amount = drift_amount

        self._rng = random.Random(seed)
        self._color_space = ContinuousColorSpace()
        self.last_frames: list[Image.Image] | None = None

    def generate(
        self,
        text: str | None = None,
        emotion: str | None = None,
        emotion_vector: EmotionVector | None = None,
        seed: int | None = None,
        title: str | None = None,
        output_path: str | None = None,
        content: dict[str, Any] | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> Image.Image:
        """
        生成单帧可视化

        输入 (三选一):
            text: 文本 (自动推断情绪)
            emotion: 情绪名称 (如 'joy', 'fear', 'bull')
            emotion_vector: 直接提供 VAD 向量

        其他参数:
            seed: 覆盖种子 (不同种子 → 不同变体)
            title: 显示标题文字
            output_path: 自动保存路径

        返回:
            PIL Image
        """
        if seed is None:
            seed = self._rng.randint(0, 999999)

        # === 1. 确定情感向量 ===
        ev = self._resolve_emotion(text, emotion, emotion_vector)

        # === 2. 转换为连续视觉参数 ===
        visual_params = ev.to_visual_params()

        # === 3. 噪声调制 (单帧用 t=0 的调制) ===
        if self.drift_amount > 0:
            visual_params = modulate_visual_params(
                visual_params,
                t=0.0,
                drift_amount=self.drift_amount,
                seed=seed,
            )

        # === 4. 文法生成场景规格 ===
        grammar = VisualGrammar(seed=seed)
        spec = grammar.generate(
            energy=visual_params.get("energy", 0.5),
            warmth=visual_params.get("warmth", 0.5),
            structure=visual_params.get("structure", 0.5),
            intensity=visual_params.get("intensity", 0.5),
            valence=visual_params.get("valence", 0.0),
            arousal=visual_params.get("arousal", 0.0),
            dominance=visual_params.get("dominance", 0.0),
        )

        # === 4b. Place content data ===
        if content:
            grammar.place_content(spec, content, visual_params)

        # === 4c. Apply user overrides ===
        if overrides:
            self._apply_overrides(spec, overrides)

        # === 5. 构建效果 ===
        effect = self._build_effect(spec, visual_params, seed)

        # === 6. 构建精灵 ===
        sprites = self._build_sprites(spec, visual_params, seed, title)

        # === 7. 生成调色板 ===
        palette = self._color_space.generate_palette(
            warmth=spec.warmth,
            saturation=spec.saturation,
            brightness=spec.brightness,
        )

        # === 8. 渲染 ===
        engine = Engine(
            internal_size=self.internal_size,
            output_size=self.output_size,
            gradient_name=spec.gradient_name,
            color_scheme=spec.color_scheme,
            sharpen=spec.sharpen,
            contrast=spec.contrast,
        )

        # 合并效果参数和色温参数
        # 注意：overlay_params 也合并进来，使复合效果的两个子效果
        # 都能从 ctx.params 中找到自己的参数
        render_params = {}
        for k, v in spec.bg_params.items():
            render_params[k] = v
            render_params["bg_" + k] = v
        if spec.overlay_params:
            for k, v in spec.overlay_params.items():
                if k not in render_params:
                    render_params[k] = v
                render_params["overlay_" + k] = v
        render_params["warmth"] = visual_params.get("warmth", 0.5)
        render_params["saturation"] = visual_params.get("saturation", 0.9)
        render_params["brightness"] = visual_params.get("brightness", 0.8)

        # Pass postfx chain and mask params to engine
        if spec.postfx_chain:
            render_params["_postfx_chain"] = spec.postfx_chain
        if spec.mask_params:
            render_params.update(spec.mask_params)

        # Pass bg_fill spec to engine
        if spec.bg_fill_spec:
            render_params["_bg_fill_spec"] = spec.bg_fill_spec

        img = engine.render_frame(
            effect=effect,
            sprites=sprites,
            time=0.0,
            frame=0,
            seed=seed,
            params=render_params,
        )

        # === 9. 保存 (如果指定路径) ===
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            img.save(output_path, quality=95)
            print(f"已保存: {output_path}", file=sys.stderr)

        return img

    def generate_video(
        self,
        text: str | None = None,
        emotion: str | None = None,
        emotion_vector: EmotionVector | None = None,
        seed: int | None = None,
        title: str | None = None,
        duration: float = 3.0,
        fps: int = 15,
        output_path: str | None = None,
        content: dict[str, Any] | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> list[Image.Image]:
        """
        生成动画序列

        参数同 generate()，额外:
            duration: 时长 (秒)
            fps: 帧率
            output_path: GIF 保存路径

        返回:
            帧列表
        """
        if seed is None:
            seed = self._rng.randint(0, 999999)

        ev = self._resolve_emotion(text, emotion, emotion_vector)
        visual_params = ev.to_visual_params()

        grammar = VisualGrammar(seed=seed)
        spec = grammar.generate(
            energy=visual_params.get("energy", 0.5),
            warmth=visual_params.get("warmth", 0.5),
            structure=visual_params.get("structure", 0.5),
            intensity=visual_params.get("intensity", 0.5),
            valence=visual_params.get("valence", 0.0),
            arousal=visual_params.get("arousal", 0.0),
            dominance=visual_params.get("dominance", 0.0),
        )

        # Place content data
        if content:
            grammar.place_content(spec, content, visual_params)

        # Apply user overrides
        if overrides:
            self._apply_overrides(spec, overrides)

        effect = self._build_effect(spec, visual_params, seed)
        sprites = self._build_sprites(spec, visual_params, seed, title)

        engine = Engine(
            internal_size=self.internal_size,
            output_size=self.output_size,
            gradient_name=spec.gradient_name,
            color_scheme=spec.color_scheme,
            sharpen=spec.sharpen,
            contrast=spec.contrast,
        )

        render_params = {}
        for k, v in spec.bg_params.items():
            render_params[k] = v
            render_params["bg_" + k] = v
        if spec.overlay_params:
            for k, v in spec.overlay_params.items():
                if k not in render_params:
                    render_params[k] = v
                render_params["overlay_" + k] = v
        render_params["warmth"] = visual_params.get("warmth", 0.5)
        render_params["saturation"] = visual_params.get("saturation", 0.9)
        render_params["brightness"] = visual_params.get("brightness", 0.8)

        # Pass postfx chain and mask params to engine
        if spec.postfx_chain:
            render_params["_postfx_chain"] = spec.postfx_chain
        if spec.mask_params:
            render_params.update(spec.mask_params)

        # Pass bg_fill spec to engine
        if spec.bg_fill_spec:
            render_params["_bg_fill_spec"] = spec.bg_fill_spec

        # 渲染每帧 (带参数漂移)
        total_frames = int(duration * fps)
        frames = []

        for i in range(total_frames):
            t = i / fps

            # 每帧施加噪声调制
            if self.drift_amount > 0:
                frame_params = modulate_visual_params(
                    render_params,
                    t=t,
                    drift_amount=self.drift_amount * 0.5,
                    seed=seed,
                )
            else:
                frame_params = render_params

            frame_img = engine.render_frame(
                effect=effect,
                sprites=sprites,
                time=t,
                frame=i,
                seed=seed,
                params=frame_params,
            )
            frames.append(frame_img)

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            Engine.save_gif(frames, output_path, fps=fps)

        self.last_frames = frames
        return frames

    def generate_variants(
        self,
        text: str | None = None,
        emotion: str | None = None,
        emotion_vector: EmotionVector | None = None,
        count: int = 5,
        base_seed: int | None = None,
        content: dict[str, Any] | None = None,
    ) -> list[Image.Image]:
        """
        生成多个不同变体

        每个变体使用不同种子，但基于相同情感输入，
        展示同一情绪的不同视觉诠释。

        参数:
            count: 变体数量
            base_seed: 基础种子 (默认使用管线种子)

        返回:
            Image 列表
        """
        if base_seed is None:
            base_seed = self.seed

        variants = []
        for i in range(count):
            img = self.generate(
                text=text,
                emotion=emotion,
                emotion_vector=emotion_vector,
                seed=base_seed + i,
                content=content,
            )
            variants.append(img)

        return variants

    # === 内部方法 ===

    def _apply_overrides(self, spec: SceneSpec, overrides: dict[str, Any]) -> None:
        """
        用户覆盖应用 - Apply user overrides to SceneSpec

        Supported keys: effect, layout, decoration, gradient, overlay,
        domain_transforms, postfx_chain, composition_mode, mask_type,
        mask_params, variant.
        """
        if overrides.get("effect"):
            spec.bg_effect = overrides["effect"]
        if overrides.get("layout"):
            spec.layout_type = overrides["layout"]
        if overrides.get("decoration"):
            spec.decoration_style = overrides["decoration"]
        if overrides.get("gradient"):
            spec.gradient_name = overrides["gradient"]
        if overrides.get("overlay"):
            ov = overrides["overlay"]
            if isinstance(ov, dict):
                if ov.get("effect"):
                    spec.overlay_effect = ov["effect"]
                if ov.get("blend"):
                    spec.overlay_blend = ov["blend"]
                if ov.get("mix") is not None:
                    mix = max(0.0, min(1.0, float(ov["mix"])))
                    spec.overlay_mix = mix
        if overrides.get("params"):
            spec.bg_params.update(overrides["params"])

        # Domain transforms (replace grammar choice)
        if overrides.get("domain_transforms"):
            spec.domain_transforms = overrides["domain_transforms"]

        # Post-FX chain (replace grammar choice)
        if overrides.get("postfx_chain"):
            spec.postfx_chain = overrides["postfx_chain"]

        # Composition mode
        if overrides.get("composition_mode"):
            spec.composition_mode = overrides["composition_mode"]

        # Mask type and params
        if overrides.get("mask_type"):
            spec.mask_type = overrides["mask_type"]
        if overrides.get("mask_params"):
            spec.mask_params.update(overrides["mask_params"])

        # Variant override
        if overrides.get("variant"):
            from procedural.effects.variants import VARIANT_REGISTRY

            variant_name = overrides["variant"]
            variants = VARIANT_REGISTRY.get(spec.bg_effect, [])
            for v in variants:
                if v["name"] == variant_name:
                    rng = random.Random(self.seed)
                    for key, val in v["params"].items():
                        if isinstance(val, tuple) and len(val) == 2:
                            lo, hi = val
                            if isinstance(lo, int) and isinstance(hi, int):
                                spec.bg_params[key] = rng.randint(lo, hi)
                            else:
                                spec.bg_params[key] = rng.uniform(float(lo), float(hi))
                        else:
                            spec.bg_params[key] = val
                    break

        # Auto-create overlay when composition mode needs one
        if spec.composition_mode != "blend" and spec.overlay_effect is None:
            from procedural.effects import EFFECT_REGISTRY

            overlay_candidates = [e for e in EFFECT_REGISTRY if e != spec.bg_effect]
            if overlay_candidates:
                rng2 = random.Random(self.seed + 999)
                spec.overlay_effect = rng2.choice(overlay_candidates)
                spec.overlay_mix = 0.3

    def _resolve_emotion(
        self,
        text: str | None,
        emotion: str | None,
        emotion_vector: EmotionVector | None,
    ) -> EmotionVector:
        """解析情感输入为 EmotionVector"""
        if emotion_vector is not None:
            return emotion_vector
        if emotion is not None:
            return emotion_from_name(emotion)
        if text is not None:
            return text_to_emotion(text)
        return EmotionVector(0.0, 0.0, 0.0)

    def _build_effect(
        self,
        spec: SceneSpec,
        visual_params: dict[str, Any],
        seed: int,
    ) -> Any:
        """根据 SceneSpec 构建效果 (可能是复合/变换/遮罩效果)"""

        # 构建主效果
        if spec.bg_effect == "cppn":
            cppn_params = spec.bg_params
            bg_effect = CPPNEffect(
                seed=cppn_params.get("seed", seed),
                num_hidden=cppn_params.get("num_hidden", 3),
                layer_size=cppn_params.get("layer_size", 8),
            )
        elif spec.bg_effect in EFFECT_REGISTRY:
            bg_effect = get_effect(spec.bg_effect)
        else:
            bg_effect = get_effect("plasma")

        # 如果有叠加效果，创建复合效果
        if spec.overlay_effect is not None:
            if spec.overlay_effect == "cppn":
                overlay_effect = CPPNEffect(
                    seed=seed + 1000,
                    num_hidden=spec.overlay_params.get("num_hidden", 2),
                    layer_size=spec.overlay_params.get("layer_size", 6),
                )
            elif spec.overlay_effect in EFFECT_REGISTRY:
                overlay_effect = get_effect(spec.overlay_effect)
            else:
                overlay_effect = None

            if overlay_effect is not None:
                # 选择合成方式: 传统混合 or 遮罩合成
                if spec.composition_mode != "blend" and spec.mask_type:
                    # 遮罩合成 - Masked composition
                    mask_cls = MASK_REGISTRY.get(spec.mask_type)
                    if mask_cls:
                        mask_effect = mask_cls()
                        bg_effect = MaskedCompositeEffect(
                            effect_a=bg_effect,
                            effect_b=overlay_effect,
                            mask=mask_effect,
                            threshold=spec.mask_params.get("mask_threshold", 0.5),
                            softness=spec.mask_params.get("mask_softness", 0.2),
                        )
                    else:
                        # Fallback to standard blend
                        blend_map = {
                            "ADD": BlendMode.ADD,
                            "SCREEN": BlendMode.SCREEN,
                            "OVERLAY": BlendMode.OVERLAY,
                            "MULTIPLY": BlendMode.MULTIPLY,
                        }
                        blend_mode = blend_map.get(spec.overlay_blend, BlendMode.ADD)
                        bg_effect = CompositeEffect(
                            effect_a=bg_effect,
                            effect_b=overlay_effect,
                            mode=blend_mode,
                            mix=spec.overlay_mix,
                        )
                else:
                    # 传统混合 - Standard blend
                    blend_map = {
                        "ADD": BlendMode.ADD,
                        "SCREEN": BlendMode.SCREEN,
                        "OVERLAY": BlendMode.OVERLAY,
                        "MULTIPLY": BlendMode.MULTIPLY,
                    }
                    blend_mode = blend_map.get(spec.overlay_blend, BlendMode.ADD)
                    bg_effect = CompositeEffect(
                        effect_a=bg_effect,
                        effect_b=overlay_effect,
                        mode=blend_mode,
                        mix=spec.overlay_mix,
                    )

        # 域变换包装 - Wrap with domain transforms
        if spec.domain_transforms:
            transform_chain = []
            for t in spec.domain_transforms:
                t_type = t.get("type", "")
                t_fn = TRANSFORM_REGISTRY.get(t_type)
                if t_fn:
                    kwargs = {k: v for k, v in t.items() if k != "type"}
                    transform_chain.append((t_fn, kwargs))
            if transform_chain:
                bg_effect = TransformedEffect(
                    inner_effect=bg_effect,
                    transforms=transform_chain,
                )

        return bg_effect

    def _build_sprites(
        self,
        spec: SceneSpec,
        visual_params: dict[str, Any],
        seed: int,
        title: str | None,
    ) -> list[Any]:
        """根据 SceneSpec 构建精灵列表"""
        rng = random.Random(seed)
        sprites = []
        w, h = self.output_size

        # 生成调色板
        palette = self._color_space.generate_palette(
            warmth=spec.warmth,
            saturation=spec.saturation,
            brightness=spec.brightness,
        )

        # === 布局 ===
        positions = self._generate_positions(
            spec.layout_type, spec.layout_count, w, h, rng
        )

        # === 从 grammar 动画配置构建动画模板 ===
        anim_templates = (
            spec.animations
            if spec.animations
            else [
                {"type": "floating", "amp": spec.float_amp, "speed": 1.0},
                {"type": "breathing", "amp": spec.breath_amp, "speed": 2.0},
            ]
        )

        # === 颜文字精灵 ===
        # Override moods from vocabulary if present
        if spec.kaomoji_mood_overrides:
            mood_options: list[str] = spec.kaomoji_mood_overrides
        else:
            mood_options = self._mood_from_valence_arousal(
                float(visual_params.get("valence", 0.0)),
                float(visual_params.get("arousal", 0.0)),
            )
        for i, pos in enumerate(positions[: spec.kaomoji_count]):
            if len(pos) == 3:
                px, py, size = pos
            else:
                px, py = pos
                size = rng.randint(*spec.kaomoji_size_range)

            mood = rng.choice(mood_options)
            phase = i * 0.5  # 错开相位

            # 从文法动画配置构建精灵动画 (注入每个精灵的相位)
            sprite_anims = []
            for tmpl in anim_templates:
                anim = dict(tmpl)
                if anim["type"] == "floating":
                    anim["phase"] = phase
                    anim["speed"] = float(anim.get("speed", 1.0)) + rng.random() * 0.5
                elif anim["type"] == "breathing":
                    anim["speed"] = float(anim.get("speed", 2.0)) + rng.random()
                sprite_anims.append(anim)

            sprite = KaomojiSprite(
                mood=mood,
                x=px,
                y=py,
                color=tuple(palette["primary"]),
                outline_color=tuple(palette["outline"]),
                scale=max(3, size // 25),
                animations=sprite_anims,
            )
            sprites.append(sprite)

        # === 中心颜文字 ===
        if spec.has_central_kaomoji:
            central_mood = rng.choice(mood_options)
            sprite = KaomojiSprite(
                mood=central_mood,
                x=w // 2 - spec.central_size // 2,
                y=h // 2 - spec.central_size // 2,
                color=tuple(palette["accent"]),
                outline_color=tuple(palette["outline"]),
                scale=max(9, spec.central_size // 20),
                animations=[
                    {"type": "breathing", "amp": spec.breath_amp * 1.5, "speed": 1.5},
                ],
            )
            sprites.append(sprite)

        if spec.decoration_style != "none":
            deco_sprites = build_decoration_sprites(
                style=spec.decoration_style,
                spec=spec,
                palette=palette,
                width=w,
                height=h,
                rng=rng,
            )
            sprites.extend(deco_sprites)

        # === 粒子文字 ===
        if spec.particle_chars:
            particle_sprites = self._build_particle_sprites(spec, palette, w, h, rng)
            sprites.extend(particle_sprites)

        # === 氛围文字 ===
        for elem in spec.text_elements:
            ex, ey = elem["position"]
            px = int(ex * w)
            py = int(ey * h)
            opacity = elem.get("opacity", 0.6)
            # 通过降低颜色亮度模拟透明度
            dim_factor = max(0.2, opacity)
            secondary = tuple(palette["secondary"])
            text_color = tuple(int(c * dim_factor) for c in secondary)
            sprites.append(
                TextSprite(
                    text=elem["text"],
                    x=px,
                    y=py,
                    color=text_color,
                    glow_color=tuple(palette.get("glow", text_color)),
                    glow_size=1,
                    animations=[
                        {
                            "type": "floating",
                            "amp": 2.0,
                            "speed": 0.3,
                            "phase": rng.uniform(0, 6.28),
                        },
                    ],
                )
            )

        # === 标题文字 ===
        if title:
            sprites.append(
                TextSprite(
                    text=title,
                    x=w // 2 - len(title) * 4,
                    y=30,
                    color=tuple(palette["primary"]),
                    glow_color=tuple(palette["glow"]),
                    glow_size=2,
                    animations=[
                        {"type": "breathing", "amp": 0.03, "speed": 1.0},
                    ],
                )
            )

        return sprites

    def _build_particle_sprites(
        self,
        spec: SceneSpec,
        palette: dict[str, Any],
        w: int,
        h: int,
        rng: random.Random,
    ) -> list[Any]:
        """生成粒子字符精灵"""
        particles: list[Any] = []
        chars = spec.particle_chars
        color = tuple(palette.get("dim", (60, 60, 60)))
        count = rng.randint(10, 25)

        for _ in range(count):
            ch = rng.choice(chars)
            x = rng.randint(20, w - 20)
            y = rng.randint(20, h - 20)
            particles.append(
                TextSprite(
                    text=ch,
                    x=x,
                    y=y,
                    color=color,
                    scale=1.0,
                    animations=[
                        {
                            "type": "floating",
                            "amp": rng.uniform(2, 6),
                            "speed": rng.uniform(0.2, 0.8),
                            "phase": rng.uniform(0, 6.28),
                        }
                    ],
                )
            )

        return particles

    def _generate_positions(
        self,
        layout_type: str,
        count: int,
        width: int,
        height: int,
        rng: random.Random,
    ) -> list[Any]:
        """根据布局类型生成位置"""
        if layout_type == "random_scatter":
            return random_scatter(width, height, count, rng)
        elif layout_type == "grid_jitter":
            return grid_with_jitter(width, height, count, rng, jitter=30)
        elif layout_type == "spiral":
            return spiral_layout(width, height, count, rng)
        elif layout_type == "force_directed":
            return force_directed_layout(width, height, count, rng, iterations=30)
        elif layout_type == "preset":
            preset = rng.choice(LAYOUT_PRESETS)
            return list(cast(list[tuple[int, int, int]], preset["positions"]))[:count]
        else:
            return random_scatter(width, height, count, rng)

    def _mood_from_valence_arousal(
        self, valence: float, arousal: float = 0.0
    ) -> list[str]:
        """
        从效价+唤醒推导颜文字情绪列表

        使用 valence 确定正/负方向，arousal 确定能量级别，
        避免 panic(高唤醒)和 sadness(低唤醒) 使用相同颜文字。
        """
        high_arousal = arousal > 0.3
        low_arousal = arousal < -0.3

        if valence > 0.7:
            if high_arousal:
                return ["euphoria", "excitement", "proud"]
            else:
                return ["love", "relaxed", "happy", "proud"]
        elif valence > 0.3:
            if high_arousal:
                return ["excitement", "happy", "euphoria"]
            else:
                return ["relaxed", "love", "happy"]
        elif valence > 0.0:
            if high_arousal:
                return ["surprised", "excited", "happy"]
            elif low_arousal:
                return ["sleepy", "relaxed", "bored"]
            else:
                return ["neutral", "thinking", "relaxed"]
        elif valence > -0.3:
            if high_arousal:
                return ["confused", "surprised", "anxiety"]
            elif low_arousal:
                return ["bored", "sleepy", "disappointed"]
            else:
                return ["confused", "thinking", "disappointed"]
        elif valence > -0.6:
            if high_arousal:
                return ["anxiety", "fear", "angry"]
            else:
                return ["sad", "lonely", "disappointed"]
        else:
            if high_arousal:
                return ["panic", "fear", "angry"]
            else:
                return ["sad", "lonely", "disappointed", "fear"]
