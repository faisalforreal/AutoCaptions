"""Word chunking and timing engine for subtitles."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import re


@dataclass
class WordItem:
    word: str
    start: float
    end: float
    punctuated_word: str = ""
    is_keyword: bool = False

    def __post_init__(self):
        if not self.punctuated_word:
            self.punctuated_word = self.word


@dataclass
class ChunkItem:
    start: float
    end: float
    words: List[WordItem] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(w.punctuated_word for w in self.words)


# Keywords to highlight when in keyword mode (numbers, money, power words)
HIGH_IMPACT_PATTERN = re.compile(
    r"^(\$?\d+[\%kKmMbB]?|\b(never|always|best|worst|secret|million|billion|money|free|proven|stop|start|danger|win|lose|now)\b)",
    re.IGNORECASE
)


def is_high_impact_word(word: str) -> bool:
    clean = re.sub(r"[^\w\$%]", "", word)
    return bool(HIGH_IMPACT_PATTERN.search(clean))


def chunk_words(
    raw_words: List[Dict[str, Any]],
    max_words_per_chunk: int = 3,
    max_gap_seconds: float = 0.5,
    min_display_seconds: float = 0.8,
) -> List[ChunkItem]:
    """
    Groups words into short, visually readable subtitle chunks.
    Respects speech pauses and sentence endings.
    """
    if not raw_words:
        return []

    # Convert raw dicts to WordItems
    words: List[WordItem] = []
    for item in raw_words:
        w_text = str(item.get("word", "")).strip()
        p_text = str(item.get("punctuated_word", w_text)).strip()
        start = float(item.get("start", 0.0))
        end = float(item.get("end", start + 0.2))
        if not w_text:
            continue
        words.append(
            WordItem(
                word=w_text,
                punctuated_word=p_text,
                start=start,
                end=end,
                is_keyword=is_high_impact_word(w_text),
            )
        )

    if not words:
        return []

    chunks: List[ChunkItem] = []
    current_words: List[WordItem] = [words[0]]

    for i in range(1, len(words)):
        prev_w = words[i - 1]
        curr_w = words[i]
        time_gap = curr_w.start - prev_w.end

        # End of sentence detection
        ends_sentence = prev_w.punctuated_word.endswith((".", "!", "?"))

        # Decide whether to start a new chunk
        should_split = (
            len(current_words) >= max_words_per_chunk
            or time_gap > max_gap_seconds
            or ends_sentence
        )

        if should_split:
            chunk_start = current_words[0].start
            chunk_end = current_words[-1].end
            # Ensure minimum readability duration
            if (chunk_end - chunk_start) < min_display_seconds:
                chunk_end = min(curr_w.start, chunk_start + min_display_seconds)

            chunks.append(ChunkItem(start=chunk_start, end=chunk_end, words=current_words))
            current_words = [curr_w]
        else:
            current_words.append(curr_w)

    if current_words:
        chunk_start = current_words[0].start
        chunk_end = max(current_words[-1].end, chunk_start + min_display_seconds)
        chunks.append(ChunkItem(start=chunk_start, end=chunk_end, words=current_words))

    return chunks
