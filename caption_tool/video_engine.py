"""FFmpeg video processing engine with CPU governance and safe path escaping."""

import json
import os
import subprocess
from typing import Dict, Any, Tuple
from .config import CPUGovernorConfig
from .hardware import get_best_video_encoder


def get_video_metadata(video_path: str) -> Dict[str, Any]:
    """Inspect video dimensions and duration using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height,duration:format=duration",
        "-of", "json",
        video_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe inspection failed: {res.stderr}")

    data = json.loads(res.stdout)
    width = 1080
    height = 1920
    duration = 0.0

    streams = data.get("streams", [])
    for s in streams:
        if "width" in s and "height" in s:
            width = int(s["width"])
            height = int(s["height"])
            if "duration" in s and s["duration"]:
                try:
                    duration = float(s["duration"])
                except ValueError:
                    pass
            break

    if duration <= 0.0:
        fmt = data.get("format", {})
        if "duration" in fmt and fmt["duration"]:
            try:
                duration = float(fmt["duration"])
            except ValueError:
                pass

    return {
        "width": width,
        "height": height,
        "duration": duration,
    }


def escape_ffmpeg_ass_path(path: str) -> str:
    """
    Safely escape subtitle path for FFmpeg's libass filter,
    especially on Windows where colons and backslashes require escaping.
    Example: C:\\temp\\sub.ass -> C\\:/temp/sub.ass
    """
    normalized = os.path.abspath(path).replace("\\", "/")
    # Escape colon (e.g. C: -> C\:)
    escaped = normalized.replace(":", r"\:")
    # Escape single quotes
    escaped = escaped.replace("'", r"\'")
    return escaped


def render_captioned_video(
    input_video: str,
    ass_path: str,
    output_video: str,
    cpu_config: CPUGovernorConfig,
) -> None:
    """
    Burn ASS subtitles into the video using FFmpeg and libass,
    governed by thread ceilings and ultrafast presets for minimal CPU impact.
    """
    escaped_ass = escape_ffmpeg_ass_path(ass_path)
    vf_filter = f"ass='{escaped_ass}'"

    encoder = get_best_video_encoder(prefer_hardware=cpu_config.use_hardware_accel)

    cmd = [
        "ffmpeg", "-y",
        "-threads", str(cpu_config.max_threads),
        "-i", input_video,
        "-vf", vf_filter,
    ]

    # Encoder specific flags
    if encoder == "libx264":
        cmd.extend([
            "-c:v", "libx264",
            "-preset", cpu_config.preset,      # e.g. ultrafast
            "-crf", str(cpu_config.crf),       # e.g. 22
            "-threads", str(cpu_config.max_threads),
        ])
    else:
        # Hardware encoder (QSV / AMF / NVENC)
        cmd.extend([
            "-c:v", encoder,
        ])

    # Audio handling: attempt stream copy first for 0% CPU audio overhead
    cmd.extend([
        "-c:a", "copy",
        output_video
    ])

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        # If -c:a copy failed (e.g. incompatible audio codec in container), retry with lightweight aac
        if "Could not find tag for codec" in res.stderr or "Error initializing output stream" in res.stderr:
            cmd[-3] = "-c:a"
            cmd[-2] = "aac"
            cmd.insert(-1, "-b:a")
            cmd.insert(-1, "128k")
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg caption rendering failed:\n{res.stderr}")
