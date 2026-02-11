#!/usr/bin/env python3
"""
VIZ - ASCII Art Visualization CLI
ASCII 艺术可视化命令行工具

AI 是大脑，VIZ 是画笔。

Usage:

    # Pure visual generation
    python3 viz.py generate --emotion euphoria --seed 42

    # With content data via stdin JSON
    echo '{"headline":"DOW +600","emotion":"euphoria"}' | python3 viz.py generate

    # With CLI args
    python3 viz.py generate --emotion panic --title "CRASH"

    # Image to ASCII conversion
    python3 viz.py convert image.png --charset blocks

    # Query available options
    python3 viz.py capabilities
"""

from __future__ import annotations

import argparse
import json
import os
import select
import sys
import time
from typing import Any, cast

# Ensure project root on path
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _script_dir)

from datetime import datetime


_VALID_LAYOUTS = {"random_scatter", "grid_jitter", "spiral", "force_directed", "preset"}
_VALID_DECORATIONS = {
    "corners",
    "edges",
    "scattered",
    "minimal",
    "none",
    "frame",
    "grid_lines",
    "circuit",
}
_VALID_BLEND_MODES = {"ADD", "SCREEN", "OVERLAY", "MULTIPLY"}


def _parse_compound_arg(arg_str):
    """解析复合参数 - Parse 'name:key=val,key=val' into dict"""
    if ":" not in arg_str:
        return {"type": arg_str}
    name, rest = arg_str.split(":", 1)
    result = {"type": name}
    for pair in rest.split(","):
        if "=" in pair:
            k, v = pair.split("=", 1)
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass
            result[k.strip()] = v
    return result


def _validate_overrides(overrides):
    """
    覆盖参数白名单校验 - Validate override values against known whitelists

    Returns list of error strings (empty = valid).
    """
    errors = []

    if "effect" in overrides:
        from procedural.effects import EFFECT_REGISTRY

        valid_effects = set(EFFECT_REGISTRY.keys()) | {"cppn"}
        if overrides["effect"] not in valid_effects:
            errors.append(
                f"Unknown effect '{overrides['effect']}', valid: {sorted(valid_effects)}"
            )

    if "layout" in overrides:
        if overrides["layout"] not in _VALID_LAYOUTS:
            errors.append(
                f"Unknown layout '{overrides['layout']}', valid: {sorted(_VALID_LAYOUTS)}"
            )

    if "decoration" in overrides:
        if overrides["decoration"] not in _VALID_DECORATIONS:
            errors.append(
                f"Unknown decoration '{overrides['decoration']}', valid: {sorted(_VALID_DECORATIONS)}"
            )

    if "gradient" in overrides:
        from procedural.palette import ASCII_GRADIENTS

        if overrides["gradient"] not in ASCII_GRADIENTS:
            errors.append(
                f"Unknown gradient '{overrides['gradient']}', valid: {sorted(ASCII_GRADIENTS.keys())}"
            )

    if "overlay" in overrides:
        ov = overrides["overlay"]
        if isinstance(ov, dict):
            if ov.get("effect"):
                from procedural.effects import EFFECT_REGISTRY

                valid_effects = set(EFFECT_REGISTRY.keys()) | {"cppn"}
                if ov["effect"] not in valid_effects:
                    errors.append(
                        f"Unknown overlay effect '{ov['effect']}', valid: {sorted(valid_effects)}"
                    )
            if ov.get("blend"):
                if ov["blend"] not in _VALID_BLEND_MODES:
                    errors.append(
                        f"Unknown blend mode '{ov['blend']}', valid: {sorted(_VALID_BLEND_MODES)}"
                    )
            if ov.get("mix") is not None:
                try:
                    mix = float(ov["mix"])
                    if not (0.0 <= mix <= 1.0):
                        errors.append(f"overlay.mix = {mix} out of range [0, 1]")
                except (TypeError, ValueError):
                    errors.append(f"overlay.mix must be a number, got '{ov['mix']}'")

    if "domain_transforms" in overrides:
        from procedural.transforms import TRANSFORM_REGISTRY

        for t in overrides["domain_transforms"]:
            t_type = t.get("type", "") if isinstance(t, dict) else str(t)
            if t_type not in TRANSFORM_REGISTRY:
                errors.append(
                    f"Unknown transform '{t_type}', valid: {sorted(TRANSFORM_REGISTRY.keys())}"
                )

    if "postfx_chain" in overrides:
        from procedural.postfx import POSTFX_REGISTRY

        for p in overrides["postfx_chain"]:
            p_type = p.get("type", "") if isinstance(p, dict) else str(p)
            if p_type not in POSTFX_REGISTRY:
                errors.append(
                    f"Unknown postfx '{p_type}', valid: {sorted(POSTFX_REGISTRY.keys())}"
                )

    if "composition_mode" in overrides:
        valid_modes = {"blend", "masked_split", "radial_masked", "noise_masked"}
        if overrides["composition_mode"] not in valid_modes:
            errors.append(
                f"Unknown composition mode '{overrides['composition_mode']}', valid: {sorted(valid_modes)}"
            )

    if "mask_type" in overrides:
        from procedural.masks import MASK_REGISTRY

        if overrides["mask_type"] not in MASK_REGISTRY:
            errors.append(
                f"Unknown mask '{overrides['mask_type']}', valid: {sorted(MASK_REGISTRY.keys())}"
            )

    if "variant" in overrides:
        if not isinstance(overrides["variant"], str):
            errors.append(f"variant must be a string, got {type(overrides['variant']).__name__}")

    if overrides.get("color_scheme"):
        from procedural.palette import COLOR_SCHEMES

        if overrides["color_scheme"] not in COLOR_SCHEMES:
            errors.append(
                f"Unknown color_scheme '{overrides['color_scheme']}', valid: {sorted(COLOR_SCHEMES.keys())}"
            )

    return errors


