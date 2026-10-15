# Implementation Plan: Production-Grade Stylized Video Captioning Tool for Agents

An autonomous, agent-ready CLI and Python tool that transcribes video using **Deepgram**, formats **rich stylized dynamic captions** (including dark rectangular badge with bold white text & red highlights, Alex Hormozi punchy burst, Vox documentary minimal, and more), with strict low-CPU performance controls and default middle-of-screen positioning.

---

## 1. How Stylized Captions Work Under the Hood

### 1.1 The ASS (Advanced SubStation Alpha) Engine
Instead of slow frame-by-frame Python drawing (which chokes CPUs), we leverage the industry-standard **ASS format** rendered directly in C by FFmpeg's `libass`. 

ASS allows native vector and typographic operations directly in the subtitle stream:
1. **Dark Rectangular Bounding Box**: 
   - Uses ASS `BorderStyle=3` (opaque bounding box) or drawing codes (`\p1 ... \p0`) with customizable background alpha (`&HAABBGGRR&`).
   - Produces crisp, cinema-grade rectangular badges behind text, guaranteeing 100% legibility over any video footage.
2. **Dynamic Active-Word Highlighting**:
   - Deepgram provides exact millisecond timestamps for each word (e.g. `"REVOLUTIONARY" [1.24s -> 1.82s]`).
   - The generator splits each phrase into dialogue events where the active word is wrapped in an inline color switch:
     `{\c&H0000FF&\b1}REVOLUTIONARY{\c&HFFFFFF&\b0}` (switching from white to bold red exactly while spoken).
3. **Dead-Center Middle Positioning**:
   - Uses ASS `Alignment=5` (middle center). The text is mathematically centered both horizontally and vertically, with fine vertical offset controls (`MarginV`).

---

## 2. Supported Caption Styles & Sources

We provide a comprehensive built-in catalog inspired by top video formats across social platforms, creator styles, and cinema, plus a custom override engine for agents.

### Style Catalog:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. "boxed_red_accent" (User Favorite - Ali Abdaal / Vox / Documentary)          │
│    [ DARK RECTANGULAR BOX ]  BOLD WHITE TEXT  [ BOLD RED HIGHLIGHT ]            │
│    - Background: Solid or 80% opaque dark charcoal / black box (#1A1A1A)       │
│    - Text: Bold modern sans-serif (Arial Black / Montserrat), crisp white        │
│    - Highlight: High-energy bold Crimson Red (#FF2020) for active/key words      │
│    - Position: Middle of video (Alignment 5)                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 2. "hormozi_yellow" (Alex Hormozi / Fast-Paced Shorts)                          │
│    - Background: None, 4px heavy black stroke outline + drop shadow             │
│    - Text: Massive uppercase Arial Black, bright white                           │
│    - Highlight: Electric Neon Yellow (#FFE600)                                  │
│    - Pacing: 2–3 words per burst (high engagement)                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 3. "beast_pop" (MrBeast / High-Energy Viral)                                    │
│    - Background: Heavy outline                                                  │
│    - Text: Bold uppercase font                                                  │
│    - Highlight: Vibrant Neon Green (#00FF66) / Electric Blue (#00D4FF)           │
│    - Pacing: 1–2 words per burst with rapid pop-ins                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 4. "minimal_clean" (Modern Aesthetic / Apple / Design Reels)                    │
│    - Background: Soft translucent frosted pill (30% black blur)                 │
│    - Text: Clean medium-weight sans-serif (Segoe UI / Inter), title-case         │
│    - Highlight: Understated warm accent or pure white glow                      │
│    - Pacing: 4–6 words per line                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 5. "classic_sub" (Standard Subtitle / Accessibility)                            │
│    - Background: Subtle drop shadow, no box                                     │
│    - Text: Standard white subtitle, sentence-level chunking                     │
│    - Highlight: None (continuous reading flow)                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 6. "custom" (Agent Full Parametric Control)                                     │
│    - Pass any combination of colors, fonts, box alpha, outline, and chunks.     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Highlighting Modes: Word-by-Word vs Key-Term Detection

The agent can configure how words get highlighted:
1. **`active_word` (Dynamic Karaoke)**: Every word lights up (e.g. in red) at the exact millisecond it is spoken, then returns to white. Best for short-form video retention.
2. **`keywords` (Semantic Emphasis)**: Emphasizes important words (nouns, action verbs, numbers, superlatives) in bold red while the rest remain white.
3. **`all`**: Entire phrase lights up uniformly during its display window.

---

## 4. Agent Tool & CLI Interface

The tool is completely headless and accepts simple flags or a JSON configuration payload.

### CLI Example (Using your favorite style):
```bash
python -m caption_tool process video.mp4 \
  --style boxed_red_accent \
  --position middle \
  --output captioned_video.mp4 \
  --format json
```

### Parametric Custom Override:
```bash
python -m caption_tool process video.mp4 \
  --position middle \
  --font "Arial Black" \
  --text-color "#FFFFFF" \
  --highlight-color "#FF1E1E" \
  --box-color "#121212" \
  --box-opacity 0.85 \
  --words-per-chunk 3 \
  --output output.mp4
```

### Structured Output for the Agent:
```json
{
  "status": "success",
  "input_video": "video.mp4",
  "output_video": "captioned_video.mp4",
  "duration_seconds": 18.4,
  "style_applied": "boxed_red_accent",
  "position": "middle",
  "word_count": 42,
  "execution_time_seconds": 3.8
}
```

---

## 5. Low-CPU Performance Protections (Preserved)

1. **CPU Governor**: `-threads 2` thread cap prevents starving the agent.
2. **Audio Passthrough**: `-c:a copy` preserves original audio bit-for-bit with 0% transcode load.
3. **Ultrafast Video Profile**: `-preset ultrafast` finishes 1080p clips in seconds.
4. **Cloud STT**: Deepgram Nova-2 handles all AI audio processing off-device.

---

## 6. Implementation Steps

1. **`config.py` & `presets.py`**:
   - Define data models for typography, colors, bounding box options, and alignment.
   - Implement presets: `boxed_red_accent` (default), `hormozi_yellow`, `beast_pop`, `minimal_clean`, `classic_sub`.
2. **`chunker.py`**:
   - Groups Deepgram word timestamps into optimal visual chunks (2–4 words for punchy reels, 5–7 words for clean subtitles) based on speech pauses and punctuation.
3. **`ass_builder.py`**:
   - Generates valid ASS v4+ scripts with `BorderStyle=3` (bounding box), `Alignment=5` (middle center), font properties, and dynamic `{\c&H...&}` highlight tags.
4. **`transcriber.py`**:
   - Deepgram client handling audio extraction + API call with word timestamps. Includes `--mock` mode for instant testing without API key.
5. **`video_engine.py`**:
   - FFmpeg runner with CPU thread capping, ultrafast encoding, and Windows path safety.
6. **`cli.py` & `agent_tool.py`**:
   - Command-line parser and standalone Python class for agent programmatic integration.
7. **Verification**:
   - Run unit tests on chunker and ASS generation.
   - Run end-to-end mock test on a synthetic video.
