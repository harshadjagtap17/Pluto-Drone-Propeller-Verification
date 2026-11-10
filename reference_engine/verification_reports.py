import json


EXPECTED_MOTORS = ["FL", "FR", "RL", "RR"]


def _get_motor_mapping(engine_result):
    """
    Convert detection-to-motor mapping into motor-to-detection mapping.
    """
    mapping = engine_result.get("motor_mapping", {})

    return {
        motor: detection_id
        for detection_id, motor in mapping.items()
    }


def generate_error_report(
    detections,
    engine_result,
    reference_config,
    appearance_scores=None,
    detected_types=None,
    similarity_threshold=0.70,
    confidence_threshold=0.50
):
    """
    Generate a detailed installation error report.

    appearance_scores:
        {"FL": 0.90, "FR": 0.85, ...}

    detected_types:
        {"FL": "A", "FR": "B", ...}
    """

    appearance_scores = appearance_scores or {}
    detected_types = detected_types or {}

    errors = []
    warnings = []

    motor_mapping = _get_motor_mapping(engine_result)

    detection_lookup = {
        item["id"]: item for item in detections
    }

    # 1. Check detection count
    if len(detections) < 4:
        errors.append({
            "parameter": "Propeller count",
            "expected": 4,
            "detected": len(detections),
            "affected_motor": "UNKNOWN",
            "reason": "One or more propellers were not detected.",
            "severity": "HIGH",
            "recommendation": "Inspect the missing or obstructed propeller."
        })

    elif len(detections) > 4:
        errors.append({
            "parameter": "Propeller count",
            "expected": 4,
            "detected": len(detections),
            "affected_motor": "UNKNOWN",
            "reason": "Additional propeller detections were found.",
            "severity": "HIGH",
            "recommendation": "Inspect possible false-positive detections."
        })

    # 2. Check motor position mapping
    for motor in EXPECTED_MOTORS:

        detection_id = motor_mapping.get(motor)

        if detection_id is None:
            errors.append({
                "parameter": "Motor position",
                "expected": motor,
                "detected": "MISSING",
                "affected_motor": motor,
                "reason": f"No detected propeller was mapped to {motor}.",
                "severity": "HIGH",
                "recommendation": f"Inspect the {motor} motor and propeller."
            })
            continue

        detection = detection_lookup.get(detection_id)

        if detection is None:
            errors.append({
                "parameter": "Motor mapping",
                "expected": motor,
                "detected": detection_id,
                "affected_motor": motor,
                "reason": "Mapped detection ID was not found.",
                "severity": "HIGH",
                "recommendation": "Recheck YOLO detections and coordinate mapping."
            })
            continue

        confidence = float(detection.get("confidence", 0))

        if confidence < confidence_threshold:
            errors.append({
                "parameter": "Detection confidence",
                "expected": f">= {confidence_threshold}",
                "detected": round(confidence, 3),
                "affected_motor": motor,
                "reason": "Detection confidence is below the configured threshold.",
                "severity": "MEDIUM",
                "recommendation": "Capture a clearer image and inspect this propeller."
            })

    # 3. Check appearance similarity
    for motor, score_data in appearance_scores.items():

        score = (
            score_data.get("similarity")
            if isinstance(score_data, dict)
            else score_data
        )

        if score is None:
            continue

        score = float(score)

        if score < similarity_threshold:
            errors.append({
                "parameter": "Propeller appearance",
                "expected": f">= {similarity_threshold:.2f}",
                "detected": round(score, 3),
                "affected_motor": motor,
                "reason": "Propeller appearance differs from its reference.",
                "severity": "HIGH",
                "recommendation": "Inspect blade shape, propeller condition and installation."
            })

    # 4. Check A/B propeller type
    for motor, detected_type in detected_types.items():

        expected_type = (
            reference_config.get("motors", {})
            .get(motor, {})
            .get("propeller_type")
        )

        if detected_type is None:
            continue

        if expected_type != detected_type:
            errors.append({
                "parameter": "Propeller type",
                "expected": expected_type,
                "detected": detected_type,
                "affected_motor": motor,
                "reason": "Detected propeller type differs from the reference configuration.",
                "severity": "HIGH",
                "recommendation": f"Check the propeller type installed at {motor}."
            })

    # 5. Configuration confidence warning
    config_status = reference_config.get(
        "drone", {}
    ).get("configuration_status", "UNKNOWN")

    if config_status != "CONFIRMED":
        warnings.append(
            "Reference configuration is ASSUMED or unconfirmed. "
            "A/B propeller and rotation checks cannot be treated as "
            "manufacturer-verified."
        )

    # 6. Overall result
    if errors:
        final_status = "FAIL"
    elif engine_result.get("status") != "MAPPING_SUCCESSFUL":
        final_status = "UNABLE TO VERIFY"
    elif config_status != "CONFIRMED":
        final_status = "UNABLE TO VERIFY"
    else:
        final_status = "PASS"

    return {
        "report_type": "DETAILED ERROR REPORT",
        "drone": reference_config.get("drone", {}).get("model", "UNKNOWN"),
        "final_status": final_status,
        "total_errors": len(errors),
        "total_warnings": len(warnings),
        "errors": errors,
        "warnings": warnings
    }


