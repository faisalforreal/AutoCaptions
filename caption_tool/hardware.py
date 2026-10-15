"""Hardware acceleration detection and probing for low CPU video encoding."""

import subprocess
import shutil
from typing import Optional


_DETECTED_ENCODER: Optional[str] = None


def test_encoder(encoder_name: str) -> bool:
    """Test if a video encoder is actually functional on this hardware."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=64x64:d=0.1",
        "-c:v", encoder_name,
        "-f", "null", "-"
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        return res.returncode == 0
    except Exception:
        return False


def get_best_video_encoder(prefer_hardware: bool = True) -> str:
    """
    Detect the most efficient video encoder available.
    Prefers hardware acceleration (NVENC, QSV, AMF) to achieve near 0% CPU load,
    otherwise falls back to libx264.
    """
    global _DETECTED_ENCODER
    if _DETECTED_ENCODER:
        return _DETECTED_ENCODER

    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg executable not found in system PATH.")

    if prefer_hardware:
        candidate_hardware_encoders = [
            "h264_qsv",     # Intel Quick Sync (standard on modern Intel CPUs)
            "h264_amf",     # AMD AMF (standard on modern AMD CPUs/APUs)
            "h264_nvenc",   # NVIDIA NVENC
        ]
        for enc in candidate_hardware_encoders:
            if test_encoder(enc):
                _DETECTED_ENCODER = enc
                return _DETECTED_ENCODER

    _DETECTED_ENCODER = "libx264"
    return _DETECTED_ENCODER