def cmd_generate(args):
    """
    生成可视化 - Generate visualization

    Accepts content via stdin JSON and/or CLI args.
    Outputs result JSON to stdout.
    """
    from procedural.flexible import (
        FlexiblePipeline,
        EmotionVector,
        text_to_emotion,
        VAD_ANCHORS,
    )
    from lib.content import make_content, content_has_data

    # === 1. Parse input ===
    # Try reading stdin JSON (non-blocking: skip if no data available)
    stdin_data = {}
    if not sys.stdin.isatty():
        try:
            ready, _, _ = select.select([sys.stdin], [], [], 0.1)
            if ready:
                raw = sys.stdin.read()
                if raw.strip():
                    stdin_data = json.loads(raw)
        except json.JSONDecodeError as e:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "message": f"Invalid stdin JSON: {e}",
                    }
                ),
                file=sys.stderr,
            )
        except (IOError, OSError):
            pass

    # Merge CLI args over stdin data
    content_data = dict(stdin_data)

    if args.emotion:
        content_data["emotion"] = args.emotion
    if args.title:
        content_data["title"] = args.title
    if args.text:
        content_data["body"] = args.text
    if args.headline:
        content_data["headline"] = args.headline
    if args.metrics:
        content_data["metrics"] = args.metrics
    if args.vad:
        content_data["vad"] = args.vad
    if args.effect:
        content_data["effect"] = args.effect
    if args.seed is not None:
        content_data["seed"] = args.seed
    if args.layout:
        content_data["layout"] = args.layout
    if args.decoration:
        content_data["decoration"] = args.decoration
    if args.gradient:
        content_data["gradient"] = args.gradient
    if args.video:
        content_data["video"] = True
    if args.duration != 3.0:
        content_data["duration"] = args.duration
    if args.fps != 15:
        content_data["fps"] = args.fps
    if args.variants != 1:
        content_data["variants"] = args.variants
    if args.mp4:
        content_data["mp4"] = True
        content_data["video"] = True  # MP4 implies video mode
    if args.transforms:
        content_data["transforms"] = [_parse_compound_arg(t) for t in args.transforms]
    if args.postfx:
        content_data["postfx"] = [_parse_compound_arg(p) for p in args.postfx]
    if args.overlay_effect:
        overlay = content_data.get("overlay", {})
        if not isinstance(overlay, dict):
            overlay = {}
        overlay["effect"] = args.overlay_effect
        if args.blend_mode:
            overlay["blend"] = args.blend_mode
        if args.overlay_mix is not None:
            overlay["mix"] = args.overlay_mix
        content_data["overlay"] = overlay
    elif args.blend_mode or args.overlay_mix is not None:
        overlay = content_data.get("overlay", {})
        if not isinstance(overlay, dict):
            overlay = {}
        if args.blend_mode:
            overlay["blend"] = args.blend_mode
        if args.overlay_mix is not None:
            overlay["mix"] = args.overlay_mix
        if overlay:
            content_data["overlay"] = overlay
    if args.composition:
        content_data["composition"] = args.composition
    if args.mask:
        content_data["mask"] = _parse_compound_arg(args.mask)
    if args.variant:
        content_data["variant"] = args.variant
    if args.palette:
        parsed_palette = []
        for p in args.palette:
            parts = p.split(",")
            if len(parts) == 3:
                parsed_palette.append([int(x) for x in parts])
        if len(parsed_palette) >= 2:
            content_data["palette"] = parsed_palette
    if args.width:
        content_data["width"] = args.width
    if args.height:
        content_data["height"] = args.height

    content = make_content(content_data)

    # === 2. Resolve emotion ===
    emotion_vector = None
    emotion_name = str(content["emotion"]) if content.get("emotion") else None

    if content.get("vad"):
        # Direct VAD vector
        vad = content["vad"]
        try:
            if isinstance(vad, str):
                parts = [float(x) for x in vad.split(",")]
            elif isinstance(vad, (list, tuple)):
                parts = [float(x) for x in vad]
            else:
                raise ValueError(
                    f"vad must be string 'V,A,D' or list [V,A,D], got {type(vad).__name__}"
                )

            if len(parts) != 3:
                raise ValueError(
                    f"vad requires exactly 3 values (V,A,D), got {len(parts)}"
                )

            for i, v in enumerate(parts):
                if not (-1.0 <= v <= 1.0):
                    raise ValueError(f"vad[{i}] = {v} out of range [-1, 1]")

            emotion_vector = EmotionVector(*parts)
        except ValueError as e:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "message": f"Invalid --vad: {e}",
                    }
                )
            )
            return
    elif emotion_name:
        emotion_name = emotion_name  # Will be passed to pipeline
    elif content.get("body"):
        # Infer from body text (fallback only)
        pass  # Pipeline handles text_to_emotion

    # === 3. Build vocabulary ===
    vocab = content.get("vocabulary", {})

    # Build content dict for pipeline
    pipeline_content = {
        "headline": content.get("headline"),
        "metrics": content.get("metrics", []),
        "timestamp": content.get("timestamp"),
        "body": content.get("body"),
        "vocabulary": vocab,
    }

    # === 4. Determine seed ===
    import random

    raw_seed = content.get("seed")
    if raw_seed is not None:
        seed = int(raw_seed)
    else:
        seed = random.randint(0, 999999)

    # === 5. Generate ===
    output_dir = args.output_dir or os.path.join(_script_dir, "media")
    os.makedirs(output_dir, exist_ok=True)
    timestamp_str = time.strftime("%Y%m%d_%H%M%S")

    # Compute output and internal resolution
    out_w = content.get("width") or 1080
    out_h = content.get("height") or 1080
    # Internal buffer: ~6.75x smaller, minimum 40px, keep aspect ratio
    _SCALE = 6.75
    buf_w = max(40, round(out_w / _SCALE))
    buf_h = max(40, round(out_h / _SCALE))

    pipe = FlexiblePipeline(
        seed=seed,
        internal_size=(buf_w, buf_h),
        output_size=(out_w, out_h),
    )

    # Build overrides for pipeline (CLI/stdin params that override grammar choices)
    overrides = {}
    if content.get("effect"):
        overrides["effect"] = content["effect"]
    if content.get("layout"):
        overrides["layout"] = content["layout"]
    if content.get("decoration"):
        overrides["decoration"] = content["decoration"]
    if content.get("gradient"):
        overrides["gradient"] = content["gradient"]
    if content.get("overlay"):
        overrides["overlay"] = content["overlay"]
    if content.get("params"):
        overrides["params"] = content["params"]
    if content.get("transforms"):
        overrides["domain_transforms"] = content["transforms"]
    if content.get("postfx"):
        overrides["postfx_chain"] = content["postfx"]
    if content.get("composition"):
        overrides["composition_mode"] = content["composition"]
    if content.get("mask"):
        mask_data = content["mask"]
        if isinstance(mask_data, dict):
            overrides["mask_type"] = mask_data.get("type", "radial")
            mask_params = {k: v for k, v in mask_data.items() if k != "type"}
            if mask_params:
                overrides["mask_params"] = mask_params
        else:
            overrides["mask_type"] = str(mask_data)
    if content.get("variant"):
        overrides["variant"] = content["variant"]
    if content.get("color_scheme"):
        overrides["color_scheme"] = content["color_scheme"]
    if content.get("palette"):
        overrides["palette"] = content["palette"]

    # Validate overrides against known values
    errors = _validate_overrides(overrides)
    if errors:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": "Invalid override values",
                    "errors": errors,
                }
            )
        )
        return

    results: list[dict[str, Any]] = []

    variant_count = cast(int, content.get("variants") or 1)
    is_video = bool(content.get("video"))
    want_mp4 = bool(content.get("mp4"))
    duration = cast(float, content.get("duration") or 3.0)
    fps = cast(int, content.get("fps") or 15)

    body_text = str(content["body"]) if content.get("body") else None
    title_text = str(content["title"]) if content.get("title") else None

    for variant_idx in range(variant_count):
        variant_seed = seed + variant_idx

        if is_video:
            suffix = f"_v{variant_idx}" if variant_count > 1 else ""
            output_path = os.path.join(output_dir, f"viz_{timestamp_str}{suffix}.gif")

            pipe.generate_video(
                text=body_text,
                emotion=emotion_name,
                emotion_vector=emotion_vector,
                seed=variant_seed,
                title=title_text,
                content=pipeline_content
                if content_has_data(pipeline_content)
                else None,
                duration=duration,
                fps=fps,
                output_path=output_path,
                overrides=overrides or None,
            )

            result_entry = {
                "path": os.path.abspath(output_path),
                "seed": variant_seed,
                "format": "gif",
                "duration": duration,
                "fps": fps,
            }

            if want_mp4:
                from procedural.engine import Engine

                mp4_path = output_path.replace(".gif", ".mp4")
                frames = pipe.last_frames
                if frames and Engine.save_mp4(frames, mp4_path, fps=fps):
                    result_entry["mp4_path"] = os.path.abspath(mp4_path)

            results.append(result_entry)

        else:
            suffix = f"_v{variant_idx}" if variant_count > 1 else ""
            output_path = os.path.join(output_dir, f"viz_{timestamp_str}{suffix}.png")

            pipe.generate(
                text=body_text,
                emotion=emotion_name,
                emotion_vector=emotion_vector,
                seed=variant_seed,
                title=title_text,
                content=pipeline_content
                if content_has_data(pipeline_content)
                else None,
                output_path=output_path,
                overrides=overrides or None,
            )

            results.append(
                {
                    "path": os.path.abspath(output_path),
                    "seed": variant_seed,
                    "format": "png",
                }
            )

    # === 6. Output JSON ===
    output = {
        "status": "ok",
        "results": results,
        "emotion": emotion_name,
        "resolution": [out_w, out_h],
    }

    print(json.dumps(output, ensure_ascii=False))


