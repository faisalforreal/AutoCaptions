"""Configuration models and color conversion utilities for caption_tool."""

from dataclasses import dataclass, field
from typing import Optional, Literal
import re


def hex_to_ass_color(hex_str: str, opacity: float = 1.0) -> str:
    """
    Convert a hex color string (e.g. #FF2020 or FF2020) to ASS format (&HAABBGGRR&).
    Note: ASS uses BGR order, and Alpha where 00 is fully opaque and FF is fully transparent.
    """
    cleaned = hex_str.strip().lstrip("#").upper()
    if len(cleaned) == 3:
        cleaned = "".join(c * 2 for c in cleaned)
    
    if len(cleaned) != 6:
        # Fallback to white if invalid
        cleaned = "FFFFFF"

    r = int(cleaned[0:2], 16)
    g = int(cleaned[2:4], 16)
    b = int(cleaned[4:6], 16)

    # Invert opacity for ASS alpha: 1.0 opacity -> 0 alpha, 0.0 opacity -> 255 (FF) alpha
    clamped_opacity = max(0.0, min(1.0, opacity))
    alpha = int(round((1.0 - clamped_opacity) * 255))

    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}&"


@dataclass
class CaptionStyle:
    """Style configuration for video subtitles."""
    name: str = "custom"
    font_name: str = "Arial Black"
    font_size: int = 24  # Base font size (will be auto-scaled to video resolution)
    primary_color: str = "#FFFFFF"      # Base text color (hex)
    highlight_color: str = "#FF2020"    # Vibrant Red or Neon Green highlight (hex)
    secondary_color: str = "#00FF66"    # Secondary accent color (e.g. for numbers or alternating keywords)
    
    # Background Box styling
    has_box: bool = True
    box_color: str = "#141414"          # Dark rectangular background (hex)
    box_opacity: float = 0.88           # Opacity (0.0 to 1.0)
    
    # Outline / Stroke styling
    outline_width: float = 2.0          # Outline width in pixels
    outline_color: str = "#000000"      # Stroke color (hex)
    shadow_depth: float = 0.0           # Drop shadow depth
    shadow_color: str = "#000000"
    
    # Text behavior
    all_caps: bool = True               # Transform text to uppercase
    bold: bool = True                   # Bold text
    italic: bool = False
    
    # Positioning
    position: Literal["middle", "bottom", "top"] = "middle"
    margin_v: int = 0                   # Fine-tuning vertical offset (pixels)
    alignment: int = 5                  # ASS Alignment: 5 = Center/Middle, 2 = Bottom, 8 = Top
    
    # Pacing / Chunking
    words_per_chunk: int = 3            # Default words per display burst
    highlight_mode: Literal["active_word", "keywords", "all", "none"] = "active_word"

    def to_ass_style(self, play_res_x: int, play_res_y: int) -> str:
        """
        Generate ASS [V4+ Styles] line.
        Format:
        Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour,
                Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle,
                BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
        """
        # Dynamic responsive font size scaling
        # Standard base is 1080p (height 1920 or 1080)
        reference_height = min(play_res_x, play_res_y)
        scaled_font_size = max(18, int(self.font_size * (reference_height / 720.0)))

        primary = hex_to_ass_color(self.primary_color)
        secondary = hex_to_ass_color(self.secondary_color)
        outline = hex_to_ass_color(self.outline_color)
        
        if self.has_box:
            # BorderStyle 3 = Opaque rectangular box using BackColour
            border_style = 3
            back = hex_to_ass_color(self.box_color, self.box_opacity)
            box_padding = max(2.0, self.outline_width)
            outline_val = box_padding
            shadow_val = 0.0
        else:
            # BorderStyle 1 = Outline + drop shadow
            border_style = 1
            back = hex_to_ass_color(self.shadow_color, 0.7)
            outline_val = self.outline_width
            shadow_val = self.shadow_depth

        bold_val = -1 if self.bold else 0
        italic_val = -1 if self.italic else 0

        # Alignment mapping
        align = self.alignment
        if self.position == "middle":
            align = 5
        elif self.position == "bottom":
            align = 2
        elif self.position == "top":
            align = 8

        margin_l = 20
        margin_r = 20
        margin_v = self.margin_v if self.margin_v != 0 else (40 if align != 5 else 0)

        style_line = (
            f"Style: Default,{self.font_name},{scaled_font_size},"
            f"{primary},{secondary},{outline},{back},"
            f"{bold_val},{italic_val},0,0,100,100,0,0,"
            f"{border_style},{outline_val:.1f},{shadow_val:.1f},{align},"
            f"{margin_l},{margin_r},{margin_v},1"
        )
        return style_line


@dataclass
class CPUGovernorConfig:
    """Resource controls to protect host CPU and agent responsiveness."""
    max_threads: int = 2               # Hard limit on FFmpeg worker threads
    preset: str = "ultrafast"          # ultrafast | veryfast | fast
    crf: int = 22                      # Constant Rate Factor (18-28, 22 is crisp & fast)
    use_hardware_accel: bool = True    # Auto-probe QSV, AMF, NVENC
    mode: Literal["burn", "soft", "sub_only"] = "burn"
