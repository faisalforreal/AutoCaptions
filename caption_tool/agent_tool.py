"""Agent Tool wrapper providing high-level programmatic interface and structured JSON output."""

import os
import shutil
import tempfile
import time
from typing import Dict, Any, Optional

from .config import CaptionStyle, CPUGovernorConfig
from .presets import get_preset, DEFAULT_PRESET, PRESETS
from .transcriber import extract_audio_fast, transcribe_with_deepgram, generate_mock_words
from .chunker import chunk_words
from .ass_builder import build_ass_script
from .video_engine import get_video_metadata, render_captioned_video


class VideoCaptionAgentTool:
    """Production-grade video captioning tool designed for AI agents and automated workflows."""

    def __init__(self, default_api_key: Optional[str] = None):
        self.default_api_key = default_api_key or os.getenv("DEEPGRAM_API_KEY")

    def get_supported_presets(self) -> Dict[str, str]:
        """Return a mapping of available style preset names to their descriptions."""
        return {
            "boxed_red_accent": "Dark rectangular background, bold white text, bold vibrant red highlights (Default)",
            "boxed_green_accent": "Dark rectangular background, bold white text, shiny neon green highlights",
            "hormozi_yellow": "Alex Hormozi style: Thick black stroke, drop shadow, electric neon yellow active-word highlight",
            "beast_pop": "MrBeast style: High-energy bold pop font with cyan and neon green highlights",
            "minimal_clean": "Apple/Vox aesthetic: Translucent dark frosted pill with clean modern typography",
            "classic_sub": "Standard clean white subtitles with subtle drop shadow",
        }

    def process(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        style_preset: str = DEFAULT_PRESET,
        position: str = "middle",
        highlight_color: Optional[str] = None,
        primary_color: Optional[str] = None,
        box_color: Optional[str] = None,
        box_opacity: Optional[float] = None,
        box_rounded: Optional[bool] = None,
        box_radius: Optional[int] = None,
        box_border_width: Optional[float] = None,
        box_border_color: Optional[str] = None,
        font_name: Optional[str] = None,
        words_per_chunk: Optional[int] = None,
        api_key: Optional[str] = None,
        mock: bool = False,
        cpu_threads: int = 2,
        mode: str = "burn",
        keep_temp: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute full end-to-end video captioning pipeline.

        Returns a structured dictionary designed for easy machine consumption.
        """
        start_time = time.time()
        abs_video_path = os.path.abspath(video_path)

        if not os.path.isfile(abs_video_path):
            raise FileNotFoundError(f"Input video not found: {abs_video_path}")

        # Determine output path
        if not output_path:
            base, ext = os.path.splitext(abs_video_path)
            output_path = f"{base}_captioned{ext}"
        abs_output_path = os.path.abspath(output_path)

        # 1. Inspect Video Specs
        meta = get_video_metadata(abs_video_path)
        width = meta["width"]
        height = meta["height"]
        duration = meta["duration"]

        # 2. Configure Style & Overrides
        style: CaptionStyle = get_preset(style_preset)
        if position in ("middle", "bottom", "top"):
            style.position = position
        if highlight_color:
            style.highlight_color = highlight_color
        if primary_color:
            style.primary_color = primary_color
        if box_color:
            style.box_color = box_color
            style.has_box = True
        if box_opacity is not None:
            style.box_opacity = max(0.0, min(1.0, float(box_opacity)))
        if box_rounded is not None:
            style.box_rounded = box_rounded
        if box_radius is not None:
            style.box_radius = max(0, int(box_radius))
        if box_border_width is not None:
            style.box_border_width = max(0.0, float(box_border_width))
        if box_border_color:
            style.box_border_color = box_border_color
        if font_name:
            style.font_name = font_name
        if words_per_chunk:
            style.words_per_chunk = max(1, int(words_per_chunk))

        # 3. Create Temporary Workspace
        temp_dir = tempfile.mkdtemp(prefix="caption_tool_")
        temp_audio = os.path.join(temp_dir, "extracted_audio.mp3")
        temp_ass = os.path.join(temp_dir, "subtitles.ass")

        try:
            # 4. Transcribe Audio (Mock or Deepgram)
            if mock or (not api_key and not self.default_api_key):
                if not mock:
                    # If user didn't explicitly pass mock, but no API key is available, report notice
                    pass
                raw_words = generate_mock_words(duration_seconds=duration if duration > 0 else 6.0)
            else:
                extract_audio_fast(abs_video_path, temp_audio)
                effective_key = api_key or self.default_api_key
                raw_words = transcribe_with_deepgram(temp_audio, api_key=effective_key)

            # 5. Word Chunking
            chunks = chunk_words(
                raw_words,
                max_words_per_chunk=style.words_per_chunk,
            )

            # 6. Generate ASS Subtitle Script
            ass_content = build_ass_script(
                chunks=chunks,
                style=style,
                play_res_x=width,
                play_res_y=height,
            )

            with open(temp_ass, "w", encoding="utf-8") as f:
                f.write(ass_content)

            # 7. Render Video with CPU Governance
            cpu_config = CPUGovernorConfig(
                max_threads=cpu_threads,
                preset="ultrafast",
                crf=22,
                mode=mode, # type: ignore
            )

            if mode == "burn":
                render_captioned_video(
                    input_video=abs_video_path,
                    ass_path=temp_ass,
                    output_video=abs_output_path,
                    cpu_config=cpu_config,
                )
            elif mode == "sub_only":
                target_ass = os.path.splitext(abs_output_path)[0] + ".ass"
                shutil.copyfile(temp_ass, target_ass)
                abs_output_path = target_ass

            elapsed_seconds = round(time.time() - start_time, 2)

            return {
                "status": "success",
                "input_video": abs_video_path,
                "output_video": abs_output_path,
                "duration_seconds": duration,
                "resolution": f"{width}x{height}",
                "style_applied": style.name,
                "position": style.position,
                "highlight_color": style.highlight_color,
                "word_count": len(raw_words),
                "chunk_count": len(chunks),
                "execution_time_seconds": elapsed_seconds,
                "is_mock": mock or (not api_key and not self.default_api_key),
            }

        finally:
            if not keep_temp and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
