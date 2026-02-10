"""test animation enhancements - transforms, postfx, masks time-awareness"""

import math
import random
import pytest

from procedural.transforms import _resolve_animated_kwargs, TransformedEffect, rotate_uv, zoom
from procedural.postfx import (
    postfx_scanlines,
    postfx_vignette,
    postfx_color_shift,
    postfx_pixelate,
    postfx_threshold,
    postfx_invert,
    postfx_edge_detect,
)
from procedural.masks import (
    HorizontalSplitMask,
    VerticalSplitMask,
    DiagonalMask,
    RadialMask,
    NoiseMask,
    SDFMask,
)
from procedural.types import Context, Cell
from procedural.core.mathx import TAU


# ==================== Helpers ====================


def make_ctx(w=32, h=32, time=0.0, params=None):
    return Context(
        width=w,
        height=h,
        time=time,
        frame=int(time * 15),
        seed=42,
        rng=random.Random(42),
        params=params or {},
    )


def make_buffer(w, h, char_idx=5, fg=(128, 128, 128)):
    return [[Cell(char_idx=char_idx, fg=fg, bg=None) for _ in range(w)] for _ in range(h)]


class StubEffect:
    def pre(self, ctx, buffer):
        return {}

    def main(self, x, y, ctx, state):
        value = (x + y) / max(ctx.width + ctx.height, 1)
        idx = min(9, int(value * 9))
        return Cell(char_idx=idx, fg=(x % 256, y % 256, 0), bg=None)

    def post(self, ctx, buffer, state):
        pass


# ==================== _resolve_animated_kwargs tests ====================


class TestResolveAnimatedKwargs:
    def test_static_values_pass_through(self):
        kwargs = {"angle": 1.5, "segments": 6}
        result = _resolve_animated_kwargs(kwargs, time=2.0)
        assert result["angle"] == 1.5
        assert result["segments"] == 6

    def test_empty_kwargs(self):
        assert _resolve_animated_kwargs({}, 1.0) == {}

    def test_none_kwargs(self):
        assert _resolve_animated_kwargs(None, 1.0) is None

    def test_linear_mode(self):
        kwargs = {"angle": {"base": 0.0, "speed": 1.0, "mode": "linear"}}
        result = _resolve_animated_kwargs(kwargs, time=2.0)
        assert abs(result["angle"] - 2.0) < 1e-9

    def test_linear_mode_with_base(self):
        kwargs = {"angle": {"base": 0.5, "speed": 1.0, "mode": "linear"}}
        result = _resolve_animated_kwargs(kwargs, time=3.0)
        assert abs(result["angle"] - 3.5) < 1e-9

    def test_oscillate_mode_at_zero(self):
        kwargs = {"factor": {"base": 2.0, "speed": 1.0, "amp": 0.5, "mode": "oscillate"}}
        result = _resolve_animated_kwargs(kwargs, time=0.0)
        assert abs(result["factor"] - 2.0) < 1e-9

    def test_oscillate_mode_at_quarter(self):
        """At time=0.25 with speed=1.0, sin(0.25 * 2π) = 1.0"""
        kwargs = {"factor": {"base": 2.0, "speed": 1.0, "amp": 0.5, "mode": "oscillate"}}
        result = _resolve_animated_kwargs(kwargs, time=0.25)
        assert abs(result["factor"] - 2.5) < 1e-6

    def test_oscillate_default_mode(self):
        """oscillate is the default mode"""
        kwargs = {"val": {"base": 1.0, "speed": 1.0, "amp": 0.3}}
        result = _resolve_animated_kwargs(kwargs, time=0.25)
        expected = 1.0 + 0.3 * math.sin(0.25 * TAU)
        assert abs(result["val"] - expected) < 1e-6

    def test_ping_pong_mode_rising(self):
        kwargs = {"val": {"base": 0.0, "speed": 1.0, "amp": 1.0, "mode": "ping_pong"}}
        result = _resolve_animated_kwargs(kwargs, time=0.5)
        assert abs(result["val"] - 0.5) < 1e-9

    def test_ping_pong_mode_peak(self):
        kwargs = {"val": {"base": 0.0, "speed": 1.0, "amp": 1.0, "mode": "ping_pong"}}
        result = _resolve_animated_kwargs(kwargs, time=1.0)
        assert abs(result["val"] - 1.0) < 1e-9

    def test_ping_pong_mode_falling(self):
        kwargs = {"val": {"base": 0.0, "speed": 1.0, "amp": 1.0, "mode": "ping_pong"}}
        result = _resolve_animated_kwargs(kwargs, time=1.5)
        assert abs(result["val"] - 0.5) < 1e-9

    def test_mixed_static_and_animated(self):
        kwargs = {
            "segments": 6,
            "angle": {"base": 0.0, "speed": 1.0, "mode": "linear"},
        }
        result = _resolve_animated_kwargs(kwargs, time=1.0)
        assert result["segments"] == 6
        assert abs(result["angle"] - 1.0) < 1e-9

    def test_dict_without_base_passes_through(self):
        """A dict that doesn't have 'base' and 'speed' should pass through"""
        kwargs = {"config": {"some_key": "some_value"}}
        result = _resolve_animated_kwargs(kwargs, time=1.0)
        assert result["config"] == {"some_key": "some_value"}


