"""Command Line Interface for video captioning tool."""

import argparse
import json
import sys
from typing import List, Optional

from .agent_tool import VideoCaptionAgentTool
from .presets import PRESETS, DEFAULT_PRESET


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="caption_tool",
        description="Production-grade stylized video captioning for AI agents and workflows.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: process
    proc_parser = subparsers.add_parser("process", help="Caption a video")
    proc_parser.add_argument("video", type=str, help="Path to input video file")
    proc_parser.add_argument("-o", "--output", type=str, default=None, help="Output video path")
    proc_parser.add_argument(
        "-s", "--style", type=str, default=DEFAULT_PRESET,
        choices=list(PRESETS.keys()),
        help=f"Styling preset (default: {DEFAULT_PRESET})"
    )
    proc_parser.add_argument(
        "-p", "--position", type=str, default="middle",
        choices=["middle", "bottom", "top"],
        help="Subtitle positioning on screen (default: middle)"
    )
    proc_parser.add_argument("--highlight-color", type=str, default=None, help="Hex highlight color (e.g. #FF2020 or #00FF66)")
    proc_parser.add_argument("--primary-color", type=str, default=None, help="Hex primary text color (default: #FFFFFF)")
    proc_parser.add_argument("--box-color", type=str, default=None, help="Hex background box color (default: #121212)")
    proc_parser.add_argument("--box-opacity", type=float, default=None, help="Box opacity from 0.0 to 1.0 (default: 0.90)")
    proc_parser.add_argument("--box-rounded", action=argparse.BooleanOptionalAction, default=True, help="Enable/disable rounded corners on badge (default: True)")
    proc_parser.add_argument("--box-radius", type=int, default=None, help="Corner radius in pixels (default: 20)")
    proc_parser.add_argument("--box-border-width", type=float, default=None, help="Border stroke width around badge (default: 1.5)")
    proc_parser.add_argument("--box-border-color", type=str, default=None, help="Border stroke color (default: #2A2A2A)")
    proc_parser.add_argument("--font", type=str, default=None, help="Font name (e.g. 'Arial Black')")
    proc_parser.add_argument("--words-per-chunk", type=int, default=None, help="Max words per display burst (default: 3)")
    proc_parser.add_argument("--api-key", type=str, default=None, help="Deepgram API Key (or set DEEPGRAM_API_KEY env var)")
    proc_parser.add_argument("--mock", action="store_true", help="Run with mock transcription (offline test, 0 credits)")
    proc_parser.add_argument("--threads", type=int, default=2, help="Max FFmpeg CPU threads to protect agent host (default: 2)")
    proc_parser.add_argument("--mode", type=str, default="burn", choices=["burn", "sub_only"], help="Output mode (default: burn)")
    proc_parser.add_argument("--format", type=str, default="json", choices=["json", "human"], help="Output format (default: json)")

    # Command: presets
    subparsers.add_parser("presets", help="List available style presets")

    # Command: schema
    subparsers.add_parser("schema", help="Print JSON Schema specification for agent tool registration")

    return parser


def main(args: Optional[List[str]] = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(args)

    tool = VideoCaptionAgentTool()

    if parsed.command == "presets":
        presets = tool.get_supported_presets()
        print(json.dumps(presets, indent=2))
        return 0

    elif parsed.command == "schema":
        schema = {
            "name": "generate_stylized_captions",
            "description": "Transcribes a video with Deepgram and burns stylized, centered captions (with vibrant red/green highlights and dark background box) into the video.",
            "parameters": {
                "type": "object",
                "properties": {
                    "video": {"type": "string", "description": "Absolute path to input video file"},
                    "output": {"type": "string", "description": "Optional destination path for captioned video"},
                    "style": {
                        "type": "string",
                        "enum": list(PRESETS.keys()),
                        "default": "boxed_red_accent",
                        "description": "Style preset name (e.g. boxed_red_accent, boxed_green_accent, hormozi_yellow)"
                    },
                    "position": {
                        "type": "string",
                        "enum": ["middle", "bottom", "top"],
                        "default": "middle",
                        "description": "Screen alignment (default: middle)"
                    },
                    "highlight_color": {
                        "type": "string",
                        "description": "Hex color for active highlighted word (e.g. #FF2020 for vibrant red, #00FF66 for shiny green)"
                    },
                    "threads": {
                        "type": "integer",
                        "default": 2,
                        "description": "CPU thread limit to protect host resources"
                    }
                },
                "required": ["video"]
            }
        }
        print(json.dumps(schema, indent=2))
        return 0

    elif parsed.command == "process":
        try:
            result = tool.process(
                video_path=parsed.video,
                output_path=parsed.output,
                style_preset=parsed.style,
                position=parsed.position,
                highlight_color=parsed.highlight_color,
                primary_color=parsed.primary_color,
                box_color=parsed.box_color,
                box_opacity=parsed.box_opacity,
                box_rounded=parsed.box_rounded,
                box_radius=parsed.box_radius,
                box_border_width=parsed.box_border_width,
                box_border_color=parsed.box_border_color,
                font_name=parsed.font,
                words_per_chunk=parsed.words_per_chunk,
                api_key=parsed.api_key,
                mock=parsed.mock,
                cpu_threads=parsed.threads,
                mode=parsed.mode,
            )
            if parsed.format == "json":
                print(json.dumps(result, indent=2))
            else:
                print(f"Success! Output saved to: {result['output_video']}")
                print(f"Duration: {result['duration_seconds']}s | Execution Time: {result['execution_time_seconds']}s")
            return 0
        except Exception as e:
            err_payload = {"status": "error", "error": str(e)}
            if parsed.format == "json":
                print(json.dumps(err_payload, indent=2), file=sys.stderr)
            else:
                print(f"Error: {e}", file=sys.stderr)
            return 1
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
