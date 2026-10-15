import unittest
from caption_tool.chunker import chunk_words, is_high_impact_word, ChunkItem


class TestChunker(unittest.TestCase):

    def test_basic_chunking(self):
        raw = [
            {"word": "This", "start": 0.0, "end": 0.3},
            {"word": "is", "start": 0.35, "end": 0.5},
            {"word": "a", "start": 0.55, "end": 0.65},
            {"word": "test", "start": 0.70, "end": 1.0},
        ]
        chunks = chunk_words(raw, max_words_per_chunk=3)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(len(chunks[0].words), 3)
        self.assertEqual(len(chunks[1].words), 1)

    def test_pause_splitting(self):
        raw = [
            {"word": "First", "start": 0.0, "end": 0.3},
            # Gap of 1.2 seconds > 0.5s pause threshold
            {"word": "Second", "start": 1.5, "end": 1.8},
        ]
        chunks = chunk_words(raw, max_words_per_chunk=3, max_gap_seconds=0.5)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].words[0].word, "First")
        self.assertEqual(chunks[1].words[0].word, "Second")

    def test_sentence_end_splitting(self):
        raw = [
            {"word": "Stop.", "punctuated_word": "Stop.", "start": 0.0, "end": 0.3},
            {"word": "Now", "punctuated_word": "Now", "start": 0.35, "end": 0.6},
        ]
        chunks = chunk_words(raw, max_words_per_chunk=3)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].words[0].word, "Stop.")
        self.assertEqual(chunks[1].words[0].word, "Now")

    def test_high_impact_word_detection(self):
        self.assertTrue(is_high_impact_word("$100"))
        self.assertTrue(is_high_impact_word("50%"))
        self.assertTrue(is_high_impact_word("million"))
        self.assertTrue(is_high_impact_word("secret"))
        self.assertFalse(is_high_impact_word("the"))
        self.assertFalse(is_high_impact_word("and"))


if __name__ == "__main__":
    unittest.main()
