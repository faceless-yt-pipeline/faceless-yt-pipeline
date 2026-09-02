"""Text-to-speech via ElevenLabs, returning audio + word-level timestamps.

Uses the "with-timestamps" endpoint so captions can be aligned to the audio
without a separate forced-alignment step. If ElevenLabs changes this API,
check https://elevenlabs.io/docs for the current request/response shape.
"""
import base64
import logging
import os
from pathlib import Path

import requests

import config

logger = logging.getLogger(__name__)

_API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"


def generate_voice(script: str, out_audio_path: Path) -> list[dict]:
    """Synthesize `script`, write mp3 to out_audio_path, return word-level timestamps.

    Each returned item: {"word": str, "start": float, "end": float} (seconds).
    """
    response = requests.post(
        _API_URL.format(voice_id=config.ELEVENLABS_VOICE_ID),
        headers={
            "xi-api-key": os.environ["ELEVENLABS_API_KEY"],
            "Content-Type": "application/json",
        },
        json={
            "text": script,
            "model_id": config.ELEVENLABS_MODEL_ID,
            "voice_settings": {
                "stability": config.ELEVENLABS_STABILITY,
                "similarity_boost": config.ELEVENLABS_SIMILARITY_BOOST,
            },
        },
        timeout=180,
    )
    response.raise_for_status()
    payload = response.json()

    audio_bytes = base64.b64decode(payload["audio_base64"])
    out_audio_path.parent.mkdir(parents=True, exist_ok=True)
    out_audio_path.write_bytes(audio_bytes)
    logger.info("Wrote voiceover audio to %s (%d bytes)", out_audio_path, len(audio_bytes))

    return _words_from_alignment(payload["alignment"])


def _words_from_alignment(alignment: dict) -> list[dict]:
    """Group ElevenLabs character-level alignment into word-level timestamps."""
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]

    words = []
    current = ""
    word_start = None
    word_end = None
    for ch, start, end in zip(chars, starts, ends):
        if ch.isspace():
            if current:
                words.append({"word": current, "start": word_start, "end": word_end})
                current = ""
                word_start = None
            continue
        if current == "":
            word_start = start
        current += ch
        word_end = end
    if current:
        words.append({"word": current, "start": word_start, "end": word_end})
    return words
