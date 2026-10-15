import unittest
from caption_tool.config import CaptionStyle, hex_to_ass_color
from caption_tool.chunker import ChunkItem, WordItem
from caption_tool.ass_builder import format_ass_time, build_ass_script, make_rounded_rect_path
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

    def test_rounded_box_badge_generation(self):
        style = get_preset("boxed_red_accent")
        style.position = "middle"
        style.has_box = True
        style.box_rounded = True
        
        chunk = ChunkItem(
            start=1.0,
            end=3.0,
            words=[
                WordItem("DYNAMIC", 1.0, 2.0, "DYNAMIC"),
                WordItem("BADGE", 2.0, 3.0, "BADGE"),
            ]
        )
        ass_script = build_ass_script([chunk], style, play_res_x=1080, play_res_y=1920)
        
        # Verify both Text (Default) and BoxBadge styles are created
        self.assertIn("Style: Default,", ass_script)
        self.assertIn("Style: BoxBadge,", ass_script)

        # Layer 0 must contain the vector drawing for the rounded badge
        self.assertIn("Dialogue: 0,0:00:01.00,0:00:03.00,BoxBadge", ass_script)
        self.assertIn(r"\p1", ass_script)
        self.assertIn(r"\p0", ass_script)

        # Layer 1 must contain the centered text
        self.assertIn("Dialogue: 1,", ass_script)
        self.assertIn(r"\pos(540.0,960.0)", ass_script)

    def test_classic_square_box_style(self):
        style = get_preset("boxed_red_accent")
        style.position = "middle"
        style.has_box = True
        style.box_rounded = False
        
        ass_script = build_ass_script([], style, play_res_x=1080, play_res_y=1920)
        
        # Check alignment 5 (middle center) and BorderStyle 3 (opaque square box)
        self.assertIn(",3,", ass_script)
        self.assertIn(",5,", ass_script)

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
        self.assertIn("0:00:01.00,0:00:01.50,Default", ass_script)
        self.assertIn(r"{\c&H002020FF&}HELLO{\c&H00FFFFFF&} WORLD", ass_script)
        self.assertIn("0:00:01.50,0:00:02.50,Default", ass_script)
        self.assertIn(r"HELLO {\c&H002020FF&}WORLD{\c&H00FFFFFF&}", ass_script)

    def test_make_rounded_rect_path(self):
        path = make_rounded_rect_path(400, 100, 20)
        self.assertTrue(path.startswith("m 20.0 0"))
        # Must contain cubic bezier commands
        self.assertIn(" b ", path)


if __name__ == "__main__":
    unittest.main()
