"""test viz.py CLI - end-to-end tests for generate, convert, capabilities"""

import json
import os
import subprocess
import tempfile
import pytest


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


class TestCapabilities:
    def test_capabilities_json_output(self):
        result = run_cli(["capabilities", "--format", "json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "emotions" in data
        assert "effects" in data
        assert "sources" in data

    def test_capabilities_text_output(self):
        result = run_cli(["capabilities", "--format", "text"])
        assert result.returncode == 0
        assert "Emotions" in result.stdout or "emotions" in result.stdout.lower()

    def test_capabilities_has_required_emotions(self):
        result = run_cli(["capabilities", "--format", "json"])
        data = json.loads(result.stdout)
        emotions = data["emotions"]
        required = ["joy", "fear", "bull", "bear", "neutral"]
        for emotion in required:
            assert emotion in emotions


class TestGenerate:
    def test_generate_with_emotion(self, temp_dir):
        result = run_cli(
            ["generate", "--emotion", "joy", "--seed", "42", "--output-dir", temp_dir]
        )
        assert result.returncode == 0
        output = parse_json_output(result)
        assert output["status"] == "ok"
        assert os.path.exists(output["results"][0]["path"])

    def test_generate_with_stdin_json(self, temp_dir):
        stdin_data = json.dumps({"emotion": "bull", "seed": 42})
        result = run_cli(["generate", "--output-dir", temp_dir], stdin=stdin_data)
        assert result.returncode == 0
        output = parse_json_output(result)
        assert output["status"] == "ok"

    def test_generate_video(self, temp_dir):
        result = run_cli(
            [
                "generate",
                "--emotion",
                "calm",
                "--seed",
                "42",
                "--video",
                "--duration",
                "0.5",
                "--fps",
                "5",
                "--output-dir",
                temp_dir,
            ]
        )
        assert result.returncode == 0
        output = parse_json_output(result)
        assert output["status"] == "ok"
        assert output["results"][0]["path"].endswith(".gif")

    def test_generate_with_source(self, temp_dir):
        result = run_cli(
            [
                "generate",
                "--emotion",
                "bull",
                "--source",
                "market",
                "--seed",
                "42",
                "--output-dir",
                temp_dir,
            ]
        )
        assert result.returncode == 0
        output = parse_json_output(result)
        assert output["source"] == "market"

    def test_generate_reproducible(self, temp_dir):
        args = [
            "generate",
            "--emotion",
            "joy",
            "--seed",
            "12345",
            "--output-dir",
            temp_dir,
        ]
        result1 = run_cli(args)
        result2 = run_cli(args)
        out1 = parse_json_output(result1)
        out2 = parse_json_output(result2)
        assert out1["results"][0]["seed"] == out2["results"][0]["seed"]

    def test_generate_multiple_variants(self, temp_dir):
        result = run_cli(
            [
                "generate",
                "--emotion",
                "joy",
                "--seed",
                "42",
                "--variants",
                "2",
                "--output-dir",
                temp_dir,
            ]
        )
        assert result.returncode == 0
        output = parse_json_output(result)
        assert len(output["results"]) == 2

    def test_generate_with_vad(self, temp_dir):
        result = run_cli(
            [
                "generate",
                "--vad",
                "0.5,0.5,0.5",
                "--seed",
                "42",
                "--output-dir",
                temp_dir,
            ]
        )
        assert result.returncode == 0

    def test_generate_with_effect(self, temp_dir):
        result = run_cli(
            [
                "generate",
                "--emotion",
                "calm",
                "--effect",
                "plasma",
                "--seed",
                "42",
                "--output-dir",
                temp_dir,
            ]
        )
        assert result.returncode == 0

    def test_generate_with_layout(self, temp_dir):
        result = run_cli(
            [
                "generate",
                "--emotion",
                "joy",
                "--layout",
                "spiral",
                "--seed",
                "42",
                "--output-dir",
                temp_dir,
            ]
        )
        assert result.returncode == 0


class TestGenerateValidation:
    def test_invalid_effect_returns_error_status(self, temp_dir):
        result = run_cli(
            [
                "generate",
                "--emotion",
                "joy",
                "--effect",
                "nonexistent_effect",
                "--output-dir",
                temp_dir,
            ]
        )
        output = parse_json_output(result)
        assert output["status"] == "error"

    def test_invalid_layout_returns_error_status(self, temp_dir):
        result = run_cli(
            [
                "generate",
                "--emotion",
                "joy",
                "--layout",
                "nonexistent_layout",
                "--output-dir",
                temp_dir,
            ]
        )
        output = parse_json_output(result)
        assert output["status"] == "error"


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
