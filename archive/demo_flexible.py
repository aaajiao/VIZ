#!/usr/bin/env python3
"""
Flexible Output System 演示 - Demo Script

展示千变万化的输出系统如何从同一输入产生不同的视觉结果。

用法::

    # 基础演示: 从文本生成
    python3 viz/demo_flexible.py

    # 指定情绪
    python3 viz/demo_flexible.py --emotion euphoria

    # 从文本推断
    python3 viz/demo_flexible.py --text "市场暴跌 恐慌蔓延"

    # 生成多个变体
    python3 viz/demo_flexible.py --text "hope" --variants 5

    # 生成动画
    python3 viz/demo_flexible.py --emotion joy --video --duration 3

    # 指定 VAD 向量
    python3 viz/demo_flexible.py --vad 0.5,-0.3,0.2

    # 使用 CPPN 效果
    python3 viz/demo_flexible.py --emotion calm --seed 42
"""

import argparse
import os
import sys
import time

# 确保 viz 在路径中
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from procedural.flexible import (
    FlexiblePipeline,
    EmotionVector,
    text_to_emotion,
    VAD_ANCHORS,
)


def main():
    parser = argparse.ArgumentParser(
        description="Flexible Output System 演示 - 千变万化的可视化生成"
    )
    parser.add_argument("--text", type=str, help="输入文本 (自动推断情绪)")
    parser.add_argument("--emotion", type=str, help="情绪名称 (如 joy, fear, euphoria)")
    parser.add_argument("--vad", type=str, help="VAD 向量 (如 0.5,-0.3,0.2)")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    parser.add_argument("--variants", type=int, default=1, help="生成变体数量")
    parser.add_argument("--video", action="store_true", help="生成 GIF 动画")
    parser.add_argument("--duration", type=float, default=3.0, help="动画时长 (秒)")
    parser.add_argument("--fps", type=int, default=15, help="动画帧率")
    parser.add_argument("--title", type=str, help="标题文字")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="输出目录 (默认 ./media)")
    parser.add_argument("--list-emotions", action="store_true",
                        help="列出所有预定义情绪")
    parser.add_argument("--analyze", action="store_true",
                        help="分析文本的 VAD 向量 (不生成图片)")

    args = parser.parse_args()

    # 列出情绪
    if args.list_emotions:
        print("=== 预定义情绪 (VAD 锚点) ===\n")
        print(f"{'名称':<15} {'效价(V)':>8} {'唤醒(A)':>8} {'支配(D)':>8}")
        print("-" * 45)
        for name, ev in sorted(VAD_ANCHORS.items()):
            print(f"{name:<15} {ev.valence:>+8.2f} {ev.arousal:>+8.2f} {ev.dominance:>+8.2f}")
        return

    # 分析文本
    if args.analyze:
        if not args.text:
            print("错误: --analyze 需要 --text 参数")
            return
        ev = text_to_emotion(args.text)
        params = ev.to_visual_params()
        print(f"文本: {args.text}")
        print(f"\nVAD 向量:")
        print(f"  Valence (效价):   {ev.valence:+.3f}")
        print(f"  Arousal (唤醒度): {ev.arousal:+.3f}")
        print(f"  Dominance (支配): {ev.dominance:+.3f}")
        print(f"  Magnitude (强度): {ev.magnitude():.3f}")
        print(f"\n视觉参数:")
        for k, v in sorted(params.items()):
            if isinstance(v, float):
                print(f"  {k:<20} {v:>8.3f}")
            else:
                print(f"  {k:<20} {v!s:>8}")
        return

    # 确定输出目录
    output_dir = args.output_dir or os.path.join(script_dir, "media")
    os.makedirs(output_dir, exist_ok=True)

    # 解析 VAD 向量
    emotion_vector = None
    if args.vad:
        parts = [float(x) for x in args.vad.split(",")]
        if len(parts) != 3:
            print("错误: --vad 需要 3 个值 (valence,arousal,dominance)")
            return
        emotion_vector = EmotionVector(*parts)

    # 确定标题
    title = args.title
    if title is None:
        if args.emotion:
            title = args.emotion.upper()
        elif args.text:
            title = args.text[:20]

    # 创建管线
    pipe = FlexiblePipeline(seed=args.seed)

    # 显示输入信息
    if args.text:
        ev = text_to_emotion(args.text)
        print(f"输入文本: {args.text}")
        print(f"推断 VAD: V={ev.valence:+.2f} A={ev.arousal:+.2f} D={ev.dominance:+.2f}")
    elif args.emotion:
        ev = VAD_ANCHORS.get(args.emotion.lower())
        if ev:
            print(f"情绪: {args.emotion}")
            print(f"VAD: V={ev.valence:+.2f} A={ev.arousal:+.2f} D={ev.dominance:+.2f}")
        else:
            print(f"未知情绪: {args.emotion}, 使用 neutral")
    elif emotion_vector:
        print(f"VAD: V={emotion_vector.valence:+.2f} A={emotion_vector.arousal:+.2f} D={emotion_vector.dominance:+.2f}")
    else:
        print("未指定输入，使用 neutral")

    # 生成
    start = time.time()

    if args.video:
        # 生成动画
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"flexible_{timestamp}.gif")

        print(f"\n生成 GIF ({args.duration}s @ {args.fps}fps)...")
        pipe.generate_video(
            text=args.text,
            emotion=args.emotion,
            emotion_vector=emotion_vector,
            seed=args.seed,
            title=title,
            duration=args.duration,
            fps=args.fps,
            output_path=output_path,
        )
        elapsed = time.time() - start
        print(f"完成: {output_path} ({elapsed:.1f}s)")

    elif args.variants > 1:
        # 生成多个变体
        print(f"\n生成 {args.variants} 个变体...")
        base_seed = args.seed if args.seed is not None else 42
        for i in range(args.variants):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                output_dir, f"flexible_{timestamp}_v{i}.png"
            )
            img = pipe.generate(
                text=args.text,
                emotion=args.emotion,
                emotion_vector=emotion_vector,
                seed=base_seed + i,
                title=title,
                output_path=output_path,
            )
            print(f"  变体 {i}: {output_path}")

        elapsed = time.time() - start
        print(f"完成: {args.variants} 个变体 ({elapsed:.1f}s)")

    else:
        # 生成单帧
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"flexible_{timestamp}.png")

        print(f"\n生成单帧...")
        img = pipe.generate(
            text=args.text,
            emotion=args.emotion,
            emotion_vector=emotion_vector,
            seed=args.seed,
            title=title,
            output_path=output_path,
        )
        elapsed = time.time() - start
        print(f"完成: {output_path} ({elapsed:.1f}s)")


if __name__ == "__main__":
    main()
