from .reference_validation import validate_reference_config
from .reference_geometry import validate_geometry
from .coordinate_transform import map_image_coordinates


POSITION_TO_MOTOR = {
    "FRONT_LEFT": "FL",
    "FRONT_RIGHT": "FR",
    "REAR_LEFT": "RL",
    "REAR_RIGHT": "RR"
}


def run_reference_engine(
    reference_config,
    reference_geometry,
    detected_motors,
    front_direction
):

    # Step 1: Validate reference configuration
    config_check = validate_reference_config(reference_config)

    if not config_check["valid"]:
        return {
            "status": "REFERENCE_INVALID",
            "errors": config_check["errors"]
        }

    # Step 2: Validate reference geometry
    geometry_check = validate_geometry(reference_geometry)

    if not geometry_check["valid"]:
        return {
            "status": "REFERENCE_INVALID",
            "errors": geometry_check["errors"]
        }

    # Step 3: Map detected propellers to motor positions
    mapping = map_image_coordinates(
        detected_motors,
        front_direction
    )

    if mapping["status"] != "MAPPED":
        return {
            "status": "UNABLE_TO_VERIFY",
            "errors": mapping["errors"]
        }

    # Step 4: Convert mapped positions to motor IDs
    motor_mapping = {
        detection_id: POSITION_TO_MOTOR[position]
        for detection_id, position in mapping["mapping"].items()
    }

    return {
        "status": "MAPPING_SUCCESSFUL",
        "drone_center": mapping["drone_center"],
        "motor_mapping": motor_mapping,
        "reference_status": reference_config.get(
            "verification_status",
            reference_config.get("drone", {}).get("configuration_status", "UNKNOWN")
        )
    }
