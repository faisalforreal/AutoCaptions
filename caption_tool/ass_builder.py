"""ASS (Advanced SubStation Alpha) subtitle file generator with dynamic highlighting."""

from typing import List
from .config import CaptionStyle, hex_to_ass_color
from .chunker import ChunkItem, WordItem


def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS timestamp H:MM:SS.cs (centiseconds)."""
    if seconds < 0:
        seconds = 0.0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def build_ass_script(
    chunks: List[ChunkItem],
    style: CaptionStyle,
    play_res_x: int = 1080,
    play_res_y: int = 1920,
) -> str:
    """
    Generate complete ASS subtitle script with dynamic highlighting and middle positioning.
    """
    ass_primary_color = hex_to_ass_color(style.primary_color)
    ass_highlight_color = hex_to_ass_color(style.highlight_color)
    ass_secondary_color = hex_to_ass_color(style.secondary_color)

    style_line = style.to_ass_style(play_res_x, play_res_y)

    header = [
        "[Script Info]",
        "Title: Stylized Captions",
        "ScriptType: v4.00+",
        f"PlayResX: {play_res_x}",
        f"PlayResY: {play_res_y}",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        style_line,
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    dialogue_lines: List[str] = []

    for chunk in chunks:
        words = chunk.words
        if not words:
            continue

        if style.highlight_mode == "active_word":
            # For each word in the chunk, emit a dialogue slice where that specific word is highlighted
            for idx, active_word in enumerate(words):
                seg_start = active_word.start
                # Segment ends when the next word starts, or when this word ends
                if idx < len(words) - 1:
                    seg_end = words[idx + 1].start
                else:
                    seg_end = max(active_word.end, chunk.end)

                if seg_end <= seg_start:
                    seg_end = seg_start + 0.1

                formatted_words: List[str] = []
                for w_idx, w in enumerate(words):
                    text = w.punctuated_word.upper() if style.all_caps else w.punctuated_word
                    if w_idx == idx:
                        # Highlighted active word: bold color switch
                        formatted_words.append(f"{{\\c{ass_highlight_color}}}{text}{{\\c{ass_primary_color}}}")
                    else:
                        formatted_words.append(text)

                line_text = " ".join(formatted_words)
                start_str = format_ass_time(seg_start)
                end_str = format_ass_time(seg_end)
                dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        elif style.highlight_mode == "keywords":
            # Highlight high-impact terms throughout the entire chunk display duration
            formatted_words: List[str] = []
            for w in words:
                text = w.punctuated_word.upper() if style.all_caps else w.punctuated_word
                if w.is_keyword:
                    formatted_words.append(f"{{\\c{ass_highlight_color}}}{text}{{\\c{ass_primary_color}}}")
                else:
                    formatted_words.append(text)

            line_text = " ".join(formatted_words)
            start_str = format_ass_time(chunk.start)
            end_str = format_ass_time(chunk.end)
            dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        elif style.highlight_mode == "all":
            # Highlight all words in this chunk
            formatted_words = [
                (w.punctuated_word.upper() if style.all_caps else w.punctuated_word) for w in words
            ]
            line_text = f"{{\\c{ass_highlight_color}}}" + " ".join(formatted_words)
            start_str = format_ass_time(chunk.start)
            end_str = format_ass_time(chunk.end)
            dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        else:
            # Clean standard subtitle without inline color overrides
            formatted_words = [
                (w.punctuated_word.upper() if style.all_caps else w.punctuated_word) for w in words
            ]
            line_text = " ".join(formatted_words)
            start_str = format_ass_time(chunk.start)
            end_str = format_ass_time(chunk.end)
            dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

    return "\n".join(header + dialogue_lines) + "\n"