def cmd_convert(args):
    """
    图像转 ASCII - Convert image to ASCII art

    Wraps lib/ascii_convert module.
    """
    try:
        from lib.ascii_convert import image_to_ascii_art, add_market_overlay
    except ImportError:
        from viz.lib.ascii_convert import image_to_ascii_art, add_market_overlay  # pyright: ignore[reportMissingImports]

    if not os.path.exists(args.image):
        result = {"status": "error", "message": f"Image not found: {args.image}"}
        print(json.dumps(result))
        return

    # Parse options
    charset = args.charset or "classic"
    scale = args.scale or 0.3
    emotion = args.emotion or "neutral"

    # Emotion-based defaults
    if emotion == "bull":
        rgb_limit = (100, 255, 100)
        saturation = 1.5
        brightness = 1.2
        bg_color = "#001a00"
    elif emotion == "bear":
        rgb_limit = (255, 100, 100)
        saturation = 1.5
        brightness = 1.1
        bg_color = "#1a0000"
    else:
        rgb_limit = (255, 255, 255)
        saturation = 1.0
        brightness = 1.0
        bg_color = "#0a0a0a"

    try:
        ascii_image, ascii_text = image_to_ascii_art(
            args.image,
            char_set=charset,
            scale=scale,
            rgb_limit=rgb_limit,
            saturation=saturation,
            brightness=brightness,
            bg_color=bg_color,
        )
    except Exception as e:
        result = {"status": "error", "message": f"Failed to process image: {e}"}
        print(json.dumps(result))
        return

    # Optional overlay from stdin (non-blocking)
    overlay_data = {}
    if not sys.stdin.isatty():
        try:
            ready, _, _ = select.select([sys.stdin], [], [], 0.1)
            if ready:
                raw = sys.stdin.read()
                if raw.strip():
                    overlay_data = json.loads(raw)
        except json.JSONDecodeError as e:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "message": f"Invalid stdin JSON: {e}",
                    }
                ),
                file=sys.stderr,
            )
        except (IOError, OSError):
            pass

    if overlay_data:
        ascii_image = add_market_overlay(ascii_image, overlay_data)

    # Save
    output_dir = args.output_dir or os.path.join(_script_dir, "media")
    os.makedirs(output_dir, exist_ok=True)
    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"convert_{timestamp_str}.png")

    ascii_image.save(output_path, "PNG", quality=95)

    result = {
        "status": "ok",
        "path": os.path.abspath(output_path),
        "size": list(ascii_image.size),
        "charset": charset,
    }
    print(json.dumps(result, ensure_ascii=False))


