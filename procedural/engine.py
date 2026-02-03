"""
程序化生成引擎 - Procedural Generation Engine

核心编排器，协调效果层、精灵层和渲染管线，生成动画帧序列并输出 GIF/MP4。

渲染流程::

    1. Effect 层:
       context = Context(...)
       buffer = init_buffer()
       state = effect.pre(context, buffer)
       for y, x: buffer[y][x] = effect.main(x, y, context, state)
       effect.post(context, buffer, state)

    2. Buffer → Image:
       img_low = buffer_to_image(buffer)

    3. Sprite 层:
       for sprite in sprites: sprite.render(img_low, time)

    4. 上采样:
       img_high = upscale_image(img_low, output_size)

    5. 后处理:
       sharpen + contrast enhancement

用法示例::

    from procedural.engine import Engine
    from procedural.effects import get_effect
    from procedural.layers import TextSprite

    engine = Engine(internal_size=(160, 160), output_size=(1080, 1080))
    effect = get_effect('plasma')
    sprites = [TextSprite('HELLO', x=80, y=80, color='#00ff00')]

    # 渲染单帧
    frame = engine.render_frame(effect, sprites, time=0.0, frame=0, seed=42)
    frame.save('single_frame.png')

    # 渲染动画并保存 GIF
    frames = engine.render_video(effect, duration=3.0, fps=15, sprites=sprites, seed=42)
    engine.save_gif(frames, '/workspace/media/output.gif', fps=15)

    # 保存 MP4 (需要系统安装 FFmpeg)
    engine.save_mp4(frames, '/workspace/media/output.mp4', fps=15)
"""

import random
import time as _time

from PIL import ImageEnhance, ImageFilter

from .types import Context, Cell, Buffer
from .renderer import buffer_to_image, upscale_image

__all__ = [
    "Engine",
]


