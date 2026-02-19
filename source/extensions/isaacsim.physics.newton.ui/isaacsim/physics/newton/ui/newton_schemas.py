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

"""Newton schema discovery and UI definitions for the Newton physics extension."""


def _get_newton_schema_names(pluginName: str) -> tuple[set[str], set[str]]:
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


def get_newton_schema_names() -> tuple[set[str], set[str]]:
    """Get all Newton schema type names.

    Returns:
        A tuple of (prim_type_names, api_schema_names) for Newton schemas.
    """
    prim_type_names: set[str] = set()
    api_schema_names: set[str] = set()

    prim_types, api_schemas = _get_newton_schema_names("newton")
    prim_type_names.update(prim_types)
    api_schema_names.update(api_schemas)

    # List of schemas that are not capabilities
    not_capabilities = [
        "NewtonSceneAPI",
        "NewtonXpbdSceneAPI",
        "NewtonCollisionAPI",
        "NewtonMeshCollisionAPI",
        "NewtonMaterialAPI",
    ]

    for schema_name in not_capabilities:
        prim_type_names.discard(schema_name)
        api_schema_names.discard(schema_name)

    return prim_type_names, api_schema_names


# scene widget with hardcoded solver property
from omni.kit.property.physics.widgets import ExtensionSchemaWidget, UiProp
from omni.physics.isaacsimready import get_variant_switcher


class ExtendedNewtonSceneWidget(ExtensionSchemaWidget):
    def _filter_props_to_build(self, prim):
        filtered_props = super()._filter_props_to_build(prim)
        if get_variant_switcher().get_active_simulation()[1] == "Newton":
            filtered_props.append(
                UiProp().from_custom("newton:solver", "Solver", "", "token", "mjcwarp", "Solver used by Newton")
            )
        return filtered_props


# NOTE: omni.physics.physx.ui/omni/physics/physxui/schemas/physxschema.py for reference

from omni.kit.property.physics.builders import PrettyPrintTokenComboBuilder
from pxr import UsdPhysics


class NewtonUiDefinitions:
    """UI definitions (widgets, property builders, ordering) for Newton schemas."""

    ignore = {}
    extensions = {
        UsdPhysics.Scene: ["NewtonSceneAPI"],
    }
    extras = {}
    widgets = {
        "NewtonSceneAPI": ExtendedNewtonSceneWidget,
    }
    property_builders = {
        "newton:solver": [PrettyPrintTokenComboBuilder, [], [("mjcwarp", "MuJoCo Warp")]],
    }
    property_order = {}
