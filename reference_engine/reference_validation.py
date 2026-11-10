def validate_reference_config(config):

    errors = []

    expected_motors = {"FL", "FR", "RL", "RR"}

    motors = config.get("motors", {})
    drone = config.get("drone", {})

    if set(motors.keys()) != expected_motors:
        errors.append("Invalid motor positions.")

    for motor, details in motors.items():

        if details.get("propeller_type") not in ["A", "B"]:
            errors.append(
                f"{motor}: Invalid or unknown propeller type."
            )

        if not details.get("position"):
            errors.append(
                f"{motor}: Motor position missing."
            )

    # Check diagonal arrangement
    if len(motors) == 4:
        if motors["FL"]["propeller_type"] != motors["RR"]["propeller_type"]:
            errors.append("FL and RR propeller types must match.")

        if motors["FR"]["propeller_type"] != motors["RL"]["propeller_type"]:
            errors.append("FR and RL propeller types must match.")

    if drone.get("front_direction") not in ["NORTH", "SOUTH", "EAST", "WEST"]:
        errors.append("Front direction is unconfirmed.")

    return {
        "valid": len(errors) == 0,
        "configuration_status": drone.get("configuration_status", "UNKNOWN"),
        "errors": errors
    }
