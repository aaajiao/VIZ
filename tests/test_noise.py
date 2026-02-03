"""test procedural/core/noise.py - ValueNoise, fbm, turbulence"""

import pytest
from procedural.core.noise import ValueNoise


class TestValueNoise:
    def test_output_range(self):
        noise = ValueNoise(seed=42)
        for x in range(10):
            for y in range(10):
                value = noise(x * 0.1, y * 0.1)
                assert 0.0 <= value <= 1.0

    def test_reproducibility(self):
        noise1 = ValueNoise(seed=42)
        noise2 = ValueNoise(seed=42)
        for x in range(5):
            for y in range(5):
                assert noise1(x, y) == noise2(x, y)

    def test_different_seeds_produce_different_values(self):
        noise1 = ValueNoise(seed=42)
        noise2 = ValueNoise(seed=99)
        values1 = [noise1(x, 0) for x in range(10)]
        values2 = [noise2(x, 0) for x in range(10)]
        assert values1 != values2

    def test_smoothness(self):
        noise = ValueNoise(seed=42)
        prev = noise(0, 0)
        max_delta = 0
        for i in range(1, 100):
            curr = noise(i * 0.01, 0)
            max_delta = max(max_delta, abs(curr - prev))
            prev = curr
        assert max_delta < 0.5


class TestFBM:
    def test_output_range(self):
        noise = ValueNoise(seed=42)
        for x in range(10):
            for y in range(10):
                value = noise.fbm(x * 0.1, y * 0.1, octaves=4)
                assert 0.0 <= value <= 1.0

    def test_more_octaves_adds_detail(self):
        noise = ValueNoise(seed=42)
        values_1oct = [noise.fbm(x * 0.1, 0, octaves=1) for x in range(100)]
        values_4oct = [noise.fbm(x * 0.1, 0, octaves=4) for x in range(100)]

        def variance(vals):
            mean = sum(vals) / len(vals)
            return sum((v - mean) ** 2 for v in vals) / len(vals)

        assert variance(values_4oct) != variance(values_1oct)

    def test_lacunarity_and_gain(self):
        noise = ValueNoise(seed=42)
        v1 = noise.fbm(5, 5, octaves=4, lacunarity=2.0, gain=0.5)
        v2 = noise.fbm(5, 5, octaves=4, lacunarity=3.0, gain=0.3)
        assert v1 != v2


class TestTurbulence:
    def test_output_range(self):
        noise = ValueNoise(seed=42)
        for x in range(10):
            for y in range(10):
                value = noise.turbulence(x * 0.1, y * 0.1, octaves=4)
                assert 0.0 <= value <= 1.0

    def test_differs_from_fbm(self):
        noise = ValueNoise(seed=42)
        fbm_val = noise.fbm(5, 5, octaves=4)
        turb_val = noise.turbulence(5, 5, octaves=4)
        assert fbm_val != turb_val
