# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Common telemetry schema for Isaac Sim extensions.

Defines the baked JSON Schema (draft-07) consumed by ``omni.structuredlog.register_schema()``.
The schema contains three events shared across all Isaac Sim extensions:

* **extensionActivated** -- tracks which extensions are enabled/disabled per session.
* **featureUsed** -- tracks commands, menu items, and API calls within extensions.
* **errorOccurred** -- tracks recoverable errors with structured context.
"""

_EVENT_PREFIX = "com.nvidia.isaacsim.telemetry.common"

COMMON_SCHEMA_NAME = "isaacsim.telemetry.common"
#: Schema name used as the key when registering with `TelemetryManager`.

ISAACSIM_COMMON_SCHEMA: dict = {
    "generated": "Hand-authored common telemetry schema for Isaac Sim.",
    "anyOf": [
        {"$ref": f"#/definitions/events/{_EVENT_PREFIX}.extensionActivated"},
        {"$ref": f"#/definitions/events/{_EVENT_PREFIX}.featureUsed"},
        {"$ref": f"#/definitions/events/{_EVENT_PREFIX}.errorOccurred"},
    ],
    "$schema": "http://json-schema.org/draft-07/schema#",
    "schemaMeta": {
        "clientName": COMMON_SCHEMA_NAME,
        "schemaVersion": "1.0",
        "eventPrefix": _EVENT_PREFIX,
        "definitionVersion": "1.0",
        "omniverseFlags": ["fSchemaFlagAnonymizeEvents"],
        "description": "Common telemetry events shared across all Isaac Sim extensions.",
    },
    "definitions": {
        "events": {
            f"{_EVENT_PREFIX}.extensionActivated": {
                "eventMeta": {
                    "service": "telemetry",
                    "privacy": {
                        "category": "usage",
                        "description": "Tracks which Isaac Sim extensions are actively used in a session",
                    },
                    "omniverseFlags": [],
                },
                "type": "object",
                "additionalProperties": False,
                "required": ["extensionId", "extensionVersion", "action"],
                "properties": {
                    "extensionId": {
                        "type": "string",
                        "description": "Extension identifier (e.g. isaacsim.sensors.rtx)",
                    },
                    "extensionVersion": {
                        "type": "string",
                        "description": "Semantic version of the extension (e.g. 1.2.0)",
                    },
                    "action": {
                        "type": "string",
                        "description": "Lifecycle action: enabled or disabled",
                    },
                },
                "description": "Emitted when an Isaac Sim extension is enabled or disabled.",
            },
            f"{_EVENT_PREFIX}.featureUsed": {
                "eventMeta": {
                    "service": "telemetry",
                    "privacy": {
                        "category": "usage",
                        "description": "Tracks feature adoption within Isaac Sim extensions",
                    },
                    "omniverseFlags": [],
                },
                "type": "object",
                "additionalProperties": False,
                "required": ["extensionId", "featureName", "featureType", "durationMs"],
                "properties": {
                    "extensionId": {
                        "type": "string",
                        "description": "Extension that owns the feature",
                    },
                    "featureName": {
                        "type": "string",
                        "description": "Feature identifier (e.g. import_urdf, create_lidar_sensor)",
                    },
                    "featureType": {
                        "type": "string",
                        "description": "Category of usage: command, menu_item, or api_call",
                    },
                    "durationMs": {
                        "type": "number",
                        "description": "Wall-clock duration of the operation in milliseconds, 0.0 if not measured",
                    },
                },
                "description": "Emitted when a user invokes a command, menu item, or significant API call.",
            },
            f"{_EVENT_PREFIX}.errorOccurred": {
                "eventMeta": {
                    "service": "telemetry",
                    "privacy": {
                        "category": "performance",
                        "description": "Tracks errors for reliability analysis",
                    },
                    "omniverseFlags": [],
                },
                "type": "object",
                "additionalProperties": False,
                "required": ["extensionId", "errorType", "errorMessage", "context"],
                "properties": {
                    "extensionId": {
                        "type": "string",
                        "description": "Extension where the error occurred",
                    },
                    "errorType": {
                        "type": "string",
                        "description": "Error classification (e.g. import_failure, validation_error, runtime_error)",
                    },
                    "errorMessage": {
                        "type": "string",
                        "description": "Human-readable error description",
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional JSON-encoded extra detail for diagnostics",
                    },
                },
                "description": "Emitted when a recoverable error occurs in an Isaac Sim extension.",
            },
        },
    },
    "description": "Common telemetry events shared across all Isaac Sim extensions.",
}
