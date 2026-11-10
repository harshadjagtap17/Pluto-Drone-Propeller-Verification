def validate_drone_identity(
    detected_drone,
    reference_drone="PLUTO"
):
    """
    Validate whether the detected drone identity
    matches the reference drone.
    """

    if detected_drone is None:
        return {
            "status": "UNABLE TO VERIFY",
            "error": "Drone identity is unknown"
        }

    if detected_drone.upper() != reference_drone.upper():
        return {
            "status": "FAIL",
            "error": (
                f"External or incorrect drone detected: "
                f"{detected_drone}"
            )
        }

    return {
        "status": "PASS",
        "error": None
    }
