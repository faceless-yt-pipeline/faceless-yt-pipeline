"""Generate AI still images per story scene, for a Ken Burns pan/zoom background.

Replaces the stock background-clip loop with images that actually match the story,
generated via fal.ai's hosted FLUX.1 [schnell] model (https://fal.ai). Scene boundaries
are chosen deterministically in Python (evenly-sized word-count groups, same pattern as
scripts/generate_shorts.py) rather than asked of the model — asking Claude to both pick
scene boundaries AND hit an exact count reliably under-delivered (a 5s-per-scene target
that should yield ~42 scenes for a 3.5min story instead produced 26 uneven ones, some
over 20s), so the model's only job here is writing a good image prompt per pre-defined
scene, which it does reliably.
"""
import json
import logging
import os
import re
from pathlib import Path

import anthropic
import requests

import config

logger = logging.getLogger(__name__)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

_IMAGE_PROMPT_SYSTEM = (
    "You are writing image-generation prompts for pre-defined scenes from a narration script, "
    "to be shown as still images behind the narration with a slow pan/zoom.\n\n"
    "For each scene's text below, write a vivid, concrete image-generation prompt describing "
    "the setting, mood, lighting, and any characters — visually specific enough for a "
    "text-to-image model, and consistent in style across scenes (photorealistic, cinematic). "
    "Never include text, letters, or words in the image description. Text-to-image models "
    "render readable text as garbled nonsense, so also avoid describing anything a viewer "
    "would expect to read: shop signs, labels, book/magazine covers, screens, newspapers, "
    "storefronts with signage. If a setting would naturally have one, either frame the shot "
    "to exclude it or describe it as blurred, out of focus, or turned away from camera.\n\n"
    "Respond with ONLY a JSON array of exactly {count} strings (the image prompts), in the "
    "same order as the scenes given, nothing else."
)


def _target_scene_count(total_duration: float) -> int:
    """Roughly one scene per SCENE_SECONDS_TARGET seconds, clamped to [MIN_COUNT, MAX_COUNT]."""
    if not total_duration:
        return config.SCENE_MIN_COUNT
    target = round(total_duration / config.SCENE_SECONDS_TARGET)
    return max(config.SCENE_MIN_COUNT, min(target, config.SCENE_MAX_COUNT))


def _split_into_scene_texts(script: str, target_scenes: int) -> list[str]:
    """Deterministically split the script into `target_scenes` equal-word-count chunks.

    Splits at word boundaries rather than sentence boundaries. Unlike a Shorts teaser
    cutoff, a scene image has no reason to end on a sentence boundary — it's just a
    picture behind the narration, so a mid-sentence change is invisible to the viewer.
    Grouping by sentence instead left scene durations uneven (3s to 13s+) whenever the
    script had a long sentence, since it can't be split further without breaking one.
    Word-level splitting keeps every scene within a word of the same size.
    """
    words = script.split()
    if target_scenes <= 1 or not words:
        return [script.strip()]

    total_words = len(words)
    chunk_size = total_words / target_scenes
    groups = []
    for i in range(target_scenes):
        start = round(i * chunk_size)
        end = round((i + 1) * chunk_size) if i < target_scenes - 1 else total_words
        if start < end:
            groups.append(" ".join(words[start:end]))
    return groups


_PROMPT_BATCH_SIZE = 15  # smaller batches hit the exact requested count far more reliably
                           # than one large call — a 58-scene story asked for in one shot
                           # once silently returned only 57 prompts.
_PROMPT_MAX_ATTEMPTS = 2


def _generate_image_prompts(scene_texts: list[str]) -> list[str]:
    all_prompts = []
    for start in range(0, len(scene_texts), _PROMPT_BATCH_SIZE):
        batch = scene_texts[start:start + _PROMPT_BATCH_SIZE]
        all_prompts.extend(_generate_image_prompts_batch(batch))
    return all_prompts


def _generate_image_prompts_batch(scene_texts: list[str]) -> list[str]:
    numbered = "\n\n".join(f"Scene {i + 1}: {text}" for i, text in enumerate(scene_texts))
    # Response length scales with scene count (one prompt per scene), so a fixed cap that's
    # fine for a handful of scenes truncates the JSON once it's dozens.
    max_tokens = min(16000, max(2000, 300 + len(scene_texts) * 120))

    client = anthropic.Anthropic()
    last_error = None
    for attempt in range(1, _PROMPT_MAX_ATTEMPTS + 1):
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=_IMAGE_PROMPT_SYSTEM.format(count=len(scene_texts)),
            messages=[{"role": "user", "content": numbered}],
        )
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            prompts = json.loads(text)
        except json.JSONDecodeError as exc:
            last_error = f"Could not parse image prompts from model output:\n{text[:500]}"
            logger.warning("%s (attempt %d/%d)", last_error, attempt, _PROMPT_MAX_ATTEMPTS)
            continue

        if isinstance(prompts, list) and len(prompts) == len(scene_texts):
            return prompts

        got = len(prompts) if isinstance(prompts, list) else "invalid JSON"
        last_error = f"Expected {len(scene_texts)} image prompts, got {got}"
        logger.warning("%s (attempt %d/%d)", last_error, attempt, _PROMPT_MAX_ATTEMPTS)

    raise RuntimeError(last_error)


