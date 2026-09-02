"""Build a burned-in-ready .ass subtitle file from word-level timestamps."""
import logging
from pathlib import Path

import config

logger = logging.getLogger(__name__)

_ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},{color},{highlight},{outline},&H00000000,1,0,0,0,100,100,0,0,1,4,0,2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ass_style_color(rgb_hex: str) -> str:
    """RRGGBB -> ASS style color &HAABBGGRR (opaque)."""
    r, g, b = rgb_hex[0:2], rgb_hex[2:4], rgb_hex[4:6]
    return f"&H00{b}{g}{r}"


def _ass_override_color(rgb_hex: str) -> str:
    """RRGGBB -> ASS inline override color &HBBGGRR&."""
    r, g, b = rgb_hex[0:2], rgb_hex[2:4], rgb_hex[4:6]
    return f"&H{b}{g}{r}&"


def _ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def _chunk(words: list[dict], size: int) -> list[list[dict]]:
    return [words[i:i + size] for i in range(0, len(words), size)]


def build_captions(words: list[dict], out_ass_path: Path) -> None:
    """Write an ASS file that highlights the active word within each on-screen chunk."""
    base_color = _ass_override_color(config.CAPTION_FONT_COLOR)
    highlight_color = _ass_override_color(config.CAPTION_HIGHLIGHT_COLOR)

    lines = [_ASS_HEADER.format(
        width=config.VIDEO_WIDTH,
        height=config.VIDEO_HEIGHT,
        font=config.CAPTION_FONT.stem,
        size=config.CAPTION_FONT_SIZE,
        color=_ass_style_color(config.CAPTION_FONT_COLOR),
        highlight=_ass_style_color(config.CAPTION_HIGHLIGHT_COLOR),
        outline=_ass_style_color(config.CAPTION_OUTLINE_COLOR),
        margin_v=config.CAPTION_MARGIN_V,
    )]

    for chunk in _chunk(words, config.CAPTION_WORDS_PER_CHUNK):
        chunk_end = chunk[-1]["end"]
        for i, active in enumerate(chunk):
            seg_start = active["start"]
            seg_end = chunk[i + 1]["start"] if i + 1 < len(chunk) else chunk_end
            text_parts = []
            for j, w in enumerate(chunk):
                word = w["word"].upper()
                if j == i:
                    text_parts.append(f"{{\\c{highlight_color}}}{word}{{\\c{base_color}}}")
                else:
                    text_parts.append(word)
            text = " ".join(text_parts)
            lines.append(f"Dialogue: 0,{_ts(seg_start)},{_ts(seg_end)},Default,,0,0,0,,{text}\n")

    out_ass_path.parent.mkdir(parents=True, exist_ok=True)
    out_ass_path.write_text("".join(lines), encoding="utf-8")
    logger.info("Wrote captions to %s (%d words)", out_ass_path, len(words))
