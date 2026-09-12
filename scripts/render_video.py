"""Compose the final vertical video: background (stock loop or AI scene images) + voiceover + burned-in captions."""
import logging
import random
import subprocess
import tempfile
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def audio_duration(audio_path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def _pick_background() -> Path:
    clips = sorted(config.BACKGROUND_DIR.glob("*.mp4"))
    if not clips:
        raise RuntimeError(f"No background clips found in {config.BACKGROUND_DIR}. Add .mp4 files there.")
    return random.choice(clips)


# ffmpeg's filtergraph parser treats ':' and '\' specially inside filter args,
# so escape paths before splicing them into -vf. fontsdir must be passed
# explicitly — libass doesn't pick up assets/fonts/*.ttf on its own and will
# silently fall back to a system font otherwise.
def _escape(path: Path) -> str:
    return str(path).replace("\\", "/").replace(":", "\\:")


def _render_scene_clip(image_path: Path, duration: float, out_path: Path) -> None:
    """Ken Burns: a slow zoom-in over the scene's duration, scaled/cropped to the output frame."""
    frames = max(int(round(duration * config.VIDEO_FPS)), 1)
    zoom_step = (config.SCENE_ZOOM_MAX - 1.0) / frames
    # zoompan needs the source upscaled first for smooth (non-jumpy) sampling while it zooms,
    # but the source images are only ~576px wide and the final output caps at VIDEO_WIDTH —
    # upscaling much beyond that wastes CPU for no visible benefit. This clip is also just an
    # intermediate (render_video() re-encodes the concatenated background again), so a faster
    # preset here doesn't cost final quality.
    upscale_width = config.VIDEO_WIDTH * 3
    vf = (
        f"scale={upscale_width}:-2,"
        f"zoompan=z='min(zoom+{zoom_step:.6f},{config.SCENE_ZOOM_MAX})':"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}:fps={config.VIDEO_FPS}"
    )
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(image_path),
        "-vf", vf, "-t", f"{duration:.3f}", "-r", str(config.VIDEO_FPS),
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "veryfast",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)


def _build_scene_background(scene_images: list[tuple[Path, float]], tmp_dir: Path) -> Path:
    clip_paths = []
    for i, (image_path, duration) in enumerate(scene_images):
        clip_path = tmp_dir / f"scene_clip_{i:03d}.mp4"
        _render_scene_clip(image_path, duration, clip_path)
        clip_paths.append(clip_path)

    # The concat demuxer's list format has its own (simpler) escaping rules — unlike
    # -vf filtergraph args, ':' is not special here, so _escape() (built for -vf) is wrong.
    concat_lines = [f"file '{str(p).replace('\\', '/')}'" for p in clip_paths]
    concat_list = tmp_dir / "concat_list.txt"
    concat_list.write_text("\n".join(concat_lines), encoding="utf-8")

    background = tmp_dir / "background.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(background)],
        check=True,
    )
    return background


def render_video(
    audio_path: Path,
    captions_path: Path,
    out_video_path: Path,
    scene_images: list[tuple[Path, float]] | None = None,
) -> None:
    duration = audio_duration(audio_path)
    out_video_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=out_video_path.parent) as tmp:
        if scene_images:
            background = _build_scene_background(scene_images, Path(tmp))
            input_args = ["-i", str(background)]
        else:
            input_args = ["-stream_loop", "-1", "-i", str(_pick_background())]

        ass_filter_path = _escape(captions_path)
        fontsdir = _escape(config.CAPTION_FONT.parent)
        vf = (
            f"scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT},"
            f"ass='{ass_filter_path}':fontsdir='{fontsdir}'"
        )

        cmd = [
            "ffmpeg", "-y",
            *input_args,
            "-i", str(audio_path),
            "-map", "0:v:0", "-map", "1:a:0",
            "-vf", vf,
            "-r", str(config.VIDEO_FPS),
            "-t", f"{duration:.3f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(out_video_path),
        ]
        logger.info("Rendering video: %s", " ".join(cmd))
        subprocess.run(cmd, check=True)
    logger.info("Wrote video to %s", out_video_path)
