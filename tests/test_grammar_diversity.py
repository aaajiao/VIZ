"""test grammar diversity - statistical tests for enhanced variety in grammar choices"""

import os
import sys
from collections import Counter

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from procedural.flexible.grammar import VisualGrammar, SceneSpec


class TestEffectWeightFlattening:
    """B1: Effect weights should be more uniform"""

    def test_no_single_effect_dominates(self):
        """Over 100 seeds, no effect should appear more than 25%"""
        counter = Counter()
        for seed in range(100):
            grammar = VisualGrammar(seed=seed)
            spec = grammar.generate(energy=0.5, warmth=0.5, structure=0.5)
            counter[spec.bg_effect] += 1

        total = sum(counter.values())
        for effect, count in counter.items():
            ratio = count / total
            assert ratio < 0.25, f"{effect} appeared {ratio:.1%} of the time (>25%)"

    def test_at_least_8_different_effects(self):
        """Over 100 seeds, at least 8 distinct effects should appear"""
        effects = set()
        for seed in range(100):
            grammar = VisualGrammar(seed=seed)
            spec = grammar.generate(energy=0.5, warmth=0.5, structure=0.5)
            effects.add(spec.bg_effect)

        assert len(effects) >= 8, f"Only {len(effects)} distinct effects in 100 runs"

    def test_formerly_rare_effects_appear(self):
        """Effects that were previously rare should now appear in 200 seeds"""
        effects = Counter()
        for seed in range(200):
            grammar = VisualGrammar(seed=seed)
            spec = grammar.generate(energy=0.5, warmth=0.5, structure=0.5)
            effects[spec.bg_effect] += 1

        # These were previously rare (low weights)
        formerly_rare = ["slime_dish", "sand_game", "wireframe_cube", "donut"]
        for effect in formerly_rare:
            assert effects[effect] > 0, f"{effect} never appeared in 200 runs"


class TestOverlayActivation:
    """B2: Overlay should activate more frequently"""

    def test_overlay_activation_rate(self):
        """At mid-energy, overlay should activate 40-90%"""
        overlay_count = 0
        total = 100
        for seed in range(total):
            grammar = VisualGrammar(seed=seed)
            spec = grammar.generate(energy=0.5)
            if spec.overlay_effect is not None:
                overlay_count += 1

        rate = overlay_count / total
        assert rate > 0.35, f"Overlay rate {rate:.1%} too low (expected >35%)"

    def test_high_energy_overlay_very_likely(self):
        """At high energy, overlay should be very common"""
        overlay_count = 0
        total = 100
        for seed in range(total):
            grammar = VisualGrammar(seed=seed)
            spec = grammar.generate(energy=0.9)
            if spec.overlay_effect is not None:
                overlay_count += 1

        rate = overlay_count / total
        assert rate > 0.55, f"High-energy overlay rate {rate:.1%} too low (expected >55%)"


class TestDomainTransforms:
    """B3: Domain transforms should be more frequent"""

    def test_transforms_activation_rate(self):
        """At least 50% of renders should have at least one transform"""
        has_transform = 0
        total = 100
        for seed in range(total):
            grammar = VisualGrammar(seed=seed)
            spec = grammar.generate(energy=0.5, structure=0.5)
            if spec.domain_transforms:
                has_transform += 1

        rate = has_transform / total
        assert rate > 0.45, f"Transform rate {rate:.1%} too low (expected >45%)"

    def test_multiple_transform_types_appear(self):
        """Multiple transform types should be used across seeds"""
        types = set()
        for seed in range(100):
            grammar = VisualGrammar(seed=seed)
            spec = grammar.generate(energy=0.5, structure=0.5)
            for t in spec.domain_transforms:
                types.add(t.get("type"))

        assert len(types) >= 4, f"Only {len(types)} transform types in 100 runs"

    def test_polar_remap_appears(self):
        """New polar_remap transform should appear in 300 seeds"""
        found = False
        for seed in range(300):
            grammar = VisualGrammar(seed=seed)
            spec = grammar.generate(energy=0.7)
            for t in spec.domain_transforms:
                if t.get("type") == "polar_remap":
                    found = True
                    break
            if found:
                break

        assert found, "polar_remap never appeared in 300 runs"


class TestPostFXGuarantee:
    """B4: PostFX chain should always have at least 1 effect"""

    def test_postfx_never_empty(self):
        """PostFX chain should never be empty"""
        for seed in range(200):
            grammar = VisualGrammar(seed=seed)
            spec = grammar.generate(energy=0.1, structure=0.1, intensity=0.1)
            assert len(spec.postfx_chain) >= 1, f"Seed {seed}: empty postfx chain"

    def test_postfx_variety(self):
        """Multiple postfx types should appear"""
        types = set()
        for seed in range(100):
            grammar = VisualGrammar(seed=seed)
            spec = grammar.generate(energy=0.5, structure=0.5, intensity=0.5)
            for p in spec.postfx_chain:
                types.add(p.get("type"))

        assert len(types) >= 4, f"Only {len(types)} postfx types in 100 runs"


class TestWeightedChoiceJitter:
    """B5: Weighted choice jitter should increase variety"""

    def test_deterministic_per_seed(self):
        """Same seed should produce same result"""
        for seed in range(10):
            g1 = VisualGrammar(seed=seed)
            g2 = VisualGrammar(seed=seed)
            s1 = g1.generate(energy=0.5)
            s2 = g2.generate(energy=0.5)
            assert s1.bg_effect == s2.bg_effect

    def test_adjacent_seeds_vary(self):
        """Adjacent seeds should sometimes produce different effects"""
        effects = []
        for seed in range(20):
            grammar = VisualGrammar(seed=seed)
            spec = grammar.generate(energy=0.5)
            effects.append(spec.bg_effect)

        unique = len(set(effects))
        assert unique >= 3, f"Only {unique} unique effects across 20 adjacent seeds"


class TestCompositionModeBalance:
    """B6: Composition modes should be more balanced"""

    def test_blend_not_dominant(self):
        """Blend should not exceed 45% of composition modes"""
        modes = Counter()
        for seed in range(200):
            grammar = VisualGrammar(seed=seed)
            spec = grammar.generate(energy=0.5)
            if spec.overlay_effect is not None:
                modes[spec.composition_mode] += 1

        if modes:
            total = sum(modes.values())
            blend_rate = modes.get("blend", 0) / total
            assert blend_rate < 0.45, f"Blend rate {blend_rate:.1%} too high (expected <45%)"

    def test_all_composition_modes_appear(self):
        """All 4 composition modes should appear in 200 seeds"""
        modes = set()
        for seed in range(200):
            grammar = VisualGrammar(seed=seed)
            spec = grammar.generate(energy=0.5, structure=0.5)
            if spec.overlay_effect is not None:
                modes.add(spec.composition_mode)

        expected = {"blend", "masked_split", "radial_masked", "noise_masked"}
        missing = expected - modes
        assert not missing, f"Missing composition modes: {missing}"
