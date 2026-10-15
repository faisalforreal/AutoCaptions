"""ASS (Advanced SubStation Alpha) subtitle file generator with dynamic highlighting and stylized rounded boxes."""

from typing import List, Tuple
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


def measure_text_dimensions(text: str, font_name: str, font_size: int) -> Tuple[int, int]:
    """Measure pixel width and height of text for ASS bounding box."""
    try:
        from PIL import ImageFont, ImageDraw, Image
        font = None
        font_candidates = [font_name]
        lower_name = font_name.lower()
        if "black" in lower_name:
            font_candidates.extend(["ariblk.ttf", "Arial Black.ttf", "Arial-Black.ttf", "arialbd.ttf"])
        elif "bold" in lower_name or "impact" in lower_name:
            font_candidates.extend(["impact.ttf", "arialbd.ttf", "Impact.ttf"])
        else:
            font_candidates.extend(["arial.ttf", "arialbd.ttf", "segoeui.ttf"])

        for cand in font_candidates:
            try:
                font = ImageFont.truetype(cand, font_size)
                break
            except Exception:
                continue

        if font is None:
            font = ImageFont.load_default()

        im = Image.new("RGB", (10, 10))
        draw = ImageDraw.Draw(im)
        bbox = draw.textbbox((0, 0), text, font=font)
        w = max(10, bbox[2] - bbox[0])
        h = max(10, bbox[3] - bbox[1])
        return w, h
    except Exception:
        avg_char_w = int(font_size * 0.65)
        return int(len(text) * avg_char_w), int(font_size * 1.1)


def make_rounded_rect_path(w: float, h: float, r: float) -> str:
    """Generate ASS vector drawing commands (\\p1) for a rounded rectangle."""
    r = max(0.0, min(r, w / 2.0, h / 2.0))
    if r <= 0.0:
        return f"m 0 0 l {w:.1f} 0 l {w:.1f} {h:.1f} l 0 {h:.1f}"

    # Cubic Bézier constant for quarter-circle approximation
    k = r * 0.55228475
    return (
        f"m {r:.1f} 0 "
        f"l {w - r:.1f} 0 "
        f"b {w - r + k:.1f} 0 {w:.1f} {r - k:.1f} {w:.1f} {r:.1f} "
        f"l {w:.1f} {h - r:.1f} "
        f"b {w:.1f} {h - r + k:.1f} {w - r + k:.1f} {h:.1f} {w - r:.1f} {h:.1f} "
        f"l {r:.1f} {h:.1f} "
        f"b {r - k:.1f} {h:.1f} 0 {h - r + k:.1f} 0 {h - r:.1f} "
        f"l 0 {r:.1f} "
        f"b 0 {r - k:.1f} {r - k:.1f} 0 {r:.1f} 0"
    )