# ==================== TransformedEffect animation tests ====================


class TestTransformedEffectAnimation:
    def test_animated_rotation_changes_with_time(self):
        """Animated rotation should produce different results at different times"""
        stub = StubEffect()
        anim_kwargs = {"angle": {"base": 0.0, "speed": 0.5, "mode": "linear"}}
        transformed = TransformedEffect(stub, [(rotate_uv, anim_kwargs)])

        ctx0 = make_ctx(time=0.0)
        ctx1 = make_ctx(time=1.0)
        state = transformed.pre(ctx0, [])

        cell_t0 = transformed.main(10, 10, ctx0, state)
        cell_t1 = transformed.main(10, 10, ctx1, state)
        # Different times should yield different cells
        assert cell_t0.fg != cell_t1.fg or cell_t0.char_idx != cell_t1.char_idx

    def test_static_kwargs_still_work(self):
        """Non-animated kwargs should work as before"""
        stub = StubEffect()
        ctx = make_ctx(time=0.0)
        transformed = TransformedEffect(stub, [(rotate_uv, {"angle": 0.0})])
        state = transformed.pre(ctx, [])
        cell = transformed.main(10, 10, ctx, state)
        assert isinstance(cell, Cell)


# ==================== PostFX animation tests ====================


class TestPostfxAnimation:
    def test_scanlines_scroll(self):
        """Scanlines with scroll_speed should produce different patterns at different times"""
        buf0 = make_buffer(8, 16, char_idx=9, fg=(200, 200, 200))
        buf1 = make_buffer(8, 16, char_idx=9, fg=(200, 200, 200))
        postfx_scanlines(buf0, spacing=4, darkness=0.5, scroll_speed=2.0, _time=0.0)
        postfx_scanlines(buf1, spacing=4, darkness=0.5, scroll_speed=2.0, _time=0.3)
        # At least one row should differ due to scroll offset
        diffs = sum(
            1 for y in range(16) if buf0[y][0].fg != buf1[y][0].fg
        )
        assert diffs > 0

    def test_scanlines_no_time_backward_compat(self):
        """Scanlines without _time should work as before"""
        buf = make_buffer(4, 8, char_idx=9, fg=(200, 200, 200))
        postfx_scanlines(buf, spacing=4, darkness=0.5)
        assert buf[0][0].fg[0] < 200  # Row 0 darkened
        assert buf[1][0].fg == (200, 200, 200)  # Row 1 unchanged

    def test_vignette_pulse(self):
        """Vignette with pulse should vary strength over time"""
        buf0 = make_buffer(16, 16, char_idx=9, fg=(200, 200, 200))
        buf1 = make_buffer(16, 16, char_idx=9, fg=(200, 200, 200))
        postfx_vignette(buf0, strength=0.5, pulse_speed=1.0, pulse_amp=0.3, _time=0.0)
        postfx_vignette(buf1, strength=0.5, pulse_speed=1.0, pulse_amp=0.3, _time=0.25)
        # Corner values should differ
        assert buf0[0][0].fg != buf1[0][0].fg

    def test_vignette_no_time_backward_compat(self):
        buf = make_buffer(16, 16, char_idx=9, fg=(200, 200, 200))
        postfx_vignette(buf, strength=0.5)
        assert buf[8][8].fg[0] > buf[0][0].fg[0]

    def test_color_shift_drift(self):
        """Color shift with drift should change hue over time"""
        buf0 = make_buffer(4, 4, fg=(200, 50, 50))
        buf1 = make_buffer(4, 4, fg=(200, 50, 50))
        postfx_color_shift(buf0, hue_shift=0.1, drift_speed=0.5, _time=0.0)
        postfx_color_shift(buf1, hue_shift=0.1, drift_speed=0.5, _time=0.5)
        # hue_shift at t=0: 0.1, at t=0.5: 0.1+0.25=0.35 → different colors
        assert buf0[0][0].fg != buf1[0][0].fg

    def test_color_shift_no_time_backward_compat(self):
        buf = make_buffer(4, 4, fg=(200, 50, 50))
        postfx_color_shift(buf, hue_shift=0.33)
        assert buf[0][0].fg != (200, 50, 50)

    def test_pixelate_pulse(self):
        """Pixelate with pulse should use different block sizes at different times"""
        # Use a gradient buffer so different block sizes produce different averaging
        from procedural.types import Cell
        buf0 = [[Cell(char_idx=min(9, x), fg=(x * 16 % 256, y * 16 % 256, 128), bg=None)
                 for x in range(16)] for y in range(16)]
        buf1 = [[Cell(char_idx=min(9, x), fg=(x * 16 % 256, y * 16 % 256, 128), bg=None)
                 for x in range(16)] for y in range(16)]
        postfx_pixelate(buf0, block_size=4, pulse_speed=1.0, pulse_amp=2.0, _time=0.0)
        postfx_pixelate(buf1, block_size=4, pulse_speed=1.0, pulse_amp=2.0, _time=0.25)
        # At time=0: block_size=4, at time=0.25: block_size=6 → different averaging
        diffs = sum(
            1 for y in range(16) for x in range(16)
            if buf0[y][x].fg != buf1[y][x].fg
        )
        assert diffs > 0

    def test_static_postfx_accept_unknown_kwargs(self):
        """threshold, invert, edge_detect should accept **_kw without error"""
        buf = make_buffer(8, 8, char_idx=5, fg=(100, 100, 100))
        postfx_threshold(buf, threshold=0.5, _time=1.0, _extra="ignored")
        postfx_invert(make_buffer(4, 4), _time=1.0)
        postfx_edge_detect(make_buffer(8, 8), _time=1.0)


