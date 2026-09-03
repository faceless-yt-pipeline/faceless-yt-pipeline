"""Text-to-speech via edge-tts (free, no API key), returning audio + word-level timestamps.

edge-tts wraps Microsoft Edge's online neural "Read Aloud" voices. It's unofficial —
not a supported public API with an SLA — but free and widely used for this purpose.
If Microsoft ever changes that service in a breaking way, this module is the one
place that would need to change.
"""
import asyncio
import logging
from pathlib import Path

import edge_tts

import config

logger = logging.getLogger(__name__)

_TICKS_PER_SECOND = 10_000_000  # edge-tts reports offsets/durations in 100-nanosecond units


def generate_voice(script: str, out_audio_path: Path) -> list[dict]:
    """Synthesize `script`, write mp3 to out_audio_path, return word-level timestamps.

    Each returned item: {"word": str, "start": float, "end": float} (seconds).
    """
    return asyncio.run(_synthesize(script, out_audio_path))


async def _synthesize(script: str, out_audio_path: Path) -> list[dict]:
    communicate = edge_tts.Communicate(
        script, config.EDGE_TTS_VOICE, rate=config.EDGE_TTS_RATE, boundary="WordBoundary",
    )
    out_audio_path.parent.mkdir(parents=True, exist_ok=True)

    words = []
    with open(out_audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / _TICKS_PER_SECOND
                end = start + chunk["duration"] / _TICKS_PER_SECOND
                words.append({"word": chunk["text"], "start": start, "end": end})

    if not words:
        raise RuntimeError("edge-tts returned no word-boundary timing data — cannot build captions.")

    logger.info("Wrote voiceover audio to %s (%d words)", out_audio_path, len(words))
    return words
