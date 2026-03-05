# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Mujoco schema discovery and UI definitions for the Newton physics extension."""


def _get_mujoco_schema_names(pluginName: str) -> tuple[set[str], set[str]]:
    """Get all schema type names from the specified plugin.

    Args:
        pluginName: USD plugin name to query for schema types.

    Returns:
        A tuple of (prim_type_names, api_schema_names) where:
            - prim_type_names: Set of typed schema names (e.g., "PhysicsScene", "PhysicsJoint")
            - api_schema_names: Set of API schema names (e.g., "PhysicsRigidBodyAPI", "PhysicsCollisionAPI")
    """
    from pxr import Plug, Tf, Usd

    prim_type_names: set[str] = set()
    api_schema_names: set[str] = set()

    plug_registry = Plug.Registry()
    schema_registry = Usd.SchemaRegistry()

    plugin = plug_registry.GetPluginWithName(pluginName)
    if plugin is None:
        return prim_type_names, api_schema_names

    # Get all types derived from UsdSchemaBase
    all_types = Tf.Type.Find(Usd.SchemaBase).GetAllDerivedTypes()

    for tf_type in all_types:
        if not plugin.DeclaresType(tf_type):
            continue

        # Get the schema name for this type
        schema_type_name = schema_registry.GetSchemaTypeName(tf_type)
        if not schema_type_name:
            continue

        # Get schema kind to determine if it's a prim type or API schema
        schema_kind = schema_registry.GetSchemaKind(tf_type)

        if schema_kind in (Usd.SchemaKind.AbstractTyped, Usd.SchemaKind.ConcreteTyped):
            # This is a typed schema (prim type)
            prim_type_names.add(schema_type_name)
        elif schema_kind in (Usd.SchemaKind.SingleApplyAPI, Usd.SchemaKind.MultipleApplyAPI):
            # This is an API schema
            api_schema_names.add(schema_type_name)

    return prim_type_names, api_schema_names


def get_mujoco_schema_names() -> tuple[set[str], set[str]]:
    """Get all Mujoco schema type names.

    Returns:
        A tuple of (prim_type_names, api_schema_names) for Mujoco schemas.
    """
    prim_type_names: set[str] = set()
    api_schema_names: set[str] = set()

    prim_types, api_schemas = _get_mujoco_schema_names("mjcPhysics")
    prim_type_names.update(prim_types)
    api_schema_names.update(api_schemas)

    # List of schemas that are not capabilities
    not_capabilities = [
        "MjcCollisionAPI",
        "MjcMaterialAPI",
        "MjcImageableAPI",
        "MjcJointAPI",
    ]

    for schema_name in not_capabilities:
        prim_type_names.discard(schema_name)
        api_schema_names.discard(schema_name)

    return prim_type_names, api_schema_names


# NOTE: omni.physics.physx.ui/omni/physics/physxui/schemas/physxschema.py for reference

from omni.kit.property.physics.builders import HideWidgetBuilder
from pxr import UsdPhysics

from .utils import DisableByCallbackBuilder, HideByCallbackBuilder, PrimType, make_hide_cb

CallbackBuilder = DisableByCallbackBuilder
HIDE_PROPERTY = [HideWidgetBuilder]


class MujocoUiDefinitions:
    """UI definitions (widgets, property builders, ordering) for Mujoco schemas."""

    ignore = {}
    """Dictionary of schema types to ignore in UI rendering."""
    extensions = {UsdPhysics.Joint: ["MjcJointAPI"]}
    """Dictionary mapping USD schema types to their corresponding Mujoco API extensions."""
    extras = {}
    """Dictionary of additional UI configurations for specific schema types."""
    widgets = {}
    """Dictionary mapping schema properties to custom UI widget definitions."""
    property_builders = {
        "mjc:compiler:useThread": HIDE_PROPERTY,
        # Common Mjc/Newton properties - hidden when the Newton resolver provides the value.
        # SCENE
        "mjc:option:iterations": [CallbackBuilder, make_hide_cb("mjc", PrimType.SCENE, "max_solver_iterations", None)],
        "mjc:option:timestep": [CallbackBuilder, make_hide_cb("mjc", PrimType.SCENE, "time_steps_per_second", 1000)],
        "mjc:flag:gravity": [CallbackBuilder, make_hide_cb("mjc", PrimType.SCENE, "gravity_enabled", True)],
        # JOINT
        "mjc:armature": [CallbackBuilder, make_hide_cb("mjc", PrimType.JOINT, "armature", 0.0)],
        "mjc:frictionloss": [CallbackBuilder, make_hide_cb("mjc", PrimType.JOINT, "friction", 0.0)],
        "mjc:solref": [
            CallbackBuilder,
            make_hide_cb(
                "mjc",
                PrimType.JOINT,
                [
                    "limit_transX_ke",
                    "limit_transY_ke",
                    "limit_transZ_ke",
                    "limit_transX_kd",
                    "limit_transY_kd",
                    "limit_transZ_kd",
                    "limit_linear_ke",
                    "limit_angular_ke",
                    "limit_rotX_ke",
                    "limit_rotY_ke",
                    "limit_rotZ_ke",
                    "limit_linear_kd",
                    "limit_angular_kd",
                    "limit_rotX_kd",
                    "limit_rotY_kd",
                    "limit_rotZ_kd",
                ],
            ),
        ],
        # SHAPE
        "mjc:maxhullvert": [CallbackBuilder, make_hide_cb("mjc", PrimType.SHAPE, "max_hull_vertices", -1)],
        "mjc:margin": [CallbackBuilder, make_hide_cb("mjc", PrimType.SHAPE, "margin", 0.0)],
        "mjc:gap": [CallbackBuilder, make_hide_cb("mjc", PrimType.SHAPE, "gap", 0.0)],
        # MATERIAL
        "mjc:torsionalfriction": [CallbackBuilder, make_hide_cb("mjc", PrimType.MATERIAL, "mu_torsional", 0.005)],
        "mjc:rollingfriction": [CallbackBuilder, make_hide_cb("mjc", PrimType.MATERIAL, "mu_rolling", 0.0001)],
    }
    """Dictionary mapping property names to their corresponding UI builder classes."""
    property_order = {}
    """Dictionary defining the display order of properties in the UI."""
