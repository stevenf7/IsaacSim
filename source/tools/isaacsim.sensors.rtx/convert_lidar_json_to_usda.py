# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import json
import os
import re
from pathlib import Path


def json_value_to_usda(value, usd_type):
    """Convert a JSON value to its USD representation.

    Args:
        value (Any): The value to convert
        usd_type (str): The USD type to convert to

    Returns:
        str: The USD representation of the value
    """
    # Handle array types first
    if usd_type.endswith("[]"):
        if not value:
            return "[]"
        element_type = usd_type[:-2]  # Remove [] suffix
        elements = [json_value_to_usda(x, element_type) for x in value]

        # If array has more than 10 elements, format with line breaks
        if len(elements) > 10:
            # Find the maximum width needed for each element
            max_width = max(len(str(e)) for e in elements)

            # Format elements into groups of 10
            lines = []
            for i in range(0, len(elements), 10):
                group = elements[i : i + 10]
                # Pad each element to max_width and join with commas
                padded = [str(e).rjust(max_width) for e in group]
                lines.append(", ".join(padded))

            # Join lines with newlines and proper indentation
            array_content = ",\n        ".join(lines)
            return f"[\n        {array_content}\n    ]"
        else:
            # For short arrays, keep them on one line
            return f"[{', '.join(elements)}]"

    # Handle scalar types
    if usd_type == "uint":
        # Convert any number to integer for uint type
        return str(int(value))
    elif usd_type == "float":
        return str(value)
    elif usd_type == "bool":
        return "1" if value else "0"
    elif usd_type == "token":  # Convert token values to uppercase
        return f'"{str(value).upper()}"'
    else:  # string type
        return f'"{str(value)}"'


# Schema-defined attribute types based on generatedSchema.usda
SCHEMA_ATTRIBUTE_TYPES = {
    # Core sensor attributes from OmniSensorAPI
    "modelName": "string",
    "marketName": "string",
    "modelVendor": "string",
    "modelVersion": "string",
    "tickRate": "float",
    # Token attributes from schema
    "purpose": "token",  # allowedTokens = ["default", "render", "proxy", "guide"]
    "visibility": "token",  # allowedTokens = ["inherited", "invisible"]
    "xformOpOrder": "token[]",
    # Attributes from OmniSensorGenericLidarCoreAPI
    "aspectRatio": "float",
    "auxOutputType": "token",  # allowedTokens = ["NONE", "BASIC", "EXTRA", "FULL"]
    "avgPowerW": "float",
    "azimuthErrorMean": "float",
    "azimuthErrorStd": "float",
    "beamWaistHorM": "float",
    "beamWaistVerM": "float",
    "bitDepthResolution": "float",
    "calibrationGain": "float",
    "customFrameOfReferenceTrafo": "float[]",
    "divergenceHorDeg": "float",
    "divergenceVerDeg": "float",
    "effectiveApertureSizeM": "float",
    "elementsCoordsType": "token",  # allowedTokens = ["CARTESIAN", "SPHERICAL"]
    "elevationErrorMean": "float",
    "elevationErrorStd": "float",
    "emitterStatesFile": "string",
    "farRangeM": "float",
    "focusDistM": "float",
    "intensityMappingDecoding": "float[]",
    "intensityMappingEncoding": "float[]",
    "intensityMappingType": "token",  # allowedTokens = ["LINEAR", "NONLINEAR", "NONLINEAR_ENCODING_ONLY", "NONLINEAR_DECODING_ONLY"]
    "intensityProcessing": "token",  # allowedTokens = ["RAW", "NORMALIZATION", "CORRECTION"]
    "intensityScalePercent": "float",
    "maxAzimuthROI": "float",
    "maxReturns": "uint",
    "minAzimuthROI": "float",
    "minDistBetweenEchosM": "float",
    "minReflectance": "float",
    "minReflectionRangeM": "float",
    "Msquared": "float",
    "nearRangeM": "float",
    "numberOfChannels": "uint",
    "numberOfEmitters": "uint",
    "numLines": "uint",
    "numRaysPerLine": "uint[]",
    "originErrorMean": "float[]",
    "originErrorStd": "float[]",
    "outputFrameOfReference": "token",  # allowedTokens = ["SENSOR", "WORLD", "CUSTOM"]
    "outputMotionCompensationState": "token",  # allowedTokens = ["NONCOMPENSATED", "COMPENSATED"]
    "pixelPitch": "float",
    "pulseTimeNs": "uint",
    "quantumEfficiency": "float",
    "rangeAccuracyM": "float",
    "rangeCount": "uint",
    "rangeOffsetM": "float",
    "rangeResolutionM": "float",
    "rangesMaxM": "float[]",
    "rangesMinM": "float[]",
    "rayType": "token",  # allowedTokens = ["IDEALIZED", "GAUSSIAN_BEAM", "UNIFORM_BEAM"]
    "reflectionPowerFraction": "float",
    "reportRateBaseHz": "uint",
    "rotationDirection": "token",  # allowedTokens = ["CW", "CCW"]
    "scanRateBaseHz": "uint",
    "scanType": "token",  # allowedTokens = ["ROTARY", "SOLID_STATE"]
    "skipDroppingInvalidPoints": "bool",
    "startAzimuthOffsetDeg": "float",
    "stateResolutionStep": "uint",
    "transmissionPowerFraction": "float",
    "validEndAzimuthDeg": "float",
    "validStartAzimuthDeg": "float",
    "waveLengthNm": "float",
    # Emitter state attributes from OmniSensorGenericLidarCoreEmitterStateAPI
    "azimuthDeg": "float[]",
    "bank": "uint[]",
    "channelId": "uint[]",
    "distanceCorrectionM": "float[]",
    "elevationDeg": "float[]",
    "fireTimeNs": "uint[]",
    "focalDistM": "float[]",
    "focalSlope": "float[]",
    "horOffsetM": "float[]",
    "isROIState": "bool",
    "rangeId": "uint[]",
    "reportRateDiv": "float[]",
    "roi": "bool[]",
    "vertOffsetM": "float[]",
}