def cmd_capabilities(args):
    """
    输出能力描述 - Output capabilities schema

    Returns JSON describing all available options for AI discovery.
    """
    from procedural.effects import EFFECT_REGISTRY
    from procedural.flexible.emotion import VAD_ANCHORS
    from procedural.transforms import TRANSFORM_REGISTRY
    from procedural.postfx import POSTFX_REGISTRY
    from procedural.masks import MASK_REGISTRY
    from procedural.effects.variants import VARIANT_REGISTRY
    from procedural.palette import ASCII_GRADIENTS, COLOR_SCHEMES
    from lib.kaomoji_data import KAOMOJI_SINGLE

    capabilities = {
        "version": "0.5.0",
        "description": "VIZ - ASCII Art Visualization CLI. AI is the brain, VIZ is the paintbrush.",
        "commands": {
            "generate": "Generate 1080x1080 PNG/GIF visualization",
            "convert": "Convert image to ASCII art",
            "capabilities": "This command - list all options",
        },
        "emotions": {
            name: {
                "valence": round(ev.valence, 2),
                "arousal": round(ev.arousal, 2),
                "dominance": round(ev.dominance, 2),
            }
            for name, ev in sorted(VAD_ANCHORS.items())
        },
        "effects": sorted(EFFECT_REGISTRY.keys()),
        "kaomoji_moods": sorted(KAOMOJI_SINGLE.keys()),
        "color_schemes": sorted(COLOR_SCHEMES.keys()),
        "blend_modes": ["ADD", "SCREEN", "OVERLAY", "MULTIPLY"],
        "layouts": [
            "random_scatter",
            "grid_jitter",
            "spiral",
            "force_directed",
            "preset",
        ],
        "decorations": [
            "corners",
            "edges",
            "scattered",
            "minimal",
            "none",
            "frame",
            "grid_lines",
            "circuit",
        ],
        "gradients": sorted(ASCII_GRADIENTS.keys()),
        "transforms": sorted(TRANSFORM_REGISTRY.keys()),
        "postfx": sorted(POSTFX_REGISTRY.keys()),
        "masks": sorted(MASK_REGISTRY.keys()),
        "composition_modes": ["blend", "masked_split", "radial_masked", "noise_masked"],
        "variants": {
            effect: [v["name"] for v in variants]
            for effect, variants in sorted(VARIANT_REGISTRY.items())
        },
        "charsets_convert": [
            "classic",
            "simple",
            "blocks",
            "bull",
            "bear",
            "numbers",
            "money",
        ],
        "input_schema": {
            "headline": "string - main title text",
            "metrics": "list[string] - data metrics to display",
            "body": "string - text for emotion inference (fallback)",
            "emotion": "string - emotion name from emotions list",
            "vad": "string 'V,A,D' or [V,A,D] - direct VAD vector",
            "timestamp": "string - timestamp to display",
            "effect": "string - background effect name",
            "seed": "int - reproducibility seed",
            "params": "dict - fine-grained effect parameters",
            "layout": "string - layout algorithm name",
            "decoration": "string - decoration style",
            "gradient": "string - ASCII gradient name",
            "color_scheme": "string - color scheme name (heat|rainbow|cool|matrix|plasma|ocean|fire|default)",
            "overlay": "dict {effect, blend, mix} - overlay effect config",
            "vocabulary": "dict - override visual vocabulary {particles, kaomoji_moods, decoration_chars}",
            "video": "bool - output GIF instead of PNG",
            "duration": "float - GIF duration in seconds (default 3.0)",
            "fps": "int - frames per second (default 15)",
            "variants": "int - number of variants to generate",
            "title": "string - title overlay text",
            "transforms": "list[str] - domain transform chain, e.g. ['kaleidoscope:segments=6']",
            "postfx": "list[str] - post-FX chain, e.g. ['vignette:strength=0.5']",
            "blend_mode": "string (ADD|SCREEN|OVERLAY|MULTIPLY) - blend mode for overlay",
            "overlay_mix": "float 0.0-1.0 - overlay mix ratio",
            "composition": "string (blend|masked_split|radial_masked|noise_masked)",
            "mask": "string - mask type+params, e.g. 'radial:center_x=0.5,radius=0.3'",
            "variant": "string - force effect variant name",
            "palette": "list[[r,g,b], ...] - custom color palette (2+ RGB triplets, 0-255), overrides color_scheme",
            "width": "int - output width in pixels (120-3840, default 1080)",
            "height": "int - output height in pixels (120-3840, default 1080)",
        },
        "output_schema": {
            "status": "string (ok|error)",
            "results": "list[{path, seed, format, ...}] - always an array, even for single result",
            "emotion": "string|null - emotion used",
            "resolution": "[width, height] - actual output resolution",
        },
    }

    emotions_dict = cast(dict[str, dict[str, float]], capabilities["emotions"])
    effects_list = cast(list[str], capabilities["effects"])
    moods_list = cast(list[str], capabilities["kaomoji_moods"])
    schemes_list = cast(list[str], capabilities["color_schemes"])
    layouts_list = cast(list[str], capabilities["layouts"])
    decorations_list = cast(list[str], capabilities["decorations"])

    format_type = args.format if hasattr(args, "format") else "json"
    if format_type == "json":
        print(json.dumps(capabilities, ensure_ascii=False, indent=2))
    else:
        # Human-readable
        print("=== VIZ Capabilities ===\n")
        print(f"Emotions ({len(emotions_dict)}):")
        for name in sorted(emotions_dict):
            ev: dict[str, float] = emotions_dict[name]
            print(
                f"  {name:<15} V={ev['valence']:+.2f} A={ev['arousal']:+.2f} D={ev['dominance']:+.2f}"
            )
        print(f"\nEffects ({len(effects_list)}): {', '.join(effects_list)}")
        print(f"Kaomoji Moods ({len(moods_list)}): {', '.join(moods_list)}")
        print(f"Color Schemes ({len(schemes_list)}): {', '.join(schemes_list)}")
        print(f"Layouts ({len(layouts_list)}): {', '.join(layouts_list)}")
        print(f"Decorations ({len(decorations_list)}): {', '.join(decorations_list)}")


