"""Generate a click-friendly thumbnail from the template + story hook."""
import logging
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import config

logger = logging.getLogger(__name__)


def generate_thumbnail(hook_text: str, out_path: Path) -> None:
    if not config.THUMB_TEMPLATE.exists():
        raise RuntimeError(f"Thumbnail template not found at {config.THUMB_TEMPLATE}. Add one before rendering.")

    image = Image.open(config.THUMB_TEMPLATE).convert("RGB").resize(config.THUMB_SIZE)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(config.THUMB_FONT), config.THUMB_FONT_SIZE)

    wrapped = textwrap.fill(hook_text.upper(), width=config.THUMB_MAX_CHARS_PER_LINE)
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=10)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (config.THUMB_SIZE[0] - text_w) / 2
    y = config.THUMB_SIZE[1] - text_h - 80

    draw.multiline_text(
        (x, y), wrapped, font=font, fill=config.THUMB_FONT_COLOR,
        stroke_width=config.THUMB_STROKE_WIDTH, stroke_fill=config.THUMB_STROKE_COLOR,
        align="center", spacing=10,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)
    logger.info("Wrote thumbnail to %s", out_path)
