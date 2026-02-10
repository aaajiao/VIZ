"""test director mode - CLI args for transforms, postfx, composition, masks, variants"""

import json
import importlib
import os
import subprocess
import tempfile
import pytest
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# viz.py is the CLI module (not the viz/ package __init__)
_viz_spec = importlib.util.spec_from_file_location(
    "viz_cli",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "viz.py"),
)
_viz_mod = importlib.util.module_from_spec(_viz_spec)
_viz_spec.loader.exec_module(_viz_mod)
_parse_compound_arg = _viz_mod._parse_compound_arg
_validate_overrides = _viz_mod._validate_overrides


# === Unit tests for _parse_compound_arg ===


class TestParseCompoundArg:
    def test_name_only(self):
        assert _parse_compound_arg("kaleidoscope") == {"type": "kaleidoscope"}

    def test_name_with_int_param(self):
        result = _parse_compound_arg("kaleidoscope:segments=6")
        assert result == {"type": "kaleidoscope", "segments": 6}

    def test_name_with_float_param(self):
        result = _parse_compound_arg("vignette:strength=0.5")
        assert result == {"type": "vignette", "strength": 0.5}

    def test_name_with_multiple_params(self):
        result = _parse_compound_arg("tile:cols=3,rows=2")
        assert result == {"type": "tile", "cols": 3, "rows": 2}

    def test_name_with_string_param(self):
        result = _parse_compound_arg("foo:mode=bar")
        assert result == {"type": "foo", "mode": "bar"}

    def test_mixed_types(self):
        result = _parse_compound_arg("effect:a=1,b=0.5,c=hello")
        assert result["type"] == "effect"
        assert result["a"] == 1
        assert result["b"] == 0.5
        assert result["c"] == "hello"


# === Unit tests for _validate_overrides with new fields ===


class TestValidateOverridesDirector:
    def test_valid_transform(self):
        overrides = {"domain_transforms": [{"type": "kaleidoscope", "segments": 6}]}
        errors = _validate_overrides(overrides)
        assert errors == []

    def test_invalid_transform(self):
        overrides = {"domain_transforms": [{"type": "nonexistent"}]}
        errors = _validate_overrides(overrides)
        assert len(errors) == 1
        assert "nonexistent" in errors[0]

    def test_valid_postfx(self):
        overrides = {"postfx_chain": [{"type": "vignette", "strength": 0.5}]}
        errors = _validate_overrides(overrides)
        assert errors == []

    def test_invalid_postfx(self):
        overrides = {"postfx_chain": [{"type": "nonexistent"}]}
        errors = _validate_overrides(overrides)
        assert len(errors) == 1
        assert "nonexistent" in errors[0]

    def test_valid_composition_mode(self):
        overrides = {"composition_mode": "radial_masked"}
        errors = _validate_overrides(overrides)
        assert errors == []

    def test_invalid_composition_mode(self):
        overrides = {"composition_mode": "unknown"}
        errors = _validate_overrides(overrides)
        assert len(errors) == 1

    def test_valid_mask(self):
        overrides = {"mask_type": "radial"}
        errors = _validate_overrides(overrides)
        assert errors == []

    def test_invalid_mask(self):
        overrides = {"mask_type": "nonexistent"}
        errors = _validate_overrides(overrides)
        assert len(errors) == 1

    def test_valid_variant(self):
        overrides = {"variant": "warped"}
        errors = _validate_overrides(overrides)
        assert errors == []

    def test_invalid_variant_type(self):
        overrides = {"variant": 123}
        errors = _validate_overrides(overrides)
        assert len(errors) == 1
        assert "string" in errors[0]

    def test_multiple_errors(self):
        overrides = {
            "domain_transforms": [{"type": "bad"}],
            "postfx_chain": [{"type": "bad"}],
            "composition_mode": "bad",
        }
        errors = _validate_overrides(overrides)
        assert len(errors) == 3


# === Pipeline _apply_overrides tests ===


