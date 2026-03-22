import unittest

from ensemble import compute_overall


class ComputeOverallTests(unittest.TestCase):
    def test_compute_overall_handles_empty_frames(self):
        result = compute_overall([])

        self.assertEqual(result["overall_verdict"], "uncertain")
        self.assertEqual(result["overall_score"], 0.0)
        self.assertEqual(result["frame_count"], 0)
        self.assertEqual(result["top_suspicious_frames"], [])
        self.assertEqual(result["score_timeline"], [])

    def test_compute_overall_detects_mixed_video_with_strong_ai_segments(self):
        frames = [
            {
                "frame_index": 0,
                "ai_score": 0.22,
                "ml_score": 0.25,
                "signals": {"texture_uniformity": 0.30, "noise_level": 0.30},
                "verdict": "human",
            },
            {
                "frame_index": 1,
                "ai_score": 0.78,
                "ml_score": 0.92,
                "signals": {"texture_uniformity": 0.80, "noise_level": 0.80},
                "verdict": "ai",
            },
            {
                "frame_index": 2,
                "ai_score": 0.20,
                "ml_score": 0.20,
                "signals": {"texture_uniformity": 0.25, "noise_level": 0.20},
                "verdict": "human",
            },
            {
                "frame_index": 3,
                "ai_score": 0.74,
                "ml_score": 0.88,
                "signals": {"texture_uniformity": 0.78, "noise_level": 0.75},
                "verdict": "ai",
            },
            {
                "frame_index": 4,
                "ai_score": 0.24,
                "ml_score": 0.25,
                "signals": {"texture_uniformity": 0.30, "noise_level": 0.25},
                "verdict": "human",
            },
            {
                "frame_index": 5,
                "ai_score": 0.72,
                "ml_score": 0.90,
                "signals": {"texture_uniformity": 0.80, "noise_level": 0.78},
                "verdict": "ai",
            },
        ]

        result = compute_overall(frames)

        self.assertEqual(result["overall_verdict"], "ai")
        self.assertGreaterEqual(result["overall_score"], 0.50)
        self.assertEqual(result["ai_coverage"], 0.5)
        self.assertEqual(result["peak_ml_score"], 0.92)
        self.assertEqual(result["top_suspicious_frames"], [1, 3, 5])


if __name__ == "__main__":
    unittest.main()
