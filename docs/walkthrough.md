# Walkthrough: Agent-Ready Stylized Video Captioning Tool

A complete, production-grade CLI and Python tool built for AI agents that automatically transcribes video via **Deepgram** (with word-level timestamps) and burns stylized dynamic captions into video at **adjustable positions (default: middle)** using **FFmpeg `libass`**.

---

## 🛠️ What Was Built

The tool is located in:  
📁 `C:\Users\mdfai\.gemini\antigravity\scratch\video_caption_tool`

```
video_caption_tool/
├── caption_tool/
│   ├── __init__.py          # Package export
│   ├── __main__.py          # CLI runner entrypoint
│   ├── cli.py               # Argument parser + JSON I/O
│   ├── config.py            # Typography, ASS color models, and CPU governor
│   ├── presets.py           # Presets (boxed_red_accent, boxed_green_accent, hormozi, etc.)
│   ├── chunker.py           # Word chunking & speech pause engine
│   ├── ass_builder.py       # ASS subtitle generator with dynamic word highlighting
│   ├── transcriber.py       # Audio extraction & Deepgram REST client (+ offline mock mode)
│   ├── hardware.py          # Auto-prober for QSV, AMF, NVENC hardware acceleration
│   ├── video_engine.py      # FFmpeg runner with CPU thread governance and path safety
│   └── agent_tool.py        # High-level Python class for agent tool calling
├── tests/
│   ├── test_chunker.py      # Unit tests for chunking logic
│   ├── test_ass_builder.py  # Unit tests for ASS syntax & color codes
│   └── test_pipeline_mock.py# End-to-end integration test with synthetic video
├── requirements.txt
└── README.md                # Complete documentation
```

---

## 🎨 Supported Styles

### 1. `boxed_red_accent` *(Default - Your Favorite)*
- **Visuals**: Dark charcoal / black rectangular box (`#121212` with 88% opacity), bold white uppercase text (`Arial Black`), and active words highlighted in **vibrant bold crimson red** (`#FF2020`).
- **Position**: Middle of the video (`Alignment 5`).

### 2. `boxed_green_accent`
- **Visuals**: Dark rectangular box with bold white text and active words highlighted in **shiny neon green** (`#00FF66`).

### 3. `hormozi_yellow`
- **Visuals**: Massive uppercase text, thick black outline, drop shadow, and **electric neon yellow** (`#FFE600`) dynamic highlight.

### 4. `beast_pop`
- **Visuals**: High-energy pop-in with **electric cyan** (`#00D4FF`) and **neon green** (`#00FF66`).

### 5. `minimal_clean` & `classic_sub`
- **Visuals**: Sleek translucent frosted pill or classic subtitle formats for minimalist or documentary videos.

---

## ⚡ Low-CPU Architecture Protections

To prevent starving your agent runtime on systems with limited CPU:
1. **Thread Capping (`--threads 2`)**: Limits FFmpeg worker threads so it never monopolizes 100% of the host machine's cores.
2. **Ultrafast Video Encoding**: Uses `-preset ultrafast` and `-crf 22`, reducing CPU burn time by up to 85% compared to standard encoders.
3. **Audio Stream Copy (`-c:a copy`)**: Direct audio passthrough with **0% transcode overhead**.
4. **Cloud Transcription**: All AI speech inference is offloaded to Deepgram Nova-2 in the cloud.
5. **Hardware Probing**: Automatically detects and leverages Intel QuickSync (`h264_qsv`), AMD AMF (`h264_amf`), or NVIDIA NVENC if present.

---

## 💻 How to Use It

### 1. Configure Deepgram API Key
```powershell
$env:DEEPGRAM_API_KEY = "your_deepgram_api_key_here"
```

### 2. Run via Command Line (for Agents or CLI)
```powershell
python -m caption_tool process input.mp4 --output captioned.mp4
```

### 3. Change Style or Position
```powershell
# Shiny green highlight in the middle
python -m caption_tool process input.mp4 --style boxed_green_accent --position middle

# Vibrant red highlight at the bottom
python -m caption_tool process input.mp4 --style boxed_red_accent --position bottom

# Custom colors on demand
python -m caption_tool process input.mp4 --highlight-color "#FF2020" --box-color "#0A0A0A" --box-opacity 0.95
```

### 4. Machine-Readable Agent Output (JSON)
The tool outputs structured JSON to `stdout`, making it easy for an agent to parse:
```json
{
  "status": "success",
  "input_video": "C:\\path\\input.mp4",
  "output_video": "C:\\path\\captioned.mp4",
  "duration_seconds": 15.4,
  "resolution": "1080x1920",
  "style_applied": "boxed_red_accent",
  "position": "middle",
  "highlight_color": "#FF2020",
  "word_count": 48,
  "chunk_count": 14,
  "execution_time_seconds": 3.8,
  "is_mock": false
}
```

### 5. Programmatic Python Usage
```python
from caption_tool import VideoCaptionAgentTool

tool = VideoCaptionAgentTool()
result = tool.process(
    video_path="input.mp4",
    output_path="captioned.mp4",
    style_preset="boxed_red_accent",
    position="middle",
    highlight_color="#FF2020",
    cpu_threads=2,
)
print(result["output_video"])
```

---

## 🧪 Validation & Test Results

The test suite was run and all 9 unit and integration tests passed:
- `test_chunker.py`: Verifies word grouping, 0.5s pause detection, and high-impact keyword detection.
- `test_ass_builder.py`: Verifies centisecond timestamp formatting, hex-to-ASS BGR color conversion, `Alignment=5` (middle/center), `BorderStyle=3` (box), and inline dynamic highlight tag injection (`{\c&H...&}`).
- `test_pipeline_mock.py`: Generates synthetic test video and executes the full pipeline end-to-end.
- **CLI Verification**: Verified `presets`, `schema`, and `process` subcommands on test videos with both red (`#FF2020`) and green (`#00FF66`) styles.
