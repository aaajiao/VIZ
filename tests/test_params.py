"""test procedural/params.py - ParamSpec, resolve_params, create_rng"""

import random
import pytest
from procedural.params import (
    ParamSpec,
    resolve_params,
    create_rng,
    generate_random_params,
)


class TestParamSpec:
    def test_valid_uniform_spec(self):
        spec = ParamSpec("speed", 0.5, 2.0, "uniform")
        assert spec.name == "speed"
        assert spec.min_val == 0.5
        assert spec.max_val == 2.0

    def test_valid_log_spec(self):
        spec = ParamSpec("scale", 0.01, 1.0, "log")
        assert spec.distribution == "log"

    def test_valid_normal_spec(self):
        spec = ParamSpec("intensity", 0.0, 1.0, "normal")
        assert spec.distribution == "normal"

    def test_invalid_range(self):
        with pytest.raises(ValueError):
            ParamSpec("bad", 10, 5, "uniform")

    def test_invalid_distribution(self):
        with pytest.raises(ValueError):
            ParamSpec("bad", 0, 1, "invalid_dist")

    def test_log_requires_positive_min(self):
        with pytest.raises(ValueError):
            ParamSpec("bad", 0.0, 1.0, "log")

        with pytest.raises(ValueError):
            ParamSpec("bad", -1.0, 1.0, "log")


class TestResolveParams:
    def test_produces_dict(self):
        specs = [ParamSpec("speed", 0.5, 2.0)]
        params = resolve_params(specs, seed=42)
        assert isinstance(params, dict)
        assert "speed" in params

    def test_reproducibility(self):
        specs = [ParamSpec("speed", 0.5, 2.0)]
        params1 = resolve_params(specs, seed=42)
        params2 = resolve_params(specs, seed=42)
        assert params1 == params2

    def test_different_seeds(self):
        specs = [ParamSpec("speed", 0.5, 2.0)]
        params1 = resolve_params(specs, seed=42)
        params2 = resolve_params(specs, seed=99)
        assert params1 != params2

    def test_uniform_in_range(self):
        specs = [ParamSpec("val", 10.0, 20.0, "uniform")]
        for seed in range(100):
            params = resolve_params(specs, seed=seed)
            assert 10.0 <= params["val"] <= 20.0

    def test_log_in_range(self):
        specs = [ParamSpec("val", 0.01, 1.0, "log")]
        for seed in range(100):
            params = resolve_params(specs, seed=seed)
            assert 0.01 <= params["val"] <= 1.0

    def test_normal_in_range(self):
        specs = [ParamSpec("val", 0.0, 1.0, "normal")]
        for seed in range(100):
            params = resolve_params(specs, seed=seed)
            assert 0.0 <= params["val"] <= 1.0

    def test_multiple_specs(self):
        specs = [
            ParamSpec("a", 0.0, 1.0),
            ParamSpec("b", 10.0, 20.0),
            ParamSpec("c", 0.01, 0.1, "log"),
        ]
        params = resolve_params(specs, seed=42)
        assert len(params) == 3
        assert "a" in params and "b" in params and "c" in params


class TestCreateRng:
    def test_returns_random_instance(self):
        rng = create_rng(42)
        assert isinstance(rng, random.Random)

    def test_reproducibility(self):
        rng1 = create_rng(42)
        rng2 = create_rng(42)
        assert rng1.random() == rng2.random()

    def test_different_seeds(self):
        rng1 = create_rng(42)
        rng2 = create_rng(99)
        assert rng1.random() != rng2.random()


class TestGenerateRandomParams:
    def test_plasma_params(self):
        rng = random.Random(42)
        params = generate_random_params("plasma", rng)
        assert "frequency" in params
        assert "speed" in params
        assert "color_phase" in params

    def test_wave_params(self):
        rng = random.Random(42)
        params = generate_random_params("wave", rng)
        assert "wave_count" in params
        assert "frequency" in params

    def test_flame_params(self):
        rng = random.Random(42)
        params = generate_random_params("flame", rng)
        assert "intensity" in params

    def test_moire_params(self):
        rng = random.Random(42)
        params = generate_random_params("moire", rng)
        assert "freq_a" in params
        assert "freq_b" in params

    def test_noise_field_params(self):
        rng = random.Random(42)
        params = generate_random_params("noise_field", rng)
        assert "scale" in params
        assert "octaves" in params

    def test_sdf_shapes_params(self):
        rng = random.Random(42)
        params = generate_random_params("sdf_shapes", rng)
        assert "shape_count" in params
        assert "shape_type" in params

    def test_unknown_effect_raises(self):
        rng = random.Random(42)
        with pytest.raises(ValueError):
            generate_random_params("nonexistent_effect", rng)

    def test_reproducibility(self):
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        params1 = generate_random_params("plasma", rng1)
        params2 = generate_random_params("plasma", rng2)
        assert params1 == params2
