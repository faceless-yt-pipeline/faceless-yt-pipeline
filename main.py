"""Faceless YouTube pipeline: Reddit story -> script -> voiceover -> captions -> video -> thumbnail -> upload."""
import argparse
import json
import logging
import sys
import time

from dotenv import load_dotenv

import config
from scripts import (
    fetch_reddit,
    generate_captions,
    generate_script,
    generate_thumbnail,
    render_video,
    upload_video,
)
from scripts.generate_voice import generate_voice

load_dotenv()


def _setup_logging() -> None:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.LOG_DIR / "pipeline.log", encoding="utf-8"),
        ],
    )


def run(mode: str) -> None:
    logger = logging.getLogger("main")
    run_id = time.strftime("%Y%m%d-%H%M%S")
    run_dir = config.OUTPUT_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== Run %s (mode=%s) ===", run_id, mode)

    story = fetch_reddit.fetch_story()
    (run_dir / "source.json").write_text(json.dumps(story, indent=2), encoding="utf-8")

    script = generate_script.generate_script(story)
    (run_dir / "script.txt").write_text(script, encoding="utf-8")

    if mode == "review":
        logger.info(
            "Review mode: stopping after script generation. Edit %s and rerun the "
            "remaining stages by hand once you're happy with it.", run_dir / "script.txt",
        )
        return

    audio_path = run_dir / "voice.mp3"
    words = generate_voice(script, audio_path)

    if mode == "dry-run":
        logger.info("Dry-run mode: stopping after voiceover. Output in %s", run_dir)
        return

    captions_path = run_dir / "captions.ass"
    generate_captions.build_captions(words, captions_path)

    video_path = run_dir / "video.mp4"
    render_video.render_video(audio_path, captions_path, video_path)

    thumbnail_path = run_dir / "thumbnail.png"
    generate_thumbnail.generate_thumbnail(story["title"], thumbnail_path)

    description = (
        f"{' '.join(script.split()[:80])}...\n\n"
        f"Story adapted from r/{story['subreddit']}. Original post: {story['url']}"
    )
    video_id = upload_video.upload_video(video_path, thumbnail_path, story["title"][:100], description)
    logger.info("Done. https://youtu.be/%s (privacyStatus=%s)", video_id, config.YT_PRIVACY_STATUS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Faceless YouTube storytelling pipeline")
    parser.add_argument("--mode", choices=["full", "review", "dry-run"], default="full")
    args = parser.parse_args()

    _setup_logging()
    run(args.mode)


if __name__ == "__main__":
    main()
