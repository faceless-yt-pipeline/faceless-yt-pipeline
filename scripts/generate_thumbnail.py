"""Generate a click-friendly thumbnail from a story hook, over an AI scene image or the template."""
import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

import config

logger = logging.getLogger(__name__)

_SIDE_MARGIN = 80
_VERTICAL_MARGIN = 60
_MIN_FONT_SIZE = 40
_FONT_STEP = 6
_SCRIM_HEIGHT_FRACTION = 0.5  # fraction of thumbnail height covered by the bottom gradient scrim
_SCRIM_MAX_ALPHA = 210


def _wrap_to_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    """Greedy word-wrap using actual measured pixel width, not a character-count guess."""
    lines = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\n".join(lines)


def _fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int):
    """Shrink the font until the wrapped text fits within max_width x max_height."""
    size = config.THUMB_FONT_SIZE
    while size >= _MIN_FONT_SIZE:
        font = ImageFont.truetype(str(config.THUMB_FONT), size)
        wrapped = _wrap_to_width(draw, text, font, max_width)
        bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=10)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if text_h <= max_height and text_w <= max_width:
            return font, wrapped, text_w, text_h
        size -= _FONT_STEP
    return font, wrapped, text_w, text_h  # best effort at the minimum size


def _add_bottom_scrim(image: Image.Image) -> Image.Image:
    """Dark gradient over the bottom of the image so text stays legible over a busy photo."""
    width, height = image.size
    scrim_height = int(height * _SCRIM_HEIGHT_FRACTION)
    scrim = Image.new("L", (1, scrim_height), color=0)
    for y in range(scrim_height):
        scrim.putpixel((0, y), int(_SCRIM_MAX_ALPHA * (y / scrim_height)))
    scrim = scrim.resize((width, scrim_height))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    black = Image.new("RGBA", (width, scrim_height), (0, 0, 0, 255))
    overlay.paste(black, (0, height - scrim_height), mask=scrim)
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def generate_thumbnail(hook_text: str, out_path: Path, background_image_path: Path | None = None) -> None:
    if background_image_path and background_image_path.exists():
        image = Image.open(background_image_path).convert("RGB")
        image = ImageOps.fit(image, config.THUMB_SIZE, Image.LANCZOS)
        image = _add_bottom_scrim(image)
        text_anchor = "bottom"
    else:
        if not config.THUMB_TEMPLATE.exists():
            raise RuntimeError(f"Thumbnail template not found at {config.THUMB_TEMPLATE}. Add one before rendering.")
        image = Image.open(config.THUMB_TEMPLATE).convert("RGB").resize(config.THUMB_SIZE)
        text_anchor = "center"

    draw = ImageDraw.Draw(image)

    max_width = config.THUMB_SIZE[0] - 2 * _SIDE_MARGIN
    max_height = config.THUMB_SIZE[1] - 2 * _VERTICAL_MARGIN
    font, wrapped, text_w, text_h = _fit_text(draw, hook_text.upper(), max_width, max_height)

    x = (config.THUMB_SIZE[0] - text_w) / 2
    if text_anchor == "bottom":
        y = config.THUMB_SIZE[1] - _VERTICAL_MARGIN - text_h
    else:
        y = (config.THUMB_SIZE[1] - text_h) / 2

    draw.multiline_text(
        (x, y), wrapped, font=font, fill=config.THUMB_FONT_COLOR,
        stroke_width=config.THUMB_STROKE_WIDTH, stroke_fill=config.THUMB_STROKE_COLOR,
        align="center", spacing=10,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)
    logger.info("Wrote thumbnail to %s (font size %d, background=%s)", out_path, font.size, text_anchor)
