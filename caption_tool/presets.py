"""Built-in style presets for stylized video captions."""

from typing import Dict
from .config import CaptionStyle


PRESETS: Dict[str, CaptionStyle] = {
    # 1. User Favorite: Dark rectangular box with bold white text & vibrant red highlights
    "boxed_red_accent": CaptionStyle(
        name="boxed_red_accent",
        font_name="Arial Black",
        font_size=26,
        primary_color="#FFFFFF",
        highlight_color="#FF2020",      # Vibrant Crimson Red
        secondary_color="#FF4D4D",
        has_box=True,
        box_color="#121212",            # Sleek dark rectangular box
        box_opacity=0.88,
        outline_width=4.0,              # Box padding
        shadow_depth=0.0,
        all_caps=True,
        bold=True,
        position="middle",
        words_per_chunk=3,
        highlight_mode="active_word",
    ),

    # 2. User Favorite Variant: Dark rectangular box with shiny neon green highlight
    "boxed_green_accent": CaptionStyle(
        name="boxed_green_accent",
        font_name="Arial Black",
        font_size=26,
        primary_color="#FFFFFF",
        highlight_color="#00FF66",      # Shiny Neon Green
        secondary_color="#39FF14",
        has_box=True,
        box_color="#121212",            # Dark rectangular box
        box_opacity=0.88,
        outline_width=4.0,
        shadow_depth=0.0,
        all_caps=True,
        bold=True,
        position="middle",
        words_per_chunk=3,
        highlight_mode="active_word",
    ),

    # 3. Alex Hormozi Style: Big punchy uppercase, thick outline, bright yellow highlight
    "hormozi_yellow": CaptionStyle(
        name="hormozi_yellow",
        font_name="Arial Black",
        font_size=28,
        primary_color="#FFFFFF",
        highlight_color="#FFE600",      # Electric Yellow
        secondary_color="#00FF66",      # Neon Green for secondary terms
        has_box=False,
        outline_width=3.5,              # Heavy black outline
        outline_color="#000000",
        shadow_depth=2.0,
        all_caps=True,
        bold=True,
        position="middle",
        words_per_chunk=3,
        highlight_mode="active_word",
    ),

    # 4. MrBeast Pop Style: High energy, electric cyan and green pops
    "beast_pop": CaptionStyle(
        name="beast_pop",
        font_name="Impact",
        font_size=30,
        primary_color="#FFFFFF",
        highlight_color="#00D4FF",      # Electric Cyan
        secondary_color="#00FF66",      # Shiny Green
        has_box=False,
        outline_width=4.0,
        outline_color="#000000",
        shadow_depth=2.5,
        all_caps=True,
        bold=True,
        position="middle",
        words_per_chunk=2,
        highlight_mode="active_word",
    ),

    # 5. Minimal Documentary / Apple Aesthetic
    "minimal_clean": CaptionStyle(
        name="minimal_clean",
        font_name="Segoe UI",
        font_size=22,
        primary_color="#F5F5F7",
        highlight_color="#FF3B30",      # Clean Red Accent
        secondary_color="#34C759",      # Clean Green Accent
        has_box=True,
        box_color="#000000",
        box_opacity=0.65,               # Translucent pill
        outline_width=3.0,
        shadow_depth=0.0,
        all_caps=False,
        bold=True,
        position="middle",
        words_per_chunk=4,
        highlight_mode="active_word",
    ),

    # 6. Classic Subtitle / Accessibility
    "classic_sub": CaptionStyle(
        name="classic_sub",
        font_name="Arial",
        font_size=22,
        primary_color="#FFFFFF",
        highlight_color="#FFFFFF",
        has_box=False,
        outline_width=2.0,
        outline_color="#000000",
        shadow_depth=1.0,
        all_caps=False,
        bold=False,
        position="bottom",
        words_per_chunk=6,
        highlight_mode="none",
    ),
}

DEFAULT_PRESET = "boxed_red_accent"


def get_preset(name: str = DEFAULT_PRESET) -> CaptionStyle:
    """Get a copy of a preset by name or default to boxed_red_accent."""
    if name not in PRESETS:
        name = DEFAULT_PRESET
    preset = PRESETS[name]
    # Return a shallow copy so modifications don't mutate the preset dictionary
    return CaptionStyle(**preset.__dict__)
