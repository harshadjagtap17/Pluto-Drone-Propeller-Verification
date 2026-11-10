import numpy as np


def map_image_coordinates(
    detections,
    front_direction,
    ambiguity_tolerance=1e-6
):

    if len(detections) != 4:
        return {
            "status": "UNABLE_TO_VERIFY",
            "mapping": {},
            "errors": ["Exactly four motor detections required."]
        }

    ids = [item.get("id") for item in detections]

    if None in ids or len(set(ids)) != 4:
        return {
            "status": "UNABLE_TO_VERIFY",
            "mapping": {},
            "errors": ["Missing or duplicate motor IDs."]
        }

    try:
        points = np.array([
            item["center"] for item in detections
        ], dtype=float)

        front = np.asarray(front_direction, dtype=float)

    except (KeyError, TypeError, ValueError):
        return {
            "status": "UNABLE_TO_VERIFY",
            "mapping": {},
            "errors": ["Invalid coordinate input."]
        }

    if points.shape != (4, 2) or not np.all(np.isfinite(points)):
        return {
            "status": "UNABLE_TO_VERIFY",
            "mapping": {},
            "errors": ["Invalid motor coordinates."]
        }

    magnitude = np.linalg.norm(front)

    if front.shape != (2,) or not np.isfinite(magnitude) or magnitude == 0:
        return {
            "status": "UNABLE_TO_VERIFY",
            "mapping": {},
            "errors": ["Invalid front direction."]
        }

    center = np.mean(points, axis=0)

    front = front / magnitude
    right = np.array([-front[1], front[0]])

    mapping = {}
    errors = []

    for item, point in zip(detections, points):

        relative = point - center

        x_projection = np.dot(relative, right)
        y_projection = np.dot(relative, front)

        if (
            abs(x_projection) <= ambiguity_tolerance
            or abs(y_projection) <= ambiguity_tolerance
        ):
            errors.append(
                f"{item['id']}: Ambiguous motor position."
            )
            continue

        side = "LEFT" if x_projection < 0 else "RIGHT"
        row = "FRONT" if y_projection > 0 else "REAR"

        mapping[item["id"]] = f"{row}_{side}"

    if errors:
        return {
            "status": "UNABLE_TO_VERIFY",
            "mapping": {},
            "errors": errors
        }

    if set(mapping.values()) != {
        "FRONT_LEFT",
        "FRONT_RIGHT",
        "REAR_LEFT",
        "REAR_RIGHT"
    }:
        return {
            "status": "UNABLE_TO_VERIFY",
            "mapping": {},
            "errors": ["Motor geometry is inconsistent."]
        }

    return {
        "status": "MAPPED",
        "drone_center": center.tolist(),
        "mapping": mapping,
        "errors": []
    }