# ==================== Mask animation tests ====================


class TestMaskAnimation:
    def test_horizontal_split_static_at_zero(self):
        """mask_anim_speed=0 should produce same result as original"""
        ctx = make_ctx(time=1.0, params={"mask_split": 0.5, "mask_anim_speed": 0.0})
        mask = HorizontalSplitMask()
        state = mask.pre(ctx, [])
        assert abs(state["split"] - 0.5) < 1e-9

    def test_horizontal_split_animates(self):
        """mask_anim_speed > 0 should shift the split position over time"""
        ctx0 = make_ctx(time=0.0, params={"mask_split": 0.5, "mask_anim_speed": 1.0})
        ctx1 = make_ctx(time=0.25, params={"mask_split": 0.5, "mask_anim_speed": 1.0})
        mask = HorizontalSplitMask()
        state0 = mask.pre(ctx0, [])
        state1 = mask.pre(ctx1, [])
        # At time=0, split unchanged (sin(0)=0)
        assert abs(state0["split"] - 0.5) < 1e-9
        # At time=0.25, split should have shifted
        assert abs(state1["split"] - 0.5) > 0.01

    def test_vertical_split_animates(self):
        ctx = make_ctx(time=0.25, params={"mask_split": 0.5, "mask_anim_speed": 1.0})
        mask = VerticalSplitMask()
        state = mask.pre(ctx, [])
        # sin(0.25 * 1.0 * 2π) = sin(π/2) = 1.0 → split shifts by 0.15
        assert abs(state["split"] - 0.5) > 0.01

    def test_diagonal_animates(self):
        """Diagonal mask angle should change with time"""
        ctx0 = make_ctx(time=0.0, params={"mask_angle": 0.0, "mask_anim_speed": 1.0})
        ctx1 = make_ctx(time=1.0, params={"mask_angle": 0.0, "mask_anim_speed": 1.0})
        mask = DiagonalMask()
        state0 = mask.pre(ctx0, [])
        state1 = mask.pre(ctx1, [])
        assert abs(state0["angle"]) < 1e-9
        assert abs(state1["angle"]) > 0.1

    def test_radial_animates(self):
        """Radial mask radius should pulse with time"""
        ctx = make_ctx(time=0.25, params={"mask_radius": 0.5, "mask_anim_speed": 1.0})
        mask = RadialMask()
        state = mask.pre(ctx, [])
        assert abs(state["radius"] - 0.5) > 0.01

    def test_noise_animates(self):
        """Noise mask with anim_speed should produce different patterns at different times"""
        ctx0 = make_ctx(time=0.0, params={"mask_anim_speed": 1.0})
        ctx1 = make_ctx(time=1.0, params={"mask_anim_speed": 1.0})
        mask = NoiseMask()
        state0 = mask.pre(ctx0, [])
        state1 = mask.pre(ctx1, [])
        # time_offset should differ
        assert abs(state0["time_offset"]) < 1e-9
        assert abs(state1["time_offset"]) > 0.1

    def test_sdf_animates(self):
        """SDF mask size should pulse with time"""
        ctx = make_ctx(time=0.25, params={"mask_sdf_size": 0.3, "mask_anim_speed": 1.0})
        mask = SDFMask()
        state = mask.pre(ctx, [])
        assert abs(state["size"] - 0.3) > 0.01

    def test_sdf_static_at_zero_speed(self):
        """mask_anim_speed=0 should not change size"""
        ctx = make_ctx(time=1.0, params={"mask_sdf_size": 0.3, "mask_anim_speed": 0.0})
        mask = SDFMask()
        state = mask.pre(ctx, [])
        assert abs(state["size"] - 0.3) < 1e-9

    def test_mask_split_clamped(self):
        """Animated split should stay within [0.1, 0.9]"""
        # Use extreme parameters to push split to edges
        ctx = make_ctx(time=0.25, params={"mask_split": 0.9, "mask_anim_speed": 2.0})
        mask = HorizontalSplitMask()
        state = mask.pre(ctx, [])
        assert 0.1 <= state["split"] <= 0.9
