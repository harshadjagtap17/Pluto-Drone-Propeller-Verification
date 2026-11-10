import numpy as np

REFERENCE_GEOMETRY = {
    "FL": {"x": -1.0, "y": 1.0},
    "FR": {"x": 1.0, "y": 1.0},
    "RL": {"x": -1.0, "y": -1.0},
    "RR": {"x": 1.0, "y": -1.0}
}


def calculate_drone_center(geometry):

    points = np.array([
        [data["x"], data["y"]]
        for data in geometry.values()
    ], dtype=float)

    return np.mean(points, axis=0)


def validate_geometry(geometry):

    required = {"FL", "FR", "RL", "RR"}

    if not isinstance(geometry, dict):
        return {"valid": False, "errors": ["Invalid geometry."]}

    if set(geometry.keys()) != required:
        return {"valid": False, "errors": ["Invalid motor positions."]}

    try:
        points = {
            motor: np.array([data["x"], data["y"]], dtype=float)
            for motor, data in geometry.items()
        }
    except (KeyError, TypeError, ValueError):
        return {"valid": False, "errors": ["Invalid coordinates."]}

    errors = []

    if not all(np.all(np.isfinite(p)) for p in points.values()):
        errors.append("Non-finite coordinates.")

    if errors:
        return {"valid": False, "errors": errors}

    if not (
        points["FL"][1] > points["RL"][1]
        and points["FR"][1] > points["RR"][1]
        and points["FL"][0] < points["FR"][0]
        and points["RL"][0] < points["RR"][0]
    ):
        errors.append("Motor geometry orientation invalid.")

    center = np.mean(list(points.values()), axis=0)

    if not np.allclose(center, [0, 0], atol=1e-6):
        errors.append("Geometry is not centred at origin.")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
