"""Compose the final vertical video: background loop + voiceover + burned-in captions."""
import logging
import random
import subprocess
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def _audio_duration(audio_path: Path) -> float:
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


def render_video(audio_path: Path, captions_path: Path, out_video_path: Path) -> None:
    duration = _audio_duration(audio_path)
    background = _pick_background()
    out_video_path.parent.mkdir(parents=True, exist_ok=True)

    # ffmpeg's filtergraph parser treats ':' and '\' specially inside filter args,
    # so escape paths before splicing them into -vf. fontsdir must be passed
    # explicitly — libass doesn't pick up assets/fonts/*.ttf on its own and will
    # silently fall back to a system font otherwise.
    def _escape(path: Path) -> str:
        return str(path).replace("\\", "/").replace(":", "\\:")

    ass_filter_path = _escape(captions_path)
    fontsdir = _escape(config.CAPTION_FONT.parent)
    vf = (
        f"scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT},"
        f"ass='{ass_filter_path}':fontsdir='{fontsdir}'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", str(background),
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
