import os
import cv2


def crop_detected_propellers(
    image_path,
    detections,
    output_dir="outputs/propeller_crops"
):

    os.makedirs(output_dir, exist_ok=True)

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    height, width = image.shape[:2]

    cropped_results = {}

    for detection in detections:

        detection_id = detection["id"]

        x1, y1, x2, y2 = detection["bbox"]

        # Convert coordinates to integers
        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(width, int(x2))
        y2 = min(height, int(y2))

        if x2 <= x1 or y2 <= y1:
            continue

        crop = image[y1:y2, x1:x2]

        if crop.size == 0:
            continue

        crop_path = os.path.join(
            output_dir,
            f"{detection_id}.jpg"
        )

        cv2.imwrite(crop_path, crop)

        cropped_results[detection_id] = {
            "crop_path": crop_path,
            "bbox": [x1, y1, x2, y2],
            "confidence": detection["confidence"]
        }

    return cropped_results
