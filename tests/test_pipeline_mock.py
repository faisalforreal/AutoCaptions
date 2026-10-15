import os
import subprocess
import tempfile
import unittest
from caption_tool.agent_tool import VideoCaptionAgentTool


class TestPipelineMock(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="caption_test_pipeline_")
        cls.test_video = os.path.join(cls.temp_dir, "synthetic_input.mp4")
        cls.output_video = os.path.join(cls.temp_dir, "synthetic_captioned.mp4")

        # Generate a small 2-second synthetic MP4 video with sine audio
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=2:size=640x360:rate=25",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac",
            cls.test_video
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to generate test synthetic video: {res.stderr}")

    @classmethod
    def tearDownClass(cls):
        import shutil
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_mock_end_to_end_burn(self):
        tool = VideoCaptionAgentTool()
        result = tool.process(
            video_path=self.test_video,
            output_path=self.output_video,
            style_preset="boxed_red_accent",
            position="middle",
            mock=True,
            cpu_threads=2,
        )

        self.assertEqual(result["status"], "success")
        self.assertTrue(os.path.isfile(self.output_video))
        self.assertGreater(os.path.getsize(self.output_video), 1000)
        self.assertEqual(result["position"], "middle")
        self.assertEqual(result["style_applied"], "boxed_red_accent")


if __name__ == "__main__":
    unittest.main()