def get_schema_type(key):
    """Get the type from schema for a given attribute key."""
    # Extract the base attribute name (last part after colon)
    base_key = key.split(":")[-1]
    return SCHEMA_ATTRIBUTE_TYPES.get(base_key)


def get_usd_type(key, value):
    """Get the USD type for a given key-value pair.

    Args:
        key (str): The attribute key
        value (Any): The attribute value

    Returns:
        str: The USD type for this attribute
    """
    # Check schema first using base key (last part after colon)
    base_key = key.split(":")[-1]
    schema_type = SCHEMA_ATTRIBUTE_TYPES.get(base_key)
    if schema_type:
        return schema_type

    # For values not in schema, infer type based on Python type
    if isinstance(value, bool):
        return "bool"
    elif isinstance(value, (int, float)):  # Simplify numeric type handling
        return "float" if isinstance(value, float) else "uint"
    elif isinstance(value, list):
        if not value:
            return "float[]"  # Default for empty arrays
        # Get type of first element and append []
        element_type = get_usd_type("", value[0]).replace("[]", "")
        return f"{element_type}[]"
    return "string"  # Default case


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

        # Handle rangeOffset to rangeOffsetM conversion
        if key == "rangeOffset":
            key = "rangeOffsetM"

        # Handle scanType SOLIDSTATE to SOLID_STATE conversion
        if key == "scanType" and value == "SOLIDSTATE":
            value = "SOLID_STATE"

        new_key = f"{prefix}:{key}" if prefix else key

        if isinstance(value, dict):
            flatten_json(value, new_key, result, skip_emitter_states)
        else:
            # Only include attributes that are in the schema (except for rangeOffsetM which we converted)
            base_key = new_key.split(":")[-1]
            if base_key in SCHEMA_ATTRIBUTE_TYPES or base_key == "rangeOffsetM":
                result[new_key] = value

    # After flattening, check if we need to add numberOfChannels
    if "numberOfChannels" not in result and "numberOfEmitters" in result:
        result["numberOfChannels"] = result["numberOfEmitters"]

    return result


def sanitize_name(name):
    """Replace special characters with underscores and consolidate multiple underscores."""
    # Replace special characters with underscores
    sanitized = re.sub(r"[^a-zA-Z0-9]", "_", name)

    # Replace multiple consecutive underscores with a single underscore
    sanitized = re.sub(r"_+", "_", sanitized)

    return sanitized


def extract_model_info(config):
    """Extract model name and optional tick rate from config.

    Args:
        config (dict): The JSON config

    Returns:
        tuple: (model_name, tick_rate or None)
    """
    profile = config.get("profile", {})
    model_name = profile.get("name", config.get("name", "UnknownLidar"))
    model_name = sanitize_name(model_name)

    # Extract tick rate from name (e.g., "10hz" -> 10)
    match = re.search(r"(\d+)hz", model_name.lower())
    return model_name, int(match.group(1)) if match else None


