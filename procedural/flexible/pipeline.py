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
from datetime import datetime

from PIL import Image

from procedural.engine import Engine
from procedural.effects import EFFECT_REGISTRY, get_effect
from procedural.compositor import CompositeEffect, BlendMode
from procedural.layouts import (
    random_scatter, grid_with_jitter, spiral_layout,
    force_directed_layout, LAYOUT_PRESETS,
)
from procedural.layers import TextSprite, KaomojiSprite

from .emotion import (
    EmotionVector, text_to_emotion, emotion_from_name, VAD_ANCHORS,
)
from .color_space import ContinuousColorSpace
from .modulator import modulate_visual_params
from .grammar import VisualGrammar, SceneSpec
from .cppn import CPPNEffect


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

    def generate(
        self,
        text: str | None = None,
        emotion: str | None = None,
        emotion_vector: EmotionVector | None = None,
        seed: int | None = None,
        title: str | None = None,
        output_path: str | None = None,
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
                visual_params, t=0.0,
                drift_amount=self.drift_amount, seed=seed,
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
        )

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
            sharpen=spec.sharpen,
            contrast=spec.contrast,
        )

        # 合并效果参数和色温参数
        render_params = {**spec.bg_params}
        render_params["warmth"] = visual_params.get("warmth", 0.5)
        render_params["saturation"] = visual_params.get("saturation", 0.9)

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
            print(f"已保存: {output_path}")

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
        )

        effect = self._build_effect(spec, visual_params, seed)
        sprites = self._build_sprites(spec, visual_params, seed, title)

        engine = Engine(
            internal_size=self.internal_size,
            output_size=self.output_size,
            gradient_name=spec.gradient_name,
            sharpen=spec.sharpen,
            contrast=spec.contrast,
        )

        render_params = {**spec.bg_params}
        render_params["warmth"] = visual_params.get("warmth", 0.5)
        render_params["saturation"] = visual_params.get("saturation", 0.9)

        # 渲染每帧 (带参数漂移)
        total_frames = int(duration * fps)
        frames = []

        for i in range(total_frames):
            t = i / fps

            # 每帧施加噪声调制
            if self.drift_amount > 0:
                frame_params = modulate_visual_params(
                    render_params, t=t,
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

        return frames

    def generate_variants(
        self,
        text: str | None = None,
        emotion: str | None = None,
        emotion_vector: EmotionVector | None = None,
        count: int = 5,
        base_seed: int | None = None,
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
            )
            variants.append(img)

        return variants

    # === 内部方法 ===

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
        visual_params: dict,
        seed: int,
    ):
        """根据 SceneSpec 构建效果 (可能是复合效果)"""

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

        return bg_effect

    def _build_sprites(
        self,
        spec: SceneSpec,
        visual_params: dict,
        seed: int,
        title: str | None,
    ) -> list:
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

        # === 颜文字精灵 ===
        mood_options = self._mood_from_valence(visual_params.get("valence", 0.0))
        for i, pos in enumerate(positions[:spec.kaomoji_count]):
            if len(pos) == 3:
                px, py, size = pos
            else:
                px, py = pos
                size = rng.randint(*spec.kaomoji_size_range)

            mood = rng.choice(mood_options)
            phase = i * 0.5  # 错开相位

            sprite = KaomojiSprite(
                mood=mood,
                x=px, y=py,
                color=palette["primary"],
                outline_color=palette["outline"],
                scale=max(1, size // 100),
                animations=[
                    {
                        "type": "floating",
                        "amp": spec.float_amp,
                        "speed": 0.5 + rng.random() * 1.5,
                        "phase": phase,
                    },
                    {
                        "type": "breathing",
                        "amp": spec.breath_amp,
                        "speed": 1.0 + rng.random() * 2.0,
                    },
                ],
            )
            sprites.append(sprite)

        # === 中心颜文字 ===
        if spec.has_central_kaomoji:
            central_mood = rng.choice(mood_options)
            sprite = KaomojiSprite(
                mood=central_mood,
                x=w // 2 - spec.central_size // 2,
                y=h // 2 - spec.central_size // 2,
                color=palette["accent"],
                outline_color=palette["outline"],
                scale=max(1, spec.central_size // 80),
                animations=[
                    {"type": "breathing", "amp": spec.breath_amp * 1.5, "speed": 1.5},
                ],
            )
            sprites.append(sprite)

        # === 标题文字 ===
        if title:
            sprites.append(TextSprite(
                text=title,
                x=w // 2 - len(title) * 4,
                y=30,
                color=palette["primary"],
                glow_color=palette["glow"],
                glow_size=2,
                animations=[
                    {"type": "breathing", "amp": 0.03, "speed": 1.0},
                ],
            ))

        return sprites

    def _generate_positions(
        self,
        layout_type: str,
        count: int,
        width: int,
        height: int,
        rng: random.Random,
    ) -> list:
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
            return preset["positions"][:count]
        else:
            return random_scatter(width, height, count, rng)

    def _mood_from_valence(self, valence: float) -> list[str]:
        """
        从效价值推导颜文字情绪列表

        不再是 bull/bear/neutral 三选一，而是根据连续效价
        混合多种情绪面孔。
        """
        if valence > 0.5:
            return ["bull", "happy", "excited", "euphoria", "love"]
        elif valence > 0.1:
            return ["bull", "happy", "calm", "excited"]
        elif valence > -0.1:
            return ["neutral", "calm", "thinking", "o_o"]
        elif valence > -0.5:
            return ["bear", "sad", "anxious", "thinking"]
        else:
            return ["bear", "sad", "panic", "fear", "cry"]
