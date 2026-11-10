from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reference_engine.coordinate_transform import map_image_coordinates
from reference_engine.reference_config import REFERENCE_CONFIG
from reference_engine.reference_engine import run_reference_engine
from reference_engine.reference_geometry import REFERENCE_GEOMETRY
from reference_engine.verification_reports import (
    generate_correction_report,
    generate_error_report,
)


def detect_propellers(model, image_path: Path, confidence: float):
    results = model.predict(source=str(image_path), conf=confidence, verbose=False)
    result = results[0]
    detections = []
    for index, box in enumerate(result.boxes):
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
        detections.append(
            {
                "id": f"D{index + 1}",
                "center": [(x1 + x2) / 2, (y1 + y2) / 2],
                "bbox": [x1, y1, x2, y2],
                "confidence": float(box.conf[0].cpu().item()),
            }
        )
    return detections, result


def main():
    parser = argparse.ArgumentParser(
        description="Detect Pluto drone propellers and generate verification reports."
    )
    parser.add_argument("image", type=Path, help="Path to the input drone image")
    parser.add_argument("--weights", type=Path, default=ROOT / "models" / "best.pt")
    parser.add_argument(
        "--reference",
        type=Path,
        default=ROOT / "assets" / "images" / "pluto_top_reference.png",
    )
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()

    for path in (args.image, args.weights, args.reference):
        if not path.is_file():
            raise FileNotFoundError(f"Required file not found: {path}")

    args.output.mkdir(parents=True, exist_ok=True)
    from ultralytics import YOLO

    model = YOLO(str(args.weights))

    image = cv2.imread(str(args.image))
    reference_image = cv2.imread(str(args.reference))
    if image is None:
        raise ValueError(f"Could not read input image: {args.image}")
    if reference_image is None:
        raise ValueError(f"Could not read reference image: {args.reference}")

    detections, result = detect_propellers(model, args.image, args.confidence)
    reference_detections, _ = detect_propellers(model, args.reference, args.confidence)

    annotated_path = args.output / "annotated_input.jpg"
    cv2.imwrite(str(annotated_path), result.plot())

    if len(reference_detections) != 4:
        raise RuntimeError(
            "The reference image must produce exactly four propeller detections; "
            f"received {len(reference_detections)}."
        )

    reference_mapping = map_image_coordinates(reference_detections, [0, -1])
    if reference_mapping["status"] != "MAPPED":
        raise RuntimeError(
            "Could not map the reference image: " + str(reference_mapping.get("errors"))
        )

    position_to_motor = {
        "FRONT_LEFT": "FL",
        "FRONT_RIGHT": "FR",
        "REAR_LEFT": "RL",
        "REAR_RIGHT": "RR",
    }
    reference_centers_normalized = {}
    for detection_id, position in reference_mapping["mapping"].items():
        motor = position_to_motor[position]
        detection = next(d for d in reference_detections if d["id"] == detection_id)
        reference_centers_normalized[motor] = [
            detection["center"][0] / reference_image.shape[1],
            detection["center"][1] / reference_image.shape[0],
        ]

    engine_result = run_reference_engine(
        REFERENCE_CONFIG, REFERENCE_GEOMETRY, detections, [0, -1]
    )
    error_report = generate_error_report(
        detections=detections,
        engine_result=engine_result,
        reference_config=REFERENCE_CONFIG,
        appearance_scores={},
        detected_types={},
    )
    correction_report = generate_correction_report(
        detections=detections,
        engine_result=engine_result,
        image_shape=image.shape,
        reference_centers_normalized=reference_centers_normalized,
        reference_config=REFERENCE_CONFIG,
        appearance_scores={},
    )

    summary = {
        "input_image": args.image.name,
        "reference_image": args.reference.name,
        "detected_propellers": len(detections),
        "detections": detections,
        "engine_status": engine_result.get("status"),
        "motor_mapping": engine_result.get("motor_mapping", {}),
        "error_report": error_report,
        "correction_report": correction_report,
        "annotated_image": annotated_path.name,
    }
    for filename, payload in [
        ("detailed_error_report.json", error_report),
        ("correction_report.json", correction_report),
        ("drone_verification_summary.json", summary),
    ]:
        (args.output / filename).write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )

    print(
        json.dumps(
            {
                "detected_propellers": len(detections),
                "engine_status": engine_result.get("status"),
                "final_status": error_report.get("final_status"),
                "output_directory": str(args.output.resolve()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
