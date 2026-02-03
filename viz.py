#!/usr/bin/env python3
"""
VIZ - ASCII Art Visualization CLI
ASCII 艺术可视化命令行工具

AI 是大脑，VIZ 是画笔。

Usage:

    # Pure visual generation
    python3 viz.py generate --emotion euphoria --seed 42

    # With content data via stdin JSON
    echo '{"source":"market","headline":"DOW +600","emotion":"euphoria"}' | python3 viz.py generate

    # With CLI args
    python3 viz.py generate --emotion panic --title "CRASH" --source market

    # Image to ASCII conversion
    python3 viz.py convert image.png --charset blocks

    # Query available options
    python3 viz.py capabilities
"""

import argparse
import json
import os
import sys
import time

# Ensure project root on path
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _script_dir)

from datetime import datetime


_VALID_LAYOUTS = {"random_scatter", "grid_jitter", "spiral", "force_directed", "preset"}
_VALID_DECORATIONS = {"corners", "edges", "scattered", "minimal", "none", "frame", "grid_lines", "circuit"}
_VALID_BLEND_MODES = {"ADD", "SCREEN", "OVERLAY", "MULTIPLY"}


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
    from lib.vocabulary import get_vocabulary

    # === 1. Parse input ===
    # Try reading stdin JSON (non-blocking)
    stdin_data = {}
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            if raw.strip():
                stdin_data = json.loads(raw)
        except json.JSONDecodeError as e:
            print(json.dumps({
                "status": "error",
                "message": f"Invalid stdin JSON: {e}",
            }), file=sys.stderr)
        except IOError:
            pass

    # Merge CLI args over stdin data
    content_data = dict(stdin_data)

    if args.emotion:
        content_data["emotion"] = args.emotion
    if args.source:
        content_data["source"] = args.source
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
                raise ValueError(f"vad must be string 'V,A,D' or list [V,A,D], got {type(vad).__name__}")

            if len(parts) != 3:
                raise ValueError(f"vad requires exactly 3 values (V,A,D), got {len(parts)}")

            for i, v in enumerate(parts):
                if not (-1.0 <= v <= 1.0):
                    raise ValueError(f"vad[{i}] = {v} out of range [-1, 1]")

            emotion_vector = EmotionVector(*parts)
        except ValueError as e:
            print(json.dumps({
                "status": "error",
                "message": f"Invalid --vad: {e}",
            }))
            return
    elif emotion_name:
        emotion_name = emotion_name  # Will be passed to pipeline
    elif content.get("body"):
        # Infer from body text (fallback only)
        pass  # Pipeline handles text_to_emotion

    # === 3. Build vocabulary ===
    source = content.get("source")
    vocab_overrides = content.get("vocabulary", {})
    vocab = get_vocabulary(source, vocab_overrides)

    # Build content dict for pipeline
    pipeline_content = {
        "headline": content.get("headline"),
        "metrics": content.get("metrics", []),
        "timestamp": content.get("timestamp"),
        "body": content.get("body"),
        "source": source,
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

    pipe = FlexiblePipeline(seed=seed)

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

    # Validate overrides against known values
    errors = _validate_overrides(overrides)
    if errors:
        print(json.dumps({
            "status": "error",
            "message": "Invalid override values",
            "errors": errors,
        }))
        return

    results = []

    _variants = content["variants"]
    variant_count = _variants if isinstance(_variants, int) else int(_variants)
    is_video = bool(content["video"])
    _dur = content["duration"]
    duration = _dur if isinstance(_dur, float) else float(_dur)
    _fps = content["fps"]
    fps = _fps if isinstance(_fps, int) else int(_fps)

    body_text = str(content["body"]) if content.get("body") else None
    title_text = str(content["title"]) if content.get("title") else None

    for variant_idx in range(variant_count):
        variant_seed = seed + variant_idx

        if is_video:
            suffix = f"_v{variant_idx}" if variant_count > 1 else ""
            output_path = os.path.join(
                output_dir, f"viz_{timestamp_str}{suffix}.gif"
            )

            pipe.generate_video(
                text=body_text,
                emotion=emotion_name,
                emotion_vector=emotion_vector,
                seed=variant_seed,
                title=title_text,
                content=pipeline_content if content_has_data(pipeline_content) else None,
                duration=duration,
                fps=fps,
                output_path=output_path,
                overrides=overrides or None,
            )

            results.append({
                "path": os.path.abspath(output_path),
                "seed": variant_seed,
                "format": "gif",
                "duration": duration,
                "fps": fps,
            })

        else:
            suffix = f"_v{variant_idx}" if variant_count > 1 else ""
            output_path = os.path.join(
                output_dir, f"viz_{timestamp_str}{suffix}.png"
            )

            pipe.generate(
                text=body_text,
                emotion=emotion_name,
                emotion_vector=emotion_vector,
                seed=variant_seed,
                title=title_text,
                content=pipeline_content if content_has_data(pipeline_content) else None,
                output_path=output_path,
                overrides=overrides or None,
            )

            results.append({
                "path": os.path.abspath(output_path),
                "seed": variant_seed,
                "format": "png",
            })

    # === 6. Output JSON ===
    output = {
        "status": "ok",
        "results": results,
        "emotion": emotion_name,
        "source": source,
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
        from viz.lib.ascii_convert import image_to_ascii_art, add_market_overlay

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

    # Optional overlay from stdin
    overlay_data = {}
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            if raw.strip():
                overlay_data = json.loads(raw)
        except json.JSONDecodeError as e:
            print(json.dumps({
                "status": "error",
                "message": f"Invalid stdin JSON: {e}",
            }), file=sys.stderr)
        except IOError:
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
    from lib.vocabulary import VOCABULARIES

    capabilities = {
        "version": "2.0.0",
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
        "sources": sorted(VOCABULARIES.keys()),
        "blend_modes": ["ADD", "SCREEN", "OVERLAY", "MULTIPLY"],
        "layouts": ["random_scatter", "grid_jitter", "spiral", "force_directed", "preset"],
        "decorations": ["corners", "edges", "scattered", "minimal", "none", "frame", "grid_lines", "circuit"],
        "gradients": [
            "classic", "smooth", "matrix", "plasma", "default",
            "blocks", "blocks_fine", "blocks_ultra", "glitch",
            "box_density", "box_vertical", "box_cross", "circuit",
            "dots_density", "geometric", "braille_density",
            "tech", "cyber", "organic", "noise",
        ],
        "charsets_convert": ["classic", "simple", "blocks", "bull", "bear", "numbers", "money"],
        "input_schema": {
            "source": "string (market|art|news|mood) - determines visual vocabulary",
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
            "overlay": "dict {effect, blend, mix} - overlay effect config",
            "vocabulary": "dict - override default vocabulary fields",
            "video": "bool - output GIF instead of PNG",
            "duration": "float - GIF duration in seconds (default 3.0)",
            "fps": "int - frames per second (default 15)",
            "variants": "int - number of variants to generate",
            "title": "string - title overlay text",
        },
        "output_schema": {
            "status": "string (ok|error)",
            "results": "list[{path, seed, format, ...}] - always an array, even for single result",
            "emotion": "string|null - emotion used",
            "source": "string|null - source used",
        },
    }

    emotions_dict = capabilities["emotions"]
    effects_list = capabilities["effects"]
    sources_list = capabilities["sources"]
    layouts_list = capabilities["layouts"]
    decorations_list = capabilities["decorations"]

    format_type = args.format if hasattr(args, 'format') else "json"
    if format_type == "json":
        print(json.dumps(capabilities, ensure_ascii=False, indent=2))
    else:
        # Human-readable
        print("=== VIZ Capabilities ===\n")
        print(f"Emotions ({len(emotions_dict)}):")
        for name in sorted(emotions_dict):
            ev = emotions_dict[name]
            print(f"  {name:<15} V={ev['valence']:+.2f} A={ev['arousal']:+.2f} D={ev['dominance']:+.2f}")
        print(f"\nEffects ({len(effects_list)}): {', '.join(effects_list)}")
        print(f"Sources ({len(sources_list)}): {', '.join(sources_list)}")
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
    gen.add_argument("--source", choices=["market", "art", "news", "mood"],
                     help="信息来源 (决定视觉词汇)")
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
    gen.add_argument("--output-dir", help="输出目录")

    # === convert ===
    conv = subparsers.add_parser("convert", help="图像转 ASCII Convert image to ASCII")
    conv.add_argument("image", help="图像路径")
    conv.add_argument("--charset", help="字符集 (classic, blocks, bull, bear, ...)")
    conv.add_argument("--scale", type=float, help="缩放比例")
    conv.add_argument("--emotion", help="情绪 (bull, bear, neutral)")
    conv.add_argument("--output-dir", help="输出目录")

    # === capabilities ===
    cap = subparsers.add_parser("capabilities", help="列出所有可用选项")
    cap.add_argument("--format", choices=["json", "text"], default="json",
                     help="输出格式 (default: json)")

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