def build_parser():
    """构建 CLI 解析器 - Build CLI parser"""
    parser = argparse.ArgumentParser(
        prog="viz",
        description="VIZ - ASCII Art Visualization CLI. AI is the brain, VIZ is the paintbrush.",
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令 Subcommand")

    # === generate ===
    gen = subparsers.add_parser("generate", help="生成可视化 Generate visualization")
    gen.add_argument("--emotion", help="情绪名称 (如 joy, fear, euphoria)")
    gen.add_argument("--title", help="标题文字")
    gen.add_argument("--text", help="文本输入 (用于情绪推断)")
    gen.add_argument("--headline", help="主标题")
    gen.add_argument("--metrics", nargs="*", help="指标列表")
    gen.add_argument("--vad", help="VAD 向量 (如 0.8,0.9,0.7)")
    gen.add_argument("--effect", help="背景效果")
    gen.add_argument("--seed", type=int, default=None, help="随机种子")
    gen.add_argument("--video", action="store_true", help="输出 GIF")
    gen.add_argument("--duration", type=float, default=3.0, help="GIF 时长")
    gen.add_argument("--fps", type=int, default=15, help="GIF 帧率")
    gen.add_argument("--variants", type=int, default=1, help="变体数量")
    gen.add_argument("--layout", help="布局算法")
    gen.add_argument("--decoration", help="装饰风格")
    gen.add_argument("--gradient", help="ASCII 梯度")
    gen.add_argument("--transforms", nargs="*", help="域变换链 (如 kaleidoscope:segments=6 tile:cols=3,rows=3)")
    gen.add_argument("--postfx", nargs="*", help="后处理链 (如 vignette:strength=0.5 scanlines:spacing=4)")
    gen.add_argument("--blend-mode", choices=["ADD", "SCREEN", "OVERLAY", "MULTIPLY"], help="混合模式")
    gen.add_argument("--overlay", help="叠加效果名", dest="overlay_effect")
    gen.add_argument("--overlay-mix", type=float, help="叠加混合比 0.0-1.0")
    gen.add_argument("--composition", choices=["blend", "masked_split", "radial_masked", "noise_masked"], help="合成模式")
    gen.add_argument("--mask", help="遮罩类型+参数 (如 radial:center_x=0.5,radius=0.3)")
    gen.add_argument("--variant", help="强制效果变体名")
    gen.add_argument("--palette", nargs="*", help="自定义调色盘 (如 255,0,0 0,255,0 0,0,255)")
    gen.add_argument("--width", type=int, help="输出宽度 (120-3840, 默认 1080)")
    gen.add_argument("--height", type=int, help="输出高度 (120-3840, 默认 1080)")
    gen.add_argument("--output-dir", help="输出目录")
    gen.add_argument("--mp4", action="store_true", help="同时输出 MP4 (需要 FFmpeg)")

    # === convert ===
    conv = subparsers.add_parser("convert", help="图像转 ASCII Convert image to ASCII")
    conv.add_argument("image", help="图像路径")
    conv.add_argument("--charset", help="字符集 (classic, blocks, bull, bear, ...)")
    conv.add_argument("--scale", type=float, help="缩放比例")
    conv.add_argument("--emotion", help="情绪 (bull, bear, neutral)")
    conv.add_argument("--output-dir", help="输出目录")

    # === capabilities ===
    cap = subparsers.add_parser("capabilities", help="列出所有可用选项")
    cap.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="输出格式 (default: json)",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "convert":
        cmd_convert(args)
    elif args.command == "capabilities":
        cmd_capabilities(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
