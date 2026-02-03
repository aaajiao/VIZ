"""test procedural/effects/ - all effects basic operation"""

import pytest
from procedural.engine import Engine
from procedural.effects import get_effect, EFFECT_REGISTRY
from PIL import Image


class TestEffectRegistry:
    def test_registry_not_empty(self):
        assert len(EFFECT_REGISTRY) > 0

    def test_plasma_registered(self):
        assert "plasma" in EFFECT_REGISTRY

    def test_flame_registered(self):
        assert "flame" in EFFECT_REGISTRY

    def test_wave_registered(self):
        assert "wave" in EFFECT_REGISTRY

    def test_moire_registered(self):
        assert "moire" in EFFECT_REGISTRY

    def test_noise_field_registered(self):
        assert "noise_field" in EFFECT_REGISTRY

    def test_sdf_shapes_registered(self):
        assert "sdf_shapes" in EFFECT_REGISTRY


class TestGetEffect:
    def test_returns_effect_instance(self):
        effect = get_effect("plasma")
        assert hasattr(effect, "pre")
        assert hasattr(effect, "main")
        assert hasattr(effect, "post")

    def test_unknown_effect_raises(self):
        with pytest.raises(KeyError):
            get_effect("nonexistent_effect")


class TestEffectsRender:
    """Test each effect can render without crashing"""

    @pytest.fixture
    def engine(self):
        return Engine(internal_size=(32, 32), output_size=(64, 64))

    def test_plasma_renders(self, engine):
        effect = get_effect("plasma")
        img = engine.render_frame(effect, time=0.5, seed=42)
        assert isinstance(img, Image.Image)
        assert img.size == (64, 64)

    def test_flame_renders(self, engine):
        effect = get_effect("flame")
        img = engine.render_frame(effect, time=0.5, seed=42)
        assert isinstance(img, Image.Image)

    def test_wave_renders(self, engine):
        effect = get_effect("wave")
        img = engine.render_frame(effect, time=0.5, seed=42)
        assert isinstance(img, Image.Image)

    def test_moire_renders(self, engine):
        effect = get_effect("moire")
        img = engine.render_frame(effect, time=0.5, seed=42)
        assert isinstance(img, Image.Image)

    def test_noise_field_renders(self, engine):
        effect = get_effect("noise_field")
        img = engine.render_frame(effect, time=0.5, seed=42)
        assert isinstance(img, Image.Image)

    def test_sdf_shapes_renders(self, engine):
        effect = get_effect("sdf_shapes")
        img = engine.render_frame(effect, time=0.5, seed=42)
        assert isinstance(img, Image.Image)

    def test_all_effects_render(self, engine):
        for name in EFFECT_REGISTRY:
            effect = get_effect(name)
            img = engine.render_frame(effect, time=0.5, seed=42)
            assert isinstance(img, Image.Image), f"{name} failed to render"


class TestEffectsProtocol:
    """Test effects implement required protocol"""

    def test_pre_returns_dict_or_none(self):
        for name in EFFECT_REGISTRY:
            effect = get_effect(name)
            from procedural.types import Context
            import random

            ctx = Context(
                width=32,
                height=32,
                time=0.0,
                frame=0,
                seed=42,
                rng=random.Random(42),
                params={},
            )
            buffer = [[None for _ in range(32)] for _ in range(32)]
            state = effect.pre(ctx, buffer)
            assert state is None or isinstance(state, dict)

    def test_main_returns_cell_or_none(self):
        for name in EFFECT_REGISTRY:
            effect = get_effect(name)
            from procedural.types import Context, Cell
            import random

            ctx = Context(
                width=32,
                height=32,
                time=0.0,
                frame=0,
                seed=42,
                rng=random.Random(42),
                params={},
            )
            buffer = [[None for _ in range(32)] for _ in range(32)]
            state = effect.pre(ctx, buffer) or {}
            cell = effect.main(16, 16, ctx, state)
            assert cell is None or isinstance(cell, Cell)


class TestEffectsAnimation:
    """Test effects produce different frames over time"""

    @pytest.fixture
    def engine(self):
        return Engine(internal_size=(32, 32), output_size=(64, 64))

    def test_plasma_animates(self, engine):
        effect = get_effect("plasma")
        img1 = engine.render_frame(effect, time=0.0, seed=42)
        img2 = engine.render_frame(effect, time=1.0, seed=42)
        assert list(img1.getdata()) != list(img2.getdata())

    def test_wave_animates(self, engine):
        effect = get_effect("wave")
        img1 = engine.render_frame(effect, time=0.0, seed=42)
        img2 = engine.render_frame(effect, time=1.0, seed=42)
        assert list(img1.getdata()) != list(img2.getdata())
