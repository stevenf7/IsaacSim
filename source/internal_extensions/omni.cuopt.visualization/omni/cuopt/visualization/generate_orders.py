# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Visualize transport order locations on the nearest waypoint graph nodes."""

from typing import Any

from omni.kit.material.library import CreateAndBindMdlMaterialFromLibrary
from pxr import Gf, Sdf, UsdShade

from .common import translate_rotate_scale_prim
from .generate_waypoint_graph import get_closest_node


# Assign Material to Waypoints representing order locations
def add_order_waypoint_material(stage: Any, transport_orders: Any) -> Any:
    """Create the emissive material used to mark waypoint nodes assigned to orders."""
    order_waypoint_material_name = "order_material"
    CreateAndBindMdlMaterialFromLibrary(
        mdl_name="OmniPBR.mdl",
        mtl_name="OmniPBR",
        bind_selected_prims=False,
        prim_name=order_waypoint_material_name,
    ).do()

    order_waypoint_material_path = f"/World/Looks/{order_waypoint_material_name}"
    transport_orders.order_waypoint_material = UsdShade.Material(stage.GetPrimAtPath(order_waypoint_material_path))
    waypoint_shader = UsdShade.Shader(stage.GetPrimAtPath(f"{order_waypoint_material_path}/Shader"))
    waypoint_shader.CreateInput("enable_emission", Sdf.ValueTypeNames.Bool).Set(True)
    waypoint_shader.CreateInput("emissive_color", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(transport_orders.order_waypoint_color)
    )
    waypoint_shader.CreateInput("emissive_intensity", Sdf.ValueTypeNames.Float).Set(
        transport_orders.order_waypoint_intensity
    )
    waypoint_shader.CreateInput("ao_to_diffuse", Sdf.ValueTypeNames.Float).Set(1)


# Visualize order locations in loaded task data
def visualize_order_locations(stage: Any, waypoint_graph_model: Any, transport_orders: Any) -> Any:
    """Bind order styling to nearest graph nodes and store their indices for cuOpt."""
    # Material
    order_waypoint_material_name = "order_waypoint_material"
    order_waypoint_material_path = f"/World/Looks/{order_waypoint_material_name}"

    if not stage.GetPrimAtPath(order_waypoint_material_path).IsValid():
        add_order_waypoint_material(stage, transport_orders)
    elif transport_orders.order_waypoint_material is None:
        transport_orders.order_waypoint_material = UsdShade.Material(stage.GetPrimAtPath(order_waypoint_material_path))

    order_inds = []

    for xyz_loc in transport_orders.order_xyz_locations:
        closest_waypoint_path = get_closest_node(
            stage,
            waypoint_graph_model,
            Gf.Vec3d(xyz_loc[0], xyz_loc[1], xyz_loc[2]),
        )

        closest_node_prim = stage.GetPrimAtPath(closest_waypoint_path)

        order_inds.append(waypoint_graph_model.path_node_map[closest_waypoint_path])

        translate_rotate_scale_prim(
            stage=stage,
            prim=closest_node_prim,
            scale_set=transport_orders.order_node_scale,
        )

        UsdShade.MaterialBindingAPI(closest_node_prim).Bind(transport_orders.order_waypoint_material)

    transport_orders.graph_locations = order_inds

    print(f"Orders have been assigned to the following nodes {transport_orders.graph_locations}")