def process_emitter_states(emitter_states):
    """Process emitter states into attributes and API schemas.

    Args:
        emitter_states (list): List of emitter state dictionaries

    Returns:
        tuple: (attributes, api_schemas)
    """
    attributes = []
    api_schemas = ["OmniSensorGenericLidarCoreAPI"]

    # Process each emitter state
    for i, state in enumerate(emitter_states):
        # First pass: find any float[] attributes and their length
        float_array_length = None
        for key, value in state.items():
            if "comment" in key.lower():
                continue

            # Skip attributes not in schema
            if key not in SCHEMA_ATTRIBUTE_TYPES:
                continue

            usd_type = get_usd_type(key, value)
            if usd_type == "float[]" and value:
                float_array_length = len(value)
                break

        # Second pass: process all attributes
        processed_keys = set()
        for key, value in state.items():
            if "comment" in key.lower():
                continue

            # Skip attributes not in schema
            if key not in SCHEMA_ATTRIBUTE_TYPES:
                continue

            emitter_key = f"emitterState:s{i+1:03d}:{key}"
            usd_key = f"omni:sensor:Core:{emitter_key}"
            usd_type = get_usd_type(key, value)

            # Ensure array type for emitter state values
            if not usd_type.endswith("[]"):
                usd_type = f"{usd_type}[]"
                value = [value]

            usd_value = json_value_to_usda(value, usd_type)
            attributes.append(f"    {usd_type} {usd_key} = {usd_value}")
            processed_keys.add(key)

        # If we found float arrays, populate missing float[] attributes with zeros
        # and populate channelId with sequential numbers if not specified
        if float_array_length is not None:
            # Add channelId if not specified
            if "channelId" not in processed_keys:
                emitter_key = f"emitterState:s{i+1:03d}:channelId"
                usd_key = f"omni:sensor:Core:{emitter_key}"
                channel_array = list(range(1, float_array_length + 1))  # 1 to N
                usd_value = json_value_to_usda(channel_array, "uint[]")
                attributes.append(f"    uint[] {usd_key} = {usd_value}")
                processed_keys.add("channelId")

            # Add missing float[] attributes with zeros
            for key, type_info in SCHEMA_ATTRIBUTE_TYPES.items():
                if (
                    type_info == "float[]"
                    and key
                    in [
                        "azimuthDeg",
                        "elevationDeg",
                        "fireTimeNs",
                        "bank",
                        "timeOffsetNs",
                        "distanceCorrectionM",
                        "focalDistM",
                        "focalSlope",
                        "horOffsetM",
                        "reportRateDiv",
                        "vertOffsetM",
                    ]
                    and key not in processed_keys
                ):
                    emitter_key = f"emitterState:s{i+1:03d}:{key}"
                    usd_key = f"omni:sensor:Core:{emitter_key}"
                    zero_array = [0.0] * float_array_length
                    usd_value = json_value_to_usda(zero_array, "float[]")
                    attributes.append(f"    float[] {usd_key} = {usd_value}")

    # Add schemas for additional emitter states
    if len(emitter_states) > 1:
        for i in range(1, len(emitter_states)):
            api_schemas.append(f"OmniSensorGenericLidarCoreEmitterStateAPI:s{i+1:03d}")

    return attributes, api_schemas


def convert_json_to_usda(json_path, usda_path):
    """Convert a JSON config file to USDA format."""
    with open(json_path, "r") as f:
        config = json.load(f)

    # Extract basic information
    model_name, tick_rate = extract_model_info(config)

    # Process main attributes
    attributes = []
    if "profile" in config:
        flattened = flatten_json(config["profile"], skip_emitter_states=True)
        for key, value in flattened.items():
            usd_key = f"omni:sensor:Core:{key}"
            usd_type = get_usd_type(key, value)
            usd_value = json_value_to_usda(value, usd_type)
            attributes.append(f"    {usd_type} {usd_key} = {usd_value}")

    # Process emitter states
    emitter_states = config.get("profile", {}).get("emitterStates", [])
    emitter_attrs, api_schemas = process_emitter_states(emitter_states)
    attributes.extend(emitter_attrs)

    # Format API schemas
    api_schemas_str = ", ".join(f'"{schema}"' for schema in api_schemas)

    # Generate USDA content
    usda_content = f"""#usda 1.0
(
    doc = "Generated from {os.path.basename(json_path)}"
    defaultPrim = "{model_name}"
)

def OmniLidar "{model_name}" (
    prepend apiSchemas = [{api_schemas_str}]
)
{{
    string omni:sensor:modelName = "{model_name}"
{f'    float omni:sensor:tickRate = {tick_rate}' if tick_rate is not None else ''}

    # Configuration parameters from JSON
{chr(10).join(attributes)}

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
