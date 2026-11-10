import unittest

from reference_engine.coordinate_transform import map_image_coordinates
from reference_engine.reference_validation import validate_reference_config
from reference_engine.reference_config import REFERENCE_CONFIG


class TestReferenceEngine(unittest.TestCase):
    def test_maps_four_quadrants(self):
        detections = [
            {"id": "D1", "center": [100, 100]},
            {"id": "D2", "center": [300, 100]},
            {"id": "D3", "center": [100, 300]},
            {"id": "D4", "center": [300, 300]},
        ]
        result = map_image_coordinates(detections, [0, -1])
        self.assertEqual(result["status"], "MAPPED")
        self.assertEqual(set(result["mapping"].values()), {
            "FRONT_LEFT", "FRONT_RIGHT", "REAR_LEFT", "REAR_RIGHT"
        })

    def test_rejects_missing_detection(self):
        result = map_image_coordinates(
            [{"id": "D1", "center": [100, 100]}], [0, -1]
        )
        self.assertEqual(result["status"], "UNABLE_TO_VERIFY")

    def test_reference_is_assumed_not_confirmed(self):
        result = validate_reference_config(REFERENCE_CONFIG)
        self.assertTrue(result["valid"])
        self.assertEqual(result["configuration_status"], "ASSUMED")


if __name__ == "__main__":
    unittest.main()
