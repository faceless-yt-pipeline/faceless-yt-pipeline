"""Build several Shorts-length teasers, each from a different part of the story.

Rather than cutting the full voiceover audio at a computed timestamp — which would
require reconstructing sentence boundaries from edge-tts's word-boundary events,
whose "word" text has all punctuation stripped out — this takes text-level excerpts
of the script (the longest run of complete sentences from each of config.SHORTS_PER_VIDEO
evenly-spaced starting points that fits config.SHORTS_MAX_SECONDS at the configured
words-per-minute rate) and re-runs TTS on each. It costs extra free TTS calls but
guarantees clean sentence-complete cuts with their own correctly-synced timestamps.
"""
import logging
import re
from pathlib import Path

import config
from scripts import generate_captions
from scripts.generate_voice import generate_voice

logger = logging.getLogger(__name__)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _segment_text(sentences: list[str], start_idx: int) -> str:
    """Longest run of complete sentences from start_idx that fits the Shorts word budget."""
    max_words = int(config.SHORTS_MAX_SECONDS / 60 * config.TARGET_WORDS_PER_MINUTE)
    chosen = []
    word_count = 0
    for sentence in sentences[start_idx:]:
        sentence_words = len(sentence.split())
        if chosen and word_count + sentence_words > max_words:
            break
        chosen.append(sentence)
        word_count += sentence_words
    return " ".join(chosen)


def _segment_starts(sentences: list[str], count: int) -> list[int]:
    """Evenly-spaced sentence indices (by cumulative word position) to start each segment from."""
    word_counts = [len(s.split()) for s in sentences]
    total_words = sum(word_counts)
    if count <= 1 or total_words == 0:
        return [0]

    targets = [round(total_words * i / count) for i in range(count)]
    starts, cumulative, t = [], 0, 0
    for i, wc in enumerate(word_counts):
        while t < len(targets) and cumulative >= targets[t]:
            starts.append(i)
            t += 1
        cumulative += wc
    while len(starts) < count:
        starts.append(starts[-1] if starts else 0)

    seen, unique = set(), []
    for idx in starts:
        if idx not in seen:
            seen.add(idx)
            unique.append(idx)
    return unique or [0]


def build_shorts(script: str, out_dir: Path) -> list[tuple[Path, Path, float]]:
    """Build config.SHORTS_PER_VIDEO teasers spread across the story.

    Returns a list of (short_audio_path, short_captions_path, duration_seconds),
    one per teaser, in story order. Short stories may yield fewer than
    SHORTS_PER_VIDEO if there isn't room for that many distinct starting points.
    """
    sentences = _SENTENCE_SPLIT.split(script.strip())
    starts = _segment_starts(sentences, config.SHORTS_PER_VIDEO)

    results = []
    for i, start_idx in enumerate(starts, start=1):
        teaser = _segment_text(sentences, start_idx)

        audio_path = out_dir / f"shorts_voice_{i}.mp3"
        words = generate_voice(teaser, audio_path)

        captions_path = out_dir / f"shorts_captions_{i}.ass"
        generate_captions.build_captions(words, captions_path)

        duration = words[-1]["end"] if words else 0.0
        logger.info("Built Shorts teaser %d/%d: %d words, ~%.1fs", i, len(starts), len(words), duration)
        results.append((audio_path, captions_path, duration))

    return results
