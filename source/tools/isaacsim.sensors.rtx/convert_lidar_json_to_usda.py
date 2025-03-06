# Copyright (c) 2025, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import argparse
import json
import os
import re
from pathlib import Path


def json_value_to_usda(value):
    """Convert a JSON value to its USDA representation."""
    if isinstance(value, str):
        # Escape quotes in strings
        escaped_value = value.replace('"', '\\"')
        return f'"{escaped_value}"'
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, list):
        # For arrays, format with up to 10 elements per line
        if len(value) <= 10:  # For short arrays, keep on one line
            items = [json_value_to_usda(item) for item in value]
            return f"[ {', '.join(items)} ]"
        else:  # For long arrays, use 10 elements per line with column alignment
            # Convert all items to their string representations first
            items = [json_value_to_usda(item) for item in value]

            # Find the maximum width needed for any element in the entire array
            max_width = max(len(item) for item in items) if items else 0

            chunks = []
            # Process the array in chunks of 10 elements
            for i in range(0, len(items), 10):
                chunk = items[i : i + 10]

                # Pad each element with spaces to align columns
                # Use the global max width for consistent alignment across all rows
                padded_chunk = [item.rjust(max_width) for item in chunk]
                chunks.append(", ".join(padded_chunk))

            return "[\n            " + ",\n            ".join(chunks) + "\n        ]"
    elif value is None:
        return "None"
    else:
        return f'"{str(value)}"'


# Schema-defined attribute types based on generatedSchema.usda
SCHEMA_ATTRIBUTE_TYPES = {
    # Core sensor attributes
    "modelName": "string",
    "tickRate": "float",
    # LiDAR core attributes
    "class": "string",
    "type": "string",
    "name": "string",
    "driveWorksId": "string",
    # Emitter state attributes from OmniSensorGenericLidarCoreEmitterStateAPI
    "azimuthDeg": "float[]",
    "elevationDeg": "float[]",
    "fireTimeNs": "float[]",
    "bank": "float[]",
    "isROIState": "bool[]",
    "timeOffsetNs": "float[]",
    # Other LiDAR attributes commonly found in configs
    "intensityMappingType": "string",
    "horizontalResolution": "uint",
    "verticalChannels": "uint",
    "rotationRate": "float",
    "fieldOfView": "float",
    "range": "float",
    "horizontalFOV": "float",
    "verticalFOV": "float",
    "minRange": "float",
    "maxRange": "float",
    "horizontalBeams": "uint",
    "verticalBeams": "uint",
    "minAzimuthDeg": "float",
    "maxAzimuthDeg": "float",
    "minElevationDeg": "float",
    "maxElevationDeg": "float",
}


def get_schema_type(key):
    """Get the type from schema for a given attribute key."""
    # Extract the base attribute name (last part after colon)
    base_key = key.split(":")[-1]
    return SCHEMA_ATTRIBUTE_TYPES.get(base_key)


def get_usd_type(value, key=None):
    """Determine the USD type for a given value, using schema if key is known."""
    # First check if we have a schema-defined type for this key
    if key is not None:
        schema_type = get_schema_type(key)
        if schema_type:
            return schema_type

    # Fall back to auto-detection for unknown attributes
    if isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        if value >= 0:
            return "uint"
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        return "string"
    elif isinstance(value, list):
        if not value:  # Empty list
            return "float[]"  # Default for empty arrays

        # First check if we have a schema-defined type for this array
        if key is not None:
            schema_type = get_schema_type(key)
            if schema_type and schema_type.endswith("[]"):
                return schema_type

        # Auto-detect array type
        if all(isinstance(x, bool) for x in value):
            return "bool[]"
        elif all(isinstance(x, int) and x >= 0 for x in value):
            return "uint[]"
        elif all(isinstance(x, int) for x in value):
            return "int[]"
        elif all(isinstance(x, float) for x in value):
            return "float[]"
        elif all(isinstance(x, str) for x in value):
            return "string[]"

        # Mixed or complex list, default to float[] for numeric data
        if all(isinstance(x, (int, float)) for x in value):
            return "float[]"

        return "string[]"  # Default for mixed content
    else:
        return "string"  # Default fallback


def flatten_json(json_obj, prefix="", result=None, skip_emitter_states=False):
    """Flatten nested JSON into dot-notation key-value pairs."""
    if result is None:
        result = {}

    for key, value in json_obj.items():
        # Skip comment fields for cleaner output
        if "comment" in key.lower():
            continue

        # Skip emitterStates if requested (we'll handle them separately)
        if skip_emitter_states and key == "emitterStates":
            continue

        new_key = f"{prefix}:{key}" if prefix else key

        if isinstance(value, dict):
            flatten_json(value, new_key, result, skip_emitter_states)
        else:
            result[new_key] = value

    return result