class Engine:
    """
    程序化生成引擎 - Procedural Generation Engine

    协调效果渲染、精灵叠加、图像后处理的完整管线。
    支持单帧渲染、多帧序列生成和 GIF 输出。

    属性:
        internal_size: 内部渲染分辨率 (width, height)，如 (160, 160)
        output_size: 最终输出分辨率 (width, height)，如 (1080, 1080)
        char_size: 每个字符单元的像素尺寸 (默认 1，即 1:1 映射)
        gradient_name: ASCII 梯度名称 (传递给 buffer_to_image)
        color_scheme: 颜色方案 (传递给 buffer_to_image)
        sharpen: 是否应用锐化后处理 (默认 True)
        contrast: 对比度增强系数 (默认 1.2，1.0 = 不增强)

    示例::

        engine = Engine(
            internal_size=(160, 160),
            output_size=(1080, 1080),
            sharpen=True,
            contrast=1.4,
        )
    """

    def __init__(
        self,
        internal_size=(160, 160),
        output_size=(1080, 1080),
        char_size=1,
        gradient_name="default",
        color_scheme="heat",
        sharpen=True,
        contrast=1.2,
    ):
        self.internal_size = internal_size
        self.output_size = output_size
        self.char_size = char_size
        self.gradient_name = gradient_name
        self.color_scheme = color_scheme
        self.sharpen = sharpen
        self.contrast = contrast

    def _init_buffer(self, width, height):
        """
        创建空白缓冲区 - Initialize Empty Buffer

        创建 height x width 的 2D Cell 数组，所有单元初始化为
        黑色空格 (char_idx=0, fg=black, bg=None)。

        Args:
            width: 缓冲区宽度
            height: 缓冲区高度

        Returns:
            Buffer (list[list[Cell]])
        """
        return [
            [Cell(char_idx=0, fg=(0, 0, 0), bg=None) for _ in range(width)]
            for _ in range(height)
        ]

    def _postprocess(self, image):
        """
        后处理 - Apply Post-Processing Effects

        可选地应用锐化和对比度增强。

        Args:
            image: PIL Image 对象

        Returns:
            处理后的 PIL Image
        """
        if self.sharpen:
            image = image.filter(ImageFilter.SHARPEN)

        if self.contrast != 1.0:
            image = ImageEnhance.Contrast(image).enhance(self.contrast)

        return image

    def render_frame(
        self,
        effect,
        sprites=None,
        time=0.0,
        frame=0,
        seed=42,
        params=None,
    ):
        """
        渲染单帧 - Render Single Frame

        完整的单帧渲染流程:
        1. 创建 Context 和 Buffer
        2. 调用 effect.pre() 预处理
        3. 逐像素调用 effect.main() 填充 Buffer
        4. 调用 effect.post() 后处理
        5. Buffer → 低分辨率图像
        6. 渲染 sprites 到图像
        7. 上采样到最终分辨率
        8. 应用后处理 (sharpen + contrast)

        Args:
            effect: 效果实例 (实现 Effect Protocol: pre/main/post)
            sprites: 精灵列表 (Sprite 实例，可选)
            time: 当前时间 (秒)
            frame: 当前帧号
            seed: 随机种子
            params: 效果参数字典 (可选)

        Returns:
            PIL Image - 渲染完成的帧图像 (output_size 分辨率)

        示例::

            from procedural.effects import get_effect
            engine = Engine()
            effect = get_effect('plasma')
            img = engine.render_frame(effect, time=1.5, frame=45, seed=42)
            img.save('frame.png')
        """
        if sprites is None:
            sprites = []
        if params is None:
            params = {}

        w, h = self.internal_size

        # 1. 创建渲染上下文
        rng = random.Random(seed)
        ctx = Context(
            width=w,
            height=h,
            time=time,
            frame=frame,
            seed=seed,
            rng=rng,
            params=params,
        )

        # 2. 初始化缓冲区
        buffer = self._init_buffer(w, h)

        # 3. 预处理阶段
        state = effect.pre(ctx, buffer)
        if state is None:
            state = {}

        # 4. 主渲染 - 逐像素填充 buffer
        for y in range(h):
            for x in range(w):
                cell = effect.main(x, y, ctx, state)
                if cell is not None:
                    buffer[y][x] = cell

        # 5. 后处理阶段
        effect.post(ctx, buffer, state)

        # 6. Buffer → 低分辨率图像
        img = buffer_to_image(
            buffer,
            char_size=self.char_size,
            gradient_name=self.gradient_name,
            color_scheme=self.color_scheme,
        )

        # 7. 上采样到输出分辨率 (精灵坐标在输出空间，必须先上采样)
        img = upscale_image(img, self.output_size)

        # 8. 渲染精灵层到输出分辨率图像
        for sprite in sprites:
            sprite.render(img, time=time)

        # 9. 后处理 (sharpen + contrast)
        img = self._postprocess(img)

        return img

    def render_video(
        self,
        effect,
        duration=3.0,
        fps=15,
        sprites=None,
        seed=42,
        params=None,
    ):
        """
        渲染多帧序列 - Render Video Frame Sequence

        按指定时长和帧率生成连续帧序列。
        每帧以 frame/fps 计算时间，保证动画连续性。

        Args:
            effect: 效果实例 (实现 Effect Protocol)
            duration: 动画时长 (秒，默认 3.0)
            fps: 帧率 (默认 15)
            sprites: 精灵列表 (可选)
            seed: 随机种子 (所有帧使用相同种子)
            params: 效果参数字典 (可选)

        Returns:
            list[PIL.Image] - 帧图像列表

        示例::

            engine = Engine()
            effect = get_effect('plasma')
            frames = engine.render_video(effect, duration=2.0, fps=15, seed=42)
            engine.save_gif(frames, '/workspace/media/plasma.gif')
        """
        if sprites is None:
            sprites = []
        if params is None:
            params = {}

        total_frames = int(duration * fps)
        frames = []

        print(f"渲染 {total_frames} 帧 ({duration}s @ {fps}fps)...")
        start_time = _time.time()

        for i in range(total_frames):
            t = i / fps
            frame_img = self.render_frame(
                effect=effect,
                sprites=sprites,
                time=t,
                frame=i,
                seed=seed,
                params=params,
            )
            frames.append(frame_img)

            # 进度打印 (每 30 帧)
            if (i + 1) % 30 == 0 or (i + 1) == total_frames:
                elapsed = _time.time() - start_time
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                print(
                    f"  进度: {i + 1}/{total_frames} 帧 ({elapsed:.1f}s, {rate:.1f} fps)"
                )

        elapsed = _time.time() - start_time
        print(
            f"渲染完成: {total_frames} 帧, {elapsed:.1f}s ({total_frames / elapsed:.1f} fps)"
        )

        return frames

    @staticmethod
    def save_gif(frames, output_path, fps=15):
        """
        保存为 GIF - Save Frames as GIF

        使用 Pillow 将帧列表保存为循环 GIF 动画。

        Args:
            frames: PIL Image 列表 (至少 1 帧)
            output_path: 输出文件路径 (如 '/workspace/media/output.gif')
            fps: GIF 帧率 (默认 15)

        Raises:
            ValueError: 如果 frames 为空

        示例::

            Engine.save_gif(frames, '/workspace/media/animation.gif', fps=15)
        """
        if not frames:
            raise ValueError("frames 列表为空，无法保存 GIF")

        duration_ms = int(1000 / fps)

        print(f"保存 GIF: {output_path} ({len(frames)} 帧, {fps}fps)")

        if len(frames) == 1:
            frames[0].save(output_path, "GIF", optimize=True)
        else:
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=duration_ms,
                loop=0,
                optimize=True,
            )

        print(f"GIF 保存完成: {output_path}")

    @staticmethod
    def save_mp4(frames, output_path, fps=15):
        """
        保存为 MP4 - Save Frames as MP4 via FFmpeg subprocess

        先将帧保存为临时 GIF，再用 FFmpeg 转换为 MP4。
        如果 FFmpeg 未安装，静默返回 False（优雅降级）。

        Args:
            frames: PIL Image 列表 (至少 1 帧)
            output_path: 输出文件路径 (如 '/workspace/media/output.mp4')
            fps: 视频帧率 (默认 15)

        Returns:
            bool: True 如果成功, False 如果 FFmpeg 不可用或转换失败

        示例::

            success = Engine.save_mp4(frames, '/workspace/media/animation.mp4', fps=15)
            if not success:
                print("FFmpeg not available, MP4 skipped")
        """
        import os
        import subprocess
        import tempfile

        if not frames:
            return False

        gif_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
                gif_path = tmp.name

            Engine.save_gif(frames, gif_path, fps=fps)

            print(f"转换 MP4: {output_path}")
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    gif_path,
                    "-movflags",
                    "faststart",
                    "-pix_fmt",
                    "yuv420p",
                    "-vf",
                    f"fps={fps},scale=1080:1080:flags=neighbor",
                    output_path,
                ],
                check=True,
                capture_output=True,
            )
            print(f"MP4 保存完成: {output_path}")
            return True

        except FileNotFoundError:
            print("FFmpeg 未安装，跳过 MP4 输出")
            return False
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg 转换失败: {e.stderr.decode() if e.stderr else str(e)}")
            return False
        finally:
            if gif_path and os.path.exists(gif_path):
                os.remove(gif_path)
