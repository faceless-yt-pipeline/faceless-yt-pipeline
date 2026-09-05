"""Faceless YouTube pipeline: Reddit story -> script -> voiceover -> captions -> video -> thumbnail -> upload."""
import argparse
import json
import logging
import sys
import time

from dotenv import load_dotenv

import config
from scripts import (
    generate_captions,
    generate_shorts,
    generate_story,
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

    story = generate_story.generate_story()
    (run_dir / "story.json").write_text(json.dumps(story, indent=2), encoding="utf-8")

    script = story["script"]
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
        "This is an original story, written for this channel.\n\n"
        + " ".join(config.VIDEO_HASHTAGS)
    )
    video_id = upload_video.upload_video(
        video_path, story["title"][:100], description, thumbnail_path=thumbnail_path,
    )
    logger.info("Uploaded full video: https://youtu.be/%s (privacyStatus=%s)", video_id, config.YT_PRIVACY_STATUS)

    if config.SHORTS_ENABLED:
        shorts = generate_shorts.build_shorts(script, run_dir)
        for i, (short_audio_path, short_captions_path, short_seconds) in enumerate(shorts, start=1):
            short_video_path = run_dir / f"shorts_video_{i}.mp4"
            render_video.render_video(short_audio_path, short_captions_path, short_video_path)

            part_suffix = f" (Part {i}/{len(shorts)})" if len(shorts) > 1 else ""
            short_title = f"{story['title'][:80]}{part_suffix} #Shorts"
            short_description = (
                f"Full story: https://youtu.be/{video_id}\n\n"
                + " ".join(config.SHORTS_HASHTAGS)
            )
            short_id = upload_video.upload_video(
                short_video_path, short_title, short_description, tags=config.SHORTS_DEFAULT_TAGS,
            )
            logger.info(
                "Uploaded Shorts teaser %d/%d (%.0fs): https://youtu.be/%s (privacyStatus=%s)",
                i, len(shorts), short_seconds, short_id, config.YT_PRIVACY_STATUS,
            )

    logger.info("Done. https://youtu.be/%s (privacyStatus=%s)", video_id, config.YT_PRIVACY_STATUS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Faceless YouTube storytelling pipeline")
    parser.add_argument("--mode", choices=["full", "review", "dry-run"], default="full")
    args = parser.parse_args()

    _setup_logging()
    run(args.mode)


if __name__ == "__main__":
    main()