def generate_correction_report(
    detections,
    engine_result,
    image_shape,
    reference_centers_normalized,
    reference_config,
    appearance_scores=None,
    similarity_threshold=0.70
):
    """
    Calculate image-coordinate corrections.

    reference_centers_normalized:
        {
            "FL": (x_normalized, y_normalized),
            "FR": (x_normalized, y_normalized),
            "RL": (x_normalized, y_normalized),
            "RR": (x_normalized, y_normalized)
        }

    Normalized coordinates range from 0 to 1.
    """

    height, width = image_shape[:2]

    motor_mapping = _get_motor_mapping(engine_result)

    detection_lookup = {
        item["id"]: item for item in detections
    }

    appearance_scores = appearance_scores or {}

    corrections = []

    for motor in EXPECTED_MOTORS:

        detection_id = motor_mapping.get(motor)

        if detection_id is None:
            corrections.append({
                "motor": motor,
                "status": "NOT DETECTED",
                "correction": "Physical inspection required",
                "reason": "No propeller was mapped to this motor."
            })
            continue

        detection = detection_lookup.get(detection_id)

        if detection is None:
            continue

        if motor not in reference_centers_normalized:
            corrections.append({
                "motor": motor,
                "status": "UNABLE TO CALCULATE",
                "correction": "Reference coordinates unavailable",
                "reason": "No normalized reference position was supplied."
            })
            continue

        # Actual propeller center
        actual_x, actual_y = detection["center"]

        # Convert actual coordinates to normalized coordinates
        actual_x_norm = actual_x / width
        actual_y_norm = actual_y / height

        # Expected reference center
        ref_x_norm, ref_y_norm = reference_centers_normalized[motor]

        # Calculate correction vector
        dx_norm = ref_x_norm - actual_x_norm
        dy_norm = ref_y_norm - actual_y_norm

        dx_pixels = dx_norm * width
        dy_pixels = dy_norm * height

        distance_pixels = (
            dx_pixels ** 2 + dy_pixels ** 2
        ) ** 0.5

        distance_percent = (
            distance_pixels /
            ((width ** 2 + height ** 2) ** 0.5)
        ) * 100

        score_data = appearance_scores.get(motor)

        appearance_score = (
            score_data.get("similarity")
            if isinstance(score_data, dict)
            else score_data
        )

        appearance_issue = (
            appearance_score is not None
            and float(appearance_score) < similarity_threshold
        )

        if distance_pixels > 0:
            status = "POSITION DEVIATION"
        else:
            status = "POSITION ALIGNED"

        if appearance_issue:
            correction = (
                "Inspect propeller type, blade shape and physical installation. "
                "Image-coordinate correction cannot fix appearance mismatch."
            )
        elif distance_pixels > 0:
            correction = (
                "Align the propeller with the reference position, "
                "after confirming both images have matching orientation "
                "and perspective."
            )
        else:
            correction = "No positional correction indicated."

        corrections.append({
            "motor": motor,
            "status": status,
            "actual_center_pixels": [
                round(actual_x, 2),
                round(actual_y, 2)
            ],
            "expected_center_normalized": [
                round(ref_x_norm, 4),
                round(ref_y_norm, 4)
            ],
            "correction_x_pixels": round(dx_pixels, 2),
            "correction_y_pixels": round(dy_pixels, 2),
            "correction_distance_pixels": round(distance_pixels, 2),
            "correction_distance_percent": round(distance_percent, 2),
            "appearance_similarity": appearance_score,
            "recommended_action": correction
        })

    return {
        "report_type": "CORRECTION REPORT",
        "drone": reference_config.get("drone", {}).get("model", "UNKNOWN"),
        "coordinate_unit": "pixels",
        "physical_measurement_available": False,
        "corrections": corrections
    }


def print_verification_reports(error_report, correction_report):

    print("\n" + "=" * 55)
    print("DETAILED INSTALLATION ERROR REPORT")
    print("=" * 55)

    print("Drone:", error_report["drone"])
    print("Final status:", error_report["final_status"])
    print("Total errors:", error_report["total_errors"])

    for index, error in enumerate(error_report["errors"], 1):

        print(f"\nERROR {index}")
        print("Parameter:", error["parameter"])
        print("Affected motor:", error["affected_motor"])
        print("Expected:", error["expected"])
        print("Detected:", error["detected"])
        print("Reason:", error["reason"])
        print("Severity:", error["severity"])
        print("Recommendation:", error["recommendation"])

    for warning in error_report["warnings"]:
        print("\nWARNING:", warning)

    print("\n" + "=" * 55)
    print("INSTALLATION CORRECTION REPORT")
    print("=" * 55)

    for item in correction_report["corrections"]:

        print("\nMotor:", item["motor"])
        print("Status:", item["status"])

        if "correction_distance_pixels" in item:
            print("X correction:", item["correction_x_pixels"], "pixels")
            print("Y correction:", item["correction_y_pixels"], "pixels")
            print("Total correction:", item["correction_distance_pixels"], "pixels")
            print("Correction percentage:", item["correction_distance_percent"], "%")

        print("Recommended action:", item.get("recommended_action", item.get("correction")))
