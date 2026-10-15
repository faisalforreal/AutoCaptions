"""Audio extractor and Deepgram API client for word-level transcription."""

import os
import subprocess
import tempfile
import json
from typing import List, Dict, Any, Optional
import requests


def extract_audio_fast(video_path: str, output_audio_path: str) -> None:
    """
    Extract low-bitrate mono 16kHz audio from video using FFmpeg.
    Optimized for minimal CPU consumption and rapid upload to Deepgram.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",                      # Disable video stream
        "-ar", "16000",             # 16kHz sample rate (optimal for speech models)
        "-ac", "1",                 # Mono channel
        "-b:a", "48k",              # Low bitrate to save CPU & network upload
        output_audio_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")


def transcribe_with_deepgram(
    audio_path: str,
    api_key: Optional[str] = None,
    model: str = "nova-2",
) -> List[Dict[str, Any]]:
    """
    Send audio to Deepgram REST API and return list of word items with timestamps.
    """
    key = api_key or os.getenv("DEEPGRAM_API_KEY")
    if not key:
        raise ValueError(
            "DEEPGRAM_API_KEY is not configured. "
            "Please set the DEEPGRAM_API_KEY environment variable or pass --api-key <KEY>."
        )

    url = f"https://api.deepgram.com/v1/listen?model={model}&smart_format=true&punctuate=true&utterances=true"
    headers = {
        "Authorization": f"Token {key}",
        "Content-Type": "audio/mp3",
    }

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    response = requests.post(url, headers=headers, data=audio_data, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"Deepgram API error ({response.status_code}): {response.text}")

    data = response.json()
    channels = data.get("results", {}).get("channels", [])
    if not channels:
        return []

    alternatives = channels[0].get("alternatives", [])
    if not alternatives:
        return []

    raw_words = alternatives[0].get("words", [])
    return raw_words


def generate_mock_words(duration_seconds: float = 5.0) -> List[Dict[str, Any]]:
    """
    Generate realistic mock word-level timestamps for testing without an API key.
    """
    sample_text = [
        "THIS", "IS", "AN", "AMAZING", "STYLIZED", "CAPTION",
        "POWERED", "BY", "DEEPGRAM", "AND", "FFMPEG", "RUNNING", "PERFECTLY"
    ]
    words = []
    time_cursor = 0.4
    word_duration = 0.35
    gap = 0.08

    for word in sample_text:
        if time_cursor + word_duration > duration_seconds:
            break
        start = round(time_cursor, 2)
        end = round(time_cursor + word_duration, 2)
        words.append({
            "word": word,
            "punctuated_word": word + ("!" if word in ("AMAZING", "PERFECTLY") else ""),
            "start": start,
            "end": end,
            "confidence": 0.99
        })
        time_cursor += word_duration + gap

    return words
