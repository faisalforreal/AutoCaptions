# Video Caption Tool for AI Agents

A production-grade, headless CLI and Python tool that transcribes video audio via **Deepgram** (with word-level timestamps), generates stylized dynamic subtitles in **ASS** (Advanced SubStation Alpha) format, and burns them into video at adjustable positions (**default: middle of video**) using **FFmpeg `libass`**.

Engineered specifically for **AI agents with limited CPU resources**: includes strict CPU thread capping, ultrafast hardware/software profiles, and zero-CPU soft-mux options.

---

## 📚 Project Origins & Documentation
- **Conversation Link**: [Conversation 1d7562c2-77f6-497c-941c-be21dcc70fe2](conversation://1d7562c2-77f6-497c-941c-be21dcc70fe2)
- **Detailed History**: [docs/CONVERSATION_HISTORY.md](file:///c:/Users/mdfai/Documents/SideProjects/AutoCaptions/docs/CONVERSATION_HISTORY.md)
- **Implementation Plan**: [docs/implementation_plan.md](file:///c:/Users/mdfai/Documents/SideProjects/AutoCaptions/docs/implementation_plan.md)
- **Architecture Walkthrough**: [docs/walkthrough.md](file:///c:/Users/mdfai/Documents/SideProjects/AutoCaptions/docs/walkthrough.md)

---

## 🚀 Quick Start

### 1. Environment & API Key
Set your Deepgram API key:
```bash
# Windows PowerShell
$env:DEEPGRAM_API_KEY = "your_deepgram_api_key_here"

# Linux / MacOS
export DEEPGRAM_API_KEY="your_deepgram_api_key_here"
```

*(You can also pass it per-command with `--api-key <KEY>`)*

---

## 💻 Agent CLI Usage

### Basic Command (Default: Middle position + Dark Box with Bold White Text & Bold Red Highlight):
```bash
python -m caption_tool process input.mp4 --output output.mp4
```

### Response (Clean Structured JSON to stdout):
```json
{
  "status": "success",
  "input_video": "C:\\path\\input.mp4",
  "output_video": "C:\\path\\output.mp4",
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

---

## 🎨 Supported Style Presets

Run `python -m caption_tool presets` to list all presets:

| Preset Name | Visual Description | Best For |
| :--- | :--- | :--- |
| `boxed_red_accent` *(Default)* | **Dark rectangular box**, bold white text, **vibrant red highlight** (`#FF2020`) | Ali Abdaal / Vox / High contrast documentaries |
| `boxed_green_accent` | **Dark rectangular box**, bold white text, **shiny neon green highlight** (`#00FF66`) | High-tech, crypto, finance, and trading reels |
| `hormozi_yellow` | Massive bold font, thick black outline, drop shadow, **electric neon yellow** (`#FFE600`) | Fast-paced viral shorts / Alex Hormozi style |
| `beast_pop` | Heavy pop font with electric cyan (`#00D4FF`) & neon green accents | MrBeast high-energy viral retention |
| `minimal_clean` | Frosted dark pill, modern clean typography | Apple-style aesthetics, educational videos |
| `classic_sub` | Clean standard subtitles at bottom/middle | Accessibility and cinema |

---

## ⚙️ Positioning & Custom Parametric Overrides

Any preset can be tweaked with CLI flags:

- `--position`: `middle` (default), `bottom`, `top`.
- `--highlight-color`: Any hex color (e.g. `"#FF2020"` for red, `"#00FF66"` for shiny green, `"#00D4FF"` for cyan).
- `--primary-color`: Base text color (default `"#FFFFFF"`).
- `--box-color`: Bounding box background hex (default `"#121212"`).
- `--box-opacity`: Box opacity from `0.0` to `1.0` (default `0.88`).
- `--words-per-chunk`: Max words per burst (default `3`).
- `--threads`: Max CPU threads for FFmpeg (default `2` to protect host agent).

### Example: Custom Shiny Green in the Center
```bash
python -m caption_tool process input.mp4 \
  --position middle \
  --style boxed_green_accent \
  --highlight-color "#00FF66" \
  --output captioned.mp4
```

### Example: Offline Mock Testing (0 API credits used):
```bash
python -m caption_tool process input.mp4 --mock
```

---

## 🤖 Python Programmatic API (for LangChain, AutoGen, Custom Agents)

```python
from caption_tool import VideoCaptionAgentTool

tool = VideoCaptionAgentTool()

# Process video
result = tool.process(
    video_path="input.mp4",
    output_path="output.mp4",
    style_preset="boxed_red_accent",   # or boxed_green_accent, hormozi_yellow, etc.
    position="middle",                 # middle, bottom, top
    highlight_color="#FF2020",         # bold red
    cpu_threads=2,                     # CPU safety ceiling
)

print(result["output_video"])
```

---

## ⚡ Low-CPU Architecture Protections

1. **Cloud Speech Recognition (Deepgram Nova-2)**: 0% local CPU load.
2. **Audio Pre-processing**: Instant mono 16kHz audio extraction (<0.5s CPU).
3. **Thread Limiting**: `--threads 2` prevents CPU spikes from freezing or starving your agent runtime.
4. **Ultrafast Encoding**: `-preset ultrafast` finishes 1080p clips in seconds with minimal CPU load.
5. **Hardware Auto-Probing**: Automatically offloads to Intel QSV, AMD AMF, or NVIDIA NVENC if available on the host.