def _generate_image(prompt: str, out_path: Path, image_size: str | None = None) -> None:
    api_key = os.environ.get("FAL_KEY")
    if not api_key:
        raise RuntimeError(
            "FAL_KEY environment variable not set. Get a key at https://fal.ai/dashboard/keys "
            "and add it to .env."
        )

    response = requests.post(
        f"https://fal.run/{config.FAL_MODEL}",
        headers={"Authorization": f"Key {api_key}"},
        json={"prompt": prompt, "image_size": image_size or config.SCENE_IMAGE_SIZE, "num_images": 1},
        timeout=60,
    )
    response.raise_for_status()
    image_url = response.json()["images"][0]["url"]

    image_response = requests.get(image_url, timeout=60)
    image_response.raise_for_status()
    out_path.write_bytes(image_response.content)


_THUMBNAIL_PROMPT_SYSTEM = (
    "You are writing a YouTube thumbnail for the story below: a dedicated image-generation "
    "prompt, plus a short on-image caption (separate from the video's actual title).\n\n"
    "For the image: pick the story's single most visually striking, emotionally charged "
    "moment — something that would make someone stop scrolling. Describe it as a close, "
    "dramatic, cinematic shot: concrete setting, strong lighting, clear emotion on any "
    "character's face. Never include text, letters, or words in the image description. "
    "Text-to-image models render readable text as garbled nonsense, so also avoid describing "
    "anything a viewer would expect to read: shop signs, labels, book/magazine covers, "
    "screens, newspapers, storefronts with signage. If a setting would naturally have one, "
    "either frame the shot to exclude it or describe it as blurred, out of focus, or turned "
    "away from camera.\n\n"
    "For the caption: 3-6 words, punchy and curiosity-driving, in Title Case — this sits as "
    "bold text over the bottom of the thumbnail image itself, so it must be much shorter than "
    "the video's full title, not a restatement of it.\n\n"
    'Respond with ONLY a JSON object, nothing else: {{"image_prompt": "...", "caption": "..."}}'
)


def generate_thumbnail_image(script: str, out_path: Path) -> str:
    """Generate one dedicated, high-impact image for the video's thumbnail (not a narration scene).

    Returns the short on-image caption to overlay (distinct from the video's actual title,
    which is too long to read well as thumbnail text).
    """
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=400,
        system=_THUMBNAIL_PROMPT_SYSTEM,
        messages=[{"role": "user", "content": script}],
    )
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not parse thumbnail prompt/caption from model output:\n{text[:500]}") from exc

    out_path.parent.mkdir(parents=True, exist_ok=True)
    _generate_image(parsed["image_prompt"], out_path, image_size=config.THUMBNAIL_IMAGE_SIZE)
    logger.info("Generated thumbnail image (caption %r): %s", parsed["caption"], parsed["image_prompt"][:80])
    return parsed["caption"]


def generate_scenes(script: str, words: list[dict], scenes_dir: Path) -> list[tuple[Path, float]]:
    """Return [(image_path, duration_seconds), ...] covering the full narration in order.

    `scenes_dir` is where the generated images are written — pass a distinct directory per
    call (e.g. a different one per Shorts teaser) so filenames don't collide.
    """
    total_duration = words[-1]["end"] if words else 0.0
    target_scenes = _target_scene_count(total_duration)

    scene_texts = _split_into_scene_texts(script, target_scenes)
    image_prompts = _generate_image_prompts(scene_texts)

    word_counts = [len(text.split()) for text in scene_texts]
    total_words = sum(word_counts) or 1

    scenes_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, (prompt, word_count) in enumerate(zip(image_prompts, word_counts), start=1):
        duration = max(total_duration * word_count / total_words, config.SCENE_MIN_SECONDS)
        image_path = scenes_dir / f"scene_{i:02d}.png"
        _generate_image(prompt, image_path)
        logger.info("Scene %d/%d (%.1fs): %s", i, len(image_prompts), duration, prompt[:80])
        results.append([image_path, duration])

    # Rounding and the SCENE_MIN_SECONDS floor can leave the total short of the
    # narration; pad the last scene so the background never runs out before the audio does.
    shortfall = total_duration - sum(duration for _, duration in results)
    if shortfall > 0 and results:
        results[-1][1] += shortfall

    return [(image_path, duration) for image_path, duration in results]
