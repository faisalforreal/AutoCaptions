import unittest
from caption_tool.config import CaptionStyle, hex_to_ass_color
from caption_tool.chunker import ChunkItem, WordItem
from caption_tool.ass_builder import format_ass_time, build_ass_script
from caption_tool.presets import get_preset


class TestASSBuilder(unittest.TestCase):

    def test_hex_to_ass_color(self):
        # Pure White (#FFFFFF) -> &H00FFFFFF&
        self.assertEqual(hex_to_ass_color("#FFFFFF"), "&H00FFFFFF&")
        
        # Vibrant Red (#FF2020) -> BGR order: Blue=20, Green=20, Red=FF -> &H002020FF&
        self.assertEqual(hex_to_ass_color("#FF2020"), "&H002020FF&")

        # Neon Green (#00FF66) -> Blue=66, Green=FF, Red=00 -> &H0066FF00&
        self.assertEqual(hex_to_ass_color("#00FF66"), "&H0066FF00&")

        # Opacity test: 0.0 opacity -> alpha FF (255)
        self.assertEqual(hex_to_ass_color("#FFFFFF", opacity=0.0), "&HFFFFFFFF&")

    def test_format_ass_time(self):
        self.assertEqual(format_ass_time(0.0), "0:00:00.00")
        self.assertEqual(format_ass_time(1.25), "0:00:01.25")
        self.assertEqual(format_ass_time(65.5), "0:01:05.50")

    def test_middle_alignment_and_box_style(self):
        style = get_preset("boxed_red_accent")
        style.position = "middle"
        style.has_box = True
        
        ass_script = build_ass_script([], style, play_res_x=1080, play_res_y=1920)
        
        # Check alignment 5 (middle center)
        self.assertIn(",3,", ass_script)  # BorderStyle 3 (Box)
        self.assertIn(",5,", ass_script)  # Alignment 5 (Middle Center)

    def test_dynamic_word_highlighting_events(self):
        style = get_preset("boxed_red_accent")
        chunk = ChunkItem(
            start=1.0,
            end=2.5,
            words=[
                WordItem("HELLO", 1.0, 1.5, "HELLO"),
                WordItem("WORLD", 1.5, 2.5, "WORLD"),
            ]
        )
        ass_script = build_ass_script([chunk], style, play_res_x=1080, play_res_y=1920)

        # Dialogue lines should contain color switch tag {\c&H...&}
        self.assertIn("Dialogue: 0,0:00:01.00,0:00:01.50,Default", ass_script)
        self.assertIn(r"{\c&H002020FF&}HELLO{\c&H00FFFFFF&} WORLD", ass_script)
        self.assertIn("Dialogue: 0,0:00:01.50,0:00:02.50,Default", ass_script)
        self.assertIn(r"HELLO {\c&H002020FF&}WORLD{\c&H00FFFFFF&}", ass_script)


if __name__ == "__main__":
    unittest.main()
