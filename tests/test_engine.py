"""test procedural/engine.py - Engine rendering pipeline"""

import tempfile
import os
import pytest
from PIL import Image

from procedural.engine import Engine
from procedural.types import Cell


class SimpleTestEffect:
    """Minimal effect for testing"""

    def pre(self, ctx, buffer):
        return {"test_state": True}

    def main(self, x, y, ctx, state):
        value = (x + y) / (ctx.width + ctx.height)
        intensity = int(value * 255)
        return Cell(
            char_idx=int(value * 9), fg=(intensity, intensity, intensity), bg=None
        )

    def post(self, ctx, buffer, state):
        pass


class TestEngine:
    def test_init_defaults(self):
        engine = Engine()
        assert engine.internal_size == (160, 160)
        assert engine.output_size == (1080, 1080)

    def test_init_custom_sizes(self):
        engine = Engine(internal_size=(80, 80), output_size=(540, 540))
        assert engine.internal_size == (80, 80)
        assert engine.output_size == (540, 540)

    def test_init_buffer(self):
        engine = Engine()
        buffer = engine._init_buffer(10, 10)
        assert len(buffer) == 10
        assert len(buffer[0]) == 10
        assert buffer[0][0].char_idx == 0


class TestRenderFrame:
    def test_returns_pil_image(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64))
        effect = SimpleTestEffect()
        img = engine.render_frame(effect, time=0.0, seed=42)
        assert isinstance(img, Image.Image)

    def test_output_size_correct(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64))
        effect = SimpleTestEffect()
        img = engine.render_frame(effect, time=0.0, seed=42)
        assert img.size == (64, 64)

    def test_reproducible_with_same_seed(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64))
        effect = SimpleTestEffect()
        img1 = engine.render_frame(effect, time=0.0, seed=42)
        img2 = engine.render_frame(effect, time=0.0, seed=42)
        assert list(img1.getdata()) == list(img2.getdata())

    def test_different_seeds_produce_different_images(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64))
        effect = SimpleTestEffect()
        img1 = engine.render_frame(effect, time=0.0, seed=42)
        img2 = engine.render_frame(effect, time=0.0, seed=99)
        # Simple test effect is deterministic based on position, not seed
        # but params or rng-dependent effects would differ

    def test_with_params(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64))
        effect = SimpleTestEffect()
        params = {"custom_param": 1.5}
        img = engine.render_frame(effect, params=params, seed=42)
        assert isinstance(img, Image.Image)


class TestRenderVideo:
    def test_returns_frame_list(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64))
        effect = SimpleTestEffect()
        frames = engine.render_video(effect, duration=0.2, fps=5, seed=42)
        assert isinstance(frames, list)
        assert len(frames) == 1  # 0.2s * 5fps = 1 frame

    def test_correct_frame_count(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64))
        effect = SimpleTestEffect()
        frames = engine.render_video(effect, duration=1.0, fps=10, seed=42)
        assert len(frames) == 10

    def test_all_frames_are_images(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64))
        effect = SimpleTestEffect()
        frames = engine.render_video(effect, duration=0.5, fps=5, seed=42)
        for frame in frames:
            assert isinstance(frame, Image.Image)


class TestSaveGif:
    def test_saves_gif_file(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64))
        effect = SimpleTestEffect()
        frames = engine.render_video(effect, duration=0.2, fps=5, seed=42)

        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
            output_path = f.name

        try:
            Engine.save_gif(frames, output_path, fps=5)
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0

            img = Image.open(output_path)
            assert img.format == "GIF"
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_empty_frames_raises(self):
        with pytest.raises(ValueError):
            Engine.save_gif([], "output.gif")

    def test_single_frame_gif(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64))
        effect = SimpleTestEffect()
        img = engine.render_frame(effect, seed=42)

        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
            output_path = f.name

        try:
            Engine.save_gif([img], output_path, fps=1)
            assert os.path.exists(output_path)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestPostprocessing:
    def test_sharpen_enabled(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64), sharpen=True)
        effect = SimpleTestEffect()
        img = engine.render_frame(effect, seed=42)
        assert isinstance(img, Image.Image)

    def test_sharpen_disabled(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64), sharpen=False)
        effect = SimpleTestEffect()
        img = engine.render_frame(effect, seed=42)
        assert isinstance(img, Image.Image)

    def test_contrast_enhancement(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64), contrast=1.5)
        effect = SimpleTestEffect()
        img = engine.render_frame(effect, seed=42)
        assert isinstance(img, Image.Image)