class TestApplyOverrides:
    def test_domain_transforms_override(self):
        from procedural.flexible.grammar import VisualGrammar, SceneSpec
        from procedural.flexible.pipeline import FlexiblePipeline

        pipe = FlexiblePipeline(seed=42)
        spec = SceneSpec()
        transforms = [{"type": "kaleidoscope", "segments": 6}]
        pipe._apply_overrides(spec, {"domain_transforms": transforms})
        assert spec.domain_transforms == transforms

    def test_postfx_chain_override(self):
        from procedural.flexible.grammar import SceneSpec
        from procedural.flexible.pipeline import FlexiblePipeline

        pipe = FlexiblePipeline(seed=42)
        spec = SceneSpec()
        chain = [{"type": "vignette", "strength": 0.5}]
        pipe._apply_overrides(spec, {"postfx_chain": chain})
        assert spec.postfx_chain == chain

    def test_composition_mode_override(self):
        from procedural.flexible.grammar import SceneSpec
        from procedural.flexible.pipeline import FlexiblePipeline

        pipe = FlexiblePipeline(seed=42)
        spec = SceneSpec()
        pipe._apply_overrides(spec, {"composition_mode": "radial_masked"})
        assert spec.composition_mode == "radial_masked"

    def test_mask_override(self):
        from procedural.flexible.grammar import SceneSpec
        from procedural.flexible.pipeline import FlexiblePipeline

        pipe = FlexiblePipeline(seed=42)
        spec = SceneSpec()
        pipe._apply_overrides(spec, {"mask_type": "radial", "mask_params": {"mask_radius": 0.3}})
        assert spec.mask_type == "radial"
        assert spec.mask_params["mask_radius"] == 0.3

    def test_variant_override(self):
        from procedural.flexible.grammar import SceneSpec
        from procedural.flexible.pipeline import FlexiblePipeline

        pipe = FlexiblePipeline(seed=42)
        spec = SceneSpec()
        spec.bg_effect = "plasma"
        pipe._apply_overrides(spec, {"variant": "warped"})
        assert "self_warp" in spec.bg_params

    def test_auto_overlay_for_nonblend_composition(self):
        from procedural.flexible.grammar import SceneSpec
        from procedural.flexible.pipeline import FlexiblePipeline

        pipe = FlexiblePipeline(seed=42)
        spec = SceneSpec()
        spec.overlay_effect = None
        pipe._apply_overrides(spec, {"composition_mode": "radial_masked"})
        assert spec.overlay_effect is not None
        assert spec.overlay_mix == 0.3


# === CLI integration tests ===


def run_cli(args, stdin=None, cwd=None):
    if cwd is None:
        cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cmd = ["python3", "viz.py"] + args
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, input=stdin, timeout=60
    )
    return result


