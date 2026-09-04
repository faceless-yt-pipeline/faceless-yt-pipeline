"""Build a Shorts-length teaser by re-synthesizing the opening sentences of the story.

Rather than cutting the full voiceover audio at a computed timestamp — which would
require reconstructing sentence boundaries from edge-tts's word-boundary events,
whose "word" text has all punctuation stripped out — this takes a text-level prefix
of the script (the longest run of complete sentences fitting config.SHORTS_MAX_SECONDS
at the configured words-per-minute rate) and re-runs TTS on just that. It costs one
extra free TTS call but guarantees a clean sentence-complete cut with its own
correctly-synced word timestamps.
"""
import logging
import re
from pathlib import Path

import config
from scripts import generate_captions
from scripts.generate_voice import generate_voice

logger = logging.getLogger(__name__)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _teaser_text(script: str) -> str:
    sentences = _SENTENCE_SPLIT.split(script.strip())
    max_words = int(config.SHORTS_MAX_SECONDS / 60 * config.TARGET_WORDS_PER_MINUTE)

    chosen = []
    word_count = 0
    for sentence in sentences:
        sentence_words = len(sentence.split())
        if chosen and word_count + sentence_words > max_words:
            break
        chosen.append(sentence)
        word_count += sentence_words
    return " ".join(chosen)


def build_shorts_assets(script: str, out_dir: Path) -> tuple[Path, Path, float]:
    """Synthesize + caption a Shorts-length teaser from the start of `script`.

    Returns (short_audio_path, short_captions_path, duration_seconds).
    """
    teaser = _teaser_text(script)

    short_audio_path = out_dir / "shorts_voice.mp3"
    words = generate_voice(teaser, short_audio_path)

    short_captions_path = out_dir / "shorts_captions.ass"
    generate_captions.build_captions(words, short_captions_path)

    duration = words[-1]["end"] if words else 0.0
    logger.info("Built Shorts teaser: %d words, ~%.1fs", len(words), duration)
    return short_audio_path, short_captions_path, duration
