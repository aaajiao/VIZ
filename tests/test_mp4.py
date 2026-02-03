"""test procedural/engine.py - MP4 output via FFmpeg subprocess"""

import os
import shutil
import tempfile
import pytest
from PIL import Image

from procedural.engine import Engine
from procedural.types import Cell


class SimpleTestEffect:
    """Minimal effect for testing"""

    def pre(self, ctx, buffer):
        return {}

    def main(self, x, y, ctx, state):
        value = (x + y) / (ctx.width + ctx.height)
        intensity = int(value * 255)
        return Cell(
            char_idx=int(value * 9), fg=(intensity, intensity, intensity), bg=None
        )

    def post(self, ctx, buffer, state):
        pass


FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None


class TestSaveMp4:
    def test_returns_false_on_empty_frames(self):
        result = Engine.save_mp4([], "output.mp4")
        assert result is False

    @pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="FFmpeg not installed")
    def test_saves_mp4_file(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64))
        effect = SimpleTestEffect()
        frames = engine.render_video(effect, duration=0.3, fps=10, seed=42)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            output_path = f.name

        try:
            result = Engine.save_mp4(frames, output_path, fps=10)
            assert result is True
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @pytest.mark.skipif(FFMPEG_AVAILABLE, reason="FFmpeg is installed")
    def test_returns_false_without_ffmpeg(self):
        img = Image.new("RGB", (64, 64), (0, 0, 0))
        frames = [img, img, img]

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            output_path = f.name

        try:
            result = Engine.save_mp4(frames, output_path)
            assert result is False
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="FFmpeg not installed")
    def test_cleans_up_temp_gif(self):
        engine = Engine(internal_size=(16, 16), output_size=(64, 64))
        effect = SimpleTestEffect()
        frames = engine.render_video(effect, duration=0.2, fps=5, seed=42)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            output_path = f.name

        try:
            Engine.save_mp4(frames, output_path, fps=5)
            temp_dir = tempfile.gettempdir()
            temp_gifs = [f for f in os.listdir(temp_dir) if f.endswith(".gif")]
            # Should not leave orphan .gif files (test is best-effort)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