def sanitize_name(name):
    """Replace special characters with underscores and consolidate multiple underscores."""
    # Replace special characters with underscores
    sanitized = re.sub(r"[^a-zA-Z0-9]", "_", name)

    # Replace multiple consecutive underscores with a single underscore
    sanitized = re.sub(r"_+", "_", sanitized)

    return sanitized


def convert_json_to_usda(json_path, usda_path):
    with open(json_path, "r") as f:
        config = json.load(f)

    base_name = os.path.splitext(os.path.basename(json_path))[0]

    # Extract model name from 'profile' section or the root 'name' field as fallback
    profile = config.get("profile", {})
    model_name = profile.get("name", config.get("name", "UnknownLidar"))

    # Sanitize the model name for USD compatibility
    model_name_with_underscores = sanitize_name(model_name)

    # Extract tick rate from name (e.g., "10hz" -> 10)
    tick_rate = 10  # default
    for part in model_name.split():
        if "hz" in part.lower():
            try:
                tick_rate = int(part.lower().replace("hz", ""))
                break
            except ValueError:
                pass

    # Only flatten and convert fields from the 'profile' section
    # Skip emitterStates as we'll handle them separately
    flattened = {}
    if "profile" in config:
        flattened = flatten_json(profile, skip_emitter_states=True)

    # Generate attributes, handle special cases and name conflicts
    attributes = []
    for key, value in flattened.items():
        # Transform JSON key to USD format
        usd_key = f"omni:sensor:Core:{key}"
        usd_value = json_value_to_usda(value)
        usd_type = get_usd_type(value, key)
        attributes.append(f"        {usd_type} {usd_key} = {usd_value}")

    # Handle emitter states as attributes on the main prim
    emitter_states = []
    try:
        emitter_states = profile.get("emitterStates", [])
    except (KeyError, AttributeError):
        pass

    # Process each emitter state separately
    for i, state in enumerate(emitter_states):
        for key, value in state.items():
            # Skip comment fields
            if "comment" in key.lower():
                continue

            # Format: emitterState:s{NNN}:{property}
            # Where NNN is a 3-digit number with leading zeros
            emitter_key = f"emitterState:s{i+1:03d}:{key}"
            usd_key = f"omni:sensor:Core:{emitter_key}"

            # Get schema-defined type or auto-detect
            schema_type = get_schema_type(key)

            if schema_type:
                # Use schema-defined type
                usd_type = schema_type

                # Convert single values to arrays for array types
                if isinstance(value, (int, float, bool, str)) and usd_type.endswith("[]"):
                    usd_value = json_value_to_usda([value])
                else:
                    usd_value = json_value_to_usda(value)

                attributes.append(f"        {usd_type} {usd_key} = {usd_value}")
            else:
                # Auto-detect type for unknown attributes
                if isinstance(value, list):
                    usd_value = json_value_to_usda(value)
                    usd_type = get_usd_type(value)
                    attributes.append(f"        {usd_type} {usd_key} = {usd_value}")
                else:
                    # Single values should be arrays in emitter state context
                    usd_value = json_value_to_usda([value])
                    element_type = get_usd_type(value)
                    if element_type == "uint":
                        usd_type = "uint[]"
                    else:
                        usd_type = f"{element_type}[]"
                    attributes.append(f"        {usd_type} {usd_key} = {usd_value}")

    attributes_text = "\n".join(attributes)

    usda_content = f"""#usda 1.0
(
    doc = "Generated from {os.path.basename(json_path)}"
    defaultPrim = "Lidar"
)

def Xform "Lidar"
{{
    def OmniLidar "{model_name_with_underscores}" (
        prepend apiSchemas = ["OmniSensorGenericLidarCoreAPI"]
    )
    {{
        string omni:sensor:modelName = "{model_name_with_underscores}"
        float omni:sensor:tickRate = {tick_rate}

        # Configuration parameters from JSON
{attributes_text}
    }}
}}
"""
    with open(usda_path, "w") as f:
        f.write(usda_content)


def convert_single_json(json_path):
    """Convert a single JSON file to USDA."""
    json_path = Path(json_path)
    usda_path = json_path.with_suffix(".usda")
    convert_json_to_usda(json_path, usda_path)
    return usda_path


def process_lidar_configs(config_dir):
    """Process all JSON files in a directory and convert them to USDA."""
    config_path = Path(config_dir)
    converted_files = []
    for json_file in config_path.glob("**/*.json"):
        usda_path = json_file.with_suffix(".usda")
        convert_json_to_usda(json_file, usda_path)
        converted_files.append(usda_path)
        print(f"Generated: {usda_path}")
    return converted_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert LiDAR configuration JSON files to USDA file containing OmniLidar prim."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dir", "-d", help="Directory containing JSON files to convert")
    group.add_argument("--files", "-f", nargs="+", help="Specific JSON files to convert")

    args = parser.parse_args()

    if args.dir:
        # Process all files in directory
        process_lidar_configs(args.dir)
    else:
        # Process specific files
        for json_file in args.files:
            usda_path = convert_single_json(json_file)
            print(f"Generated: {usda_path}")
