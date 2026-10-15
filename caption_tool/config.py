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
    font_size: int = 40  # Base font size (increased for high-impact readability)
    primary_color: str = "#FFFFFF"      # Base text color (hex)
    highlight_color: str = "#FF2020"    # Vibrant Red or Neon Green highlight (hex)
    secondary_color: str = "#00FF66"    # Secondary accent color (e.g. for numbers or alternating keywords)
    
    # Background Box styling
    has_box: bool = False               # Default: no dark background box
    box_rounded: bool = False           # Modern badge with smooth rounded corners
    box_radius: int = 20                # Corner radius (pixels, scaled to resolution)
    box_padding_x: int = 36             # Horizontal padding (pixels, scaled)
    box_padding_y: int = 20             # Vertical padding (pixels, scaled)
    box_border_width: float = 1.5       # Subtle border stroke width around rounded box
    box_border_color: str = "#2A2A2A"   # Subtle stroke color around badge
    box_color: str = "#121212"          # Dark rectangular background (hex)
    box_opacity: float = 0.90           # Opacity (0.0 to 1.0)
    
    # Outline / Stroke styling
    outline_width: float = 3.2          # Outline width in pixels for crisp contrast without box
    outline_color: str = "#000000"      # Stroke color (hex)
    shadow_depth: float = 1.8           # Drop shadow depth
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
        Generate ASS [V4+ Styles] line(s).
        For rounded badges, emits both foreground text style and vector badge style.
        """
        # Dynamic responsive font size scaling
        reference_height = min(play_res_x, play_res_y)
        scaled_font_size = max(20, int(self.font_size * (reference_height / 720.0)))

        primary = hex_to_ass_color(self.primary_color)
        secondary = hex_to_ass_color(self.secondary_color)
        outline = hex_to_ass_color(self.outline_color)
        
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

        if self.has_box and self.box_rounded:
            # Stylized rounded badge:
            # 1. Text Style: Clean typography with subtle outline for maximum contrast
            text_border_style = 1
            text_back = hex_to_ass_color("#000000", 0.0)
            text_outline_val = max(0.0, self.outline_width if self.outline_width > 0 else 0.5)
            text_shadow_val = 0.0
            
            text_style_line = (
                f"Style: Default,{self.font_name},{scaled_font_size},"
                f"{primary},{secondary},{outline},{text_back},"
                f"{bold_val},{italic_val},0,0,100,100,0,0,"
                f"{text_border_style},{text_outline_val:.1f},{text_shadow_val:.1f},{align},"
                f"{margin_l},{margin_r},{margin_v},1"
            )
            
            # 2. BoxBadge Style for vector drawing (\p1)
            box_fill = hex_to_ass_color(self.box_color, self.box_opacity)
            box_stroke = hex_to_ass_color(self.box_border_color, self.box_opacity if self.box_border_width > 0 else 0.0)
            box_style_line = (
                f"Style: BoxBadge,{self.font_name},{scaled_font_size},"
                f"{box_fill},{secondary},{box_stroke},{text_back},"
                f"0,0,0,0,100,100,0,0,"
                f"1,{self.box_border_width:.1f},0.0,7,"
                f"0,0,0,1"
            )
            return f"{text_style_line}\n{box_style_line}"

        elif self.has_box and not self.box_rounded:
            # Classic square rectangular box using ASS BorderStyle 3
            border_style = 3
            back = hex_to_ass_color(self.box_color, self.box_opacity)
            box_padding = max(2.0, self.outline_width)
            outline_val = box_padding
            shadow_val = 0.0
            return (
                f"Style: Default,{self.font_name},{scaled_font_size},"
                f"{primary},{secondary},{outline},{back},"
                f"{bold_val},{italic_val},0,0,100,100,0,0,"
                f"{border_style},{outline_val:.1f},{shadow_val:.1f},{align},"
                f"{margin_l},{margin_r},{margin_v},1"
            )
        else:
            # BorderStyle 1 = Outline + drop shadow
            border_style = 1
            back = hex_to_ass_color(self.shadow_color, 0.7)
            outline_val = self.outline_width
            shadow_val = self.shadow_depth
            return (
                f"Style: Default,{self.font_name},{scaled_font_size},"
                f"{primary},{secondary},{outline},{back},"
                f"{bold_val},{italic_val},0,0,100,100,0,0,"
                f"{border_style},{outline_val:.1f},{shadow_val:.1f},{align},"
                f"{margin_l},{margin_r},{margin_v},1"
            )


@dataclass
class CPUGovernorConfig:
    """Resource controls to protect host CPU and agent responsiveness."""
    max_threads: int = 2               # Hard limit on FFmpeg worker threads
    preset: str = "ultrafast"          # ultrafast | veryfast | fast
    crf: int = 22                      # Constant Rate Factor (18-28, 22 is crisp & fast)
    use_hardware_accel: bool = True    # Auto-probe QSV, AMF, NVENC
    mode: Literal["burn", "soft", "sub_only"] = "burn"