def parse_json_output(result):
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise ValueError(f"No JSON found in output: {result.stdout}")


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestDirectorModeCLI:
    def test_generate_with_transforms(self, temp_dir):
        result = run_cli([
            "generate", "--emotion", "joy", "--seed", "42",
            "--transforms", "kaleidoscope:segments=6",
            "--output-dir", temp_dir,
        ])
        assert result.returncode == 0
        output = parse_json_output(result)
        assert output["status"] == "ok"

    def test_generate_with_postfx(self, temp_dir):
        result = run_cli([
            "generate", "--emotion", "joy", "--seed", "42",
            "--postfx", "vignette:strength=0.5", "scanlines:spacing=4",
            "--output-dir", temp_dir,
        ])
        assert result.returncode == 0
        output = parse_json_output(result)
        assert output["status"] == "ok"

    def test_generate_with_composition(self, temp_dir):
        result = run_cli([
            "generate", "--emotion", "joy", "--seed", "42",
            "--composition", "radial_masked",
            "--output-dir", temp_dir,
        ])
        assert result.returncode == 0
        output = parse_json_output(result)
        assert output["status"] == "ok"

    def test_generate_with_overlay_args(self, temp_dir):
        result = run_cli([
            "generate", "--emotion", "joy", "--seed", "42",
            "--overlay", "wave", "--blend-mode", "SCREEN", "--overlay-mix", "0.4",
            "--output-dir", temp_dir,
        ])
        assert result.returncode == 0
        output = parse_json_output(result)
        assert output["status"] == "ok"

    def test_generate_with_mask(self, temp_dir):
        result = run_cli([
            "generate", "--emotion", "joy", "--seed", "42",
            "--mask", "radial:center_x=0.5,radius=0.3",
            "--composition", "radial_masked",
            "--output-dir", temp_dir,
        ])
        assert result.returncode == 0
        output = parse_json_output(result)
        assert output["status"] == "ok"

    def test_generate_with_variant(self, temp_dir):
        result = run_cli([
            "generate", "--emotion", "joy", "--seed", "42",
            "--effect", "plasma", "--variant", "warped",
            "--output-dir", temp_dir,
        ])
        assert result.returncode == 0
        output = parse_json_output(result)
        assert output["status"] == "ok"

    def test_generate_full_director_mode(self, temp_dir):
        result = run_cli([
            "generate", "--emotion", "euphoria", "--seed", "100",
            "--effect", "plasma",
            "--overlay", "wave", "--blend-mode", "SCREEN", "--overlay-mix", "0.4",
            "--composition", "radial_masked",
            "--mask", "radial:center_x=0.5,radius=0.3",
            "--transforms", "mirror_quad",
            "--postfx", "color_shift:hue_shift=0.1",
            "--variant", "warped",
            "--output-dir", temp_dir,
        ])
        assert result.returncode == 0
        output = parse_json_output(result)
        assert output["status"] == "ok"

    def test_invalid_transform_returns_error(self, temp_dir):
        result = run_cli([
            "generate", "--emotion", "joy", "--seed", "42",
            "--transforms", "nonexistent",
            "--output-dir", temp_dir,
        ])
        output = parse_json_output(result)
        assert output["status"] == "error"

    def test_invalid_postfx_returns_error(self, temp_dir):
        result = run_cli([
            "generate", "--emotion", "joy", "--seed", "42",
            "--postfx", "nonexistent",
            "--output-dir", temp_dir,
        ])
        output = parse_json_output(result)
        assert output["status"] == "error"

    def test_stdin_json_with_new_fields(self, temp_dir):
        stdin_data = json.dumps({
            "emotion": "joy",
            "seed": 42,
            "transforms": [{"type": "kaleidoscope", "segments": 6}],
            "postfx": [{"type": "vignette", "strength": 0.5}],
            "composition": "radial_masked",
        })
        result = run_cli(["generate", "--output-dir", temp_dir], stdin=stdin_data)
        assert result.returncode == 0
        output = parse_json_output(result)
        assert output["status"] == "ok"


class TestCapabilitiesDirector:
    def test_capabilities_includes_new_fields(self):
        result = run_cli(["capabilities", "--format", "json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "transforms" in data
        assert "postfx" in data
        assert "masks" in data
        assert "composition_modes" in data
        assert "variants" in data

    def test_capabilities_transforms_content(self):
        result = run_cli(["capabilities", "--format", "json"])
        data = json.loads(result.stdout)
        assert "kaleidoscope" in data["transforms"]
        assert "mirror_quad" in data["transforms"]
        assert "tile" in data["transforms"]

    def test_capabilities_variants_grouped_by_effect(self):
        result = run_cli(["capabilities", "--format", "json"])
        data = json.loads(result.stdout)
        assert "plasma" in data["variants"]
        assert "warped" in data["variants"]["plasma"]

    def test_capabilities_input_schema_new_fields(self):
        result = run_cli(["capabilities", "--format", "json"])
        data = json.loads(result.stdout)
        schema = data["input_schema"]
        assert "transforms" in schema
        assert "postfx" in schema
        assert "composition" in schema
        assert "mask" in schema
        assert "variant" in schema