def build_ass_script(
    chunks: List[ChunkItem],
    style: CaptionStyle,
    play_res_x: int = 1080,
    play_res_y: int = 1920,
) -> str:
    """
    Generate complete ASS subtitle script with dynamic highlighting, middle positioning,
    and stylized rounded box badges.
    """
    ass_primary_color = hex_to_ass_color(style.primary_color)
    ass_highlight_color = hex_to_ass_color(style.highlight_color)

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

    # Metrics scaling
    reference_height = min(play_res_x, play_res_y)
    scale = reference_height / 720.0
    scaled_font_size = max(18, int(style.font_size * scale))
    scaled_radius = max(4, int(style.box_radius * scale))
    scaled_pad_x = max(12, int(style.box_padding_x * scale))
    scaled_pad_y = max(8, int(style.box_padding_y * scale))

    # Calculate center point
    cx = play_res_x / 2.0
    if style.position == "middle":
        cy = (play_res_y / 2.0) + style.margin_v
    elif style.position == "bottom":
        margin = style.margin_v if style.margin_v != 0 else int(130 * scale)
        cy = play_res_y - margin
    elif style.position == "top":
        margin = style.margin_v if style.margin_v != 0 else int(130 * scale)
        cy = margin
    else:
        cy = (play_res_y / 2.0) + style.margin_v

    dialogue_lines: List[str] = []
    is_rounded = style.has_box and style.box_rounded

    for chunk in chunks:
        words = chunk.words
        if not words:
            continue

        full_text = " ".join(
            (w.punctuated_word.upper() if style.all_caps else w.punctuated_word) for w in words
        )

        # Layer 0: Stylized Rounded Badge Background
        if is_rounded:
            tw, th = measure_text_dimensions(full_text, style.font_name, scaled_font_size)
            bw = min(float(play_res_x - 30), tw + scaled_pad_x * 2.0)
            bh = max(th + scaled_pad_y * 2.0, float(int(scaled_font_size * 1.45)))
            bx = cx - (bw / 2.0)
            by = cy - (bh / 2.0)
            r = min(float(scaled_radius), bw / 2.0, bh / 2.0)
            path = make_rounded_rect_path(bw, bh, r)

            chunk_start_str = format_ass_time(chunk.start)
            chunk_end_str = format_ass_time(chunk.end)
            dialogue_lines.append(
                f"Dialogue: 0,{chunk_start_str},{chunk_end_str},BoxBadge,,0,0,0,,{{\\an7\\pos({bx:.1f},{by:.1f})\\p1}}{path}{{\\p0}}"
            )

        # Layer 1 (or 0 for non-rounded): Text with dynamic highlighting
        text_layer = 1 if is_rounded else 0
        pos_prefix = f"{{\\an5\\pos({cx:.1f},{cy:.1f})}}" if is_rounded else ""

        if style.highlight_mode == "active_word":
            for idx, active_word in enumerate(words):
                seg_start = active_word.start
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
                        formatted_words.append(f"{{\\c{ass_highlight_color}}}{text}{{\\c{ass_primary_color}}}")
                    else:
                        formatted_words.append(text)

                line_text = pos_prefix + " ".join(formatted_words)
                start_str = format_ass_time(seg_start)
                end_str = format_ass_time(seg_end)
                dialogue_lines.append(f"Dialogue: {text_layer},{start_str},{end_str},Default,,0,0,0,,{line_text}")

        elif style.highlight_mode == "keywords":
            formatted_words = []
            for w in words:
                text = w.punctuated_word.upper() if style.all_caps else w.punctuated_word
                if w.is_keyword:
                    formatted_words.append(f"{{\\c{ass_highlight_color}}}{text}{{\\c{ass_primary_color}}}")
                else:
                    formatted_words.append(text)

            line_text = pos_prefix + " ".join(formatted_words)
            start_str = format_ass_time(chunk.start)
            end_str = format_ass_time(chunk.end)
            dialogue_lines.append(f"Dialogue: {text_layer},{start_str},{end_str},Default,,0,0,0,,{line_text}")

        elif style.highlight_mode == "all":
            formatted_words = [
                (w.punctuated_word.upper() if style.all_caps else w.punctuated_word) for w in words
            ]
            line_text = pos_prefix + f"{{\\c{ass_highlight_color}}}" + " ".join(formatted_words)
            start_str = format_ass_time(chunk.start)
            end_str = format_ass_time(chunk.end)
            dialogue_lines.append(f"Dialogue: {text_layer},{start_str},{end_str},Default,,0,0,0,,{line_text}")

        else:
            formatted_words = [
                (w.punctuated_word.upper() if style.all_caps else w.punctuated_word) for w in words
            ]
            line_text = pos_prefix + " ".join(formatted_words)
            start_str = format_ass_time(chunk.start)
            end_str = format_ass_time(chunk.end)
            dialogue_lines.append(f"Dialogue: {text_layer},{start_str},{end_str},Default,,0,0,0,,{line_text}")

    return "\n".join(header + dialogue_lines) + "\n"
