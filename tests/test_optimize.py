import unittest
from io import BytesIO

from PIL import Image

from app import create_app
from app.routes import _effective_quality


def make_jpeg_bytes(width: int = 120, height: int = 80, color=(120, 80, 200)) -> bytes:
    image = Image.new("RGB", (width, height), color)
    output = BytesIO()
    image.save(output, format="JPEG", quality=90)
    return output.getvalue()


class QualityPresetTests(unittest.TestCase):
    def setUp(self):
        app = create_app()
        self.config = app.config

    def test_speed_preset_soft_clamps_quality(self):
        effective, note = _effective_quality(20, "speed", self.config)
        self.assertEqual(effective, 30)
        self.assertIn("softly clamps quality to 30-50", note)

    def test_speed_preset_keeps_in_range_quality(self):
        effective, note = _effective_quality(40, "speed", self.config)
        self.assertEqual(effective, 40)
        self.assertEqual(note, "")

    def test_custom_quality_uses_direct_range(self):
        effective, note = _effective_quality(120, "custom_quality", self.config)
        self.assertEqual(effective, 95)
        self.assertEqual(note, "")


class OptimizeResponseReportingTests(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_optimize_reports_dimensions_and_size_change(self):
        upload_bytes = make_jpeg_bytes(width=120, height=80)

        response = self.client.post(
            "/optimize",
            data={
                "image": (BytesIO(upload_bytes), "sample.jpg", "image/jpeg"),
                "preset": "balanced",
                "quality": "75",
                "resize_percent": "50",
                "output_format": "JPEG",
                "sharpness_balance": "0",
                "contrast": "1.0",
                "brightness": "1.0",
                "strip_metadata": "true",
                "auto_orient": "true",
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ok"])

        self.assertEqual(payload["before_width"], 120)
        self.assertEqual(payload["before_height"], 80)
        self.assertEqual(payload["after_width"], 60)
        self.assertEqual(payload["after_height"], 40)

        self.assertEqual(payload["before_size"], len(upload_bytes))
        self.assertGreater(payload["after_size"], 0)

        expected_size_change = round(
            ((payload["after_size"] - payload["before_size"]) / payload["before_size"]) * 100,
            2,
        )
        expected_reduction = round(
            ((payload["before_size"] - payload["after_size"]) / payload["before_size"]) * 100,
            2,
        )
        self.assertEqual(payload["size_change_percent"], expected_size_change)
        self.assertEqual(payload["reduction_percent"], expected_reduction)


if __name__ == "__main__":
    unittest.main()
