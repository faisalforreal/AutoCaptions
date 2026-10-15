"""Video Caption Tool - Production-grade stylized captions for AI agents."""

from .agent_tool import VideoCaptionAgentTool
from .config import CaptionStyle, CPUGovernorConfig
from .presets import PRESETS, get_preset

__all__ = [
    "VideoCaptionAgentTool",
    "CaptionStyle",
    "CPUGovernorConfig",
    "PRESETS",
    "get_preset",
]
