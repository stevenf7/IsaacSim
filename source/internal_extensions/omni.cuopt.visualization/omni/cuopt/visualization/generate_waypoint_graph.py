# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Author and update USD waypoint graph visuals for cuOpt routing demos."""

from typing import Any

from omni.kit.material.library import CreateAndBindMdlMaterialFromLibrary
from pxr import Gf, Sdf, UsdGeom, UsdShade

from .common import check_build_base_path, edge_in_volume, get_prim_translation, translate_rotate_scale_prim


class NetworkSimpleViz:
    """Create waypoint node, edge, and route materials/prims for graph visualization."""

    def __init__(self) -> None:
        self.node_scale = [0.4, 0.4, 0.15]
        self.waypoint_height = 0.15
        self.node_refinement_level = 2
        self.waypoint_color = [1, 1, 1]
        self.waypoint_intensity = 5000.0
        self.waypoint_material = None
        self.waypoint_material_path = f"/World/Looks/waypoint_material"
        self.edge_radius = 0.2

        self.routes_color = [
            [0.0, 0.00363, 0.07173],
            [0.06329, 0.01282, 0.0],
            [0.008438826, 0.0016023085, 0.008179213],
            [0.008438826, 0.0016023085, 0.0016023085],
            [0.0016023085, 0.008438826, 0.007833057],
            [0.0017753834, 0.0016023085, 0.008438826],
            [0.10548526, 0.061421696, 0],
            [0.0, 0.0, 0.0],
        ]

    # Assign Material to Waypoints
    def add_waypoint_material(self, stage: Any) -> Any:
        """Create the emissive material used by default waypoint nodes and edges.

        Args:
            stage: Stage where the waypoint material prim is created.

        Returns:
            None.
        """
        CreateAndBindMdlMaterialFromLibrary(
            mdl_name="OmniPBR.mdl",
            mtl_name="OmniPBR",
            bind_selected_prims=False,
            prim_name="waypoint_material",
        ).do()

        waypoint_material_path = self.waypoint_material_path
        self.waypoint_material = UsdShade.Material(stage.GetPrimAtPath(waypoint_material_path))
        waypoint_shader = UsdShade.Shader(stage.GetPrimAtPath(f"{waypoint_material_path}/Shader"))
        waypoint_shader.CreateInput("enable_emission", Sdf.ValueTypeNames.Bool).Set(True)
        waypoint_shader.CreateInput("emissive_color", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(self.waypoint_color))
        waypoint_shader.CreateInput("emissive_intensity", Sdf.ValueTypeNames.Float).Set(self.waypoint_intensity)
        waypoint_shader.CreateInput("ao_to_diffuse", Sdf.ValueTypeNames.Float).Set(1)

    # Visualize nodes in the Waypoint Graph network
    def add_node_to_scene(self, stage: Any, node_prim_path: Any, translation: Any) -> Any:
        """Author a waypoint node sphere at the requested graph coordinate.

        Args:
            stage: Stage where the node prim is authored.
            node_prim_path: Path for the generated node prim.
            translation: Node position to apply to the generated prim.

        Returns:
            None.
        """
        node_prim_geom = UsdGeom.Sphere.Define(stage, node_prim_path)

        if self.waypoint_height is not None:
            translation[2] = self.waypoint_height

        translate_rotate_scale_prim(
            stage=stage,
            prim_path=node_prim_path,
            translate_set=translation,
            scale_set=self.node_scale,
        )

        node_prim_geom.GetPrim().CreateAttribute("refinementEnableOverride", Sdf.ValueTypeNames.Bool).Set(True)
        node_prim_geom.GetPrim().CreateAttribute("refinementLevel", Sdf.ValueTypeNames.Int).Set(
            self.node_refinement_level
        )

        semantic_prim = stage.GetPrimAtPath(node_prim_path)

        # Material
        waypoint_material_name = "waypoint_material"
        waypoint_material_path = f"/World/Looks/{waypoint_material_name}"

        if not stage.GetPrimAtPath(waypoint_material_path).IsValid():
            self.add_waypoint_material(stage)
        elif self.waypoint_material is None:
            self.waypoint_material = UsdShade.Material(stage.GetPrimAtPath(waypoint_material_path))

        UsdShade.MaterialBindingAPI(semantic_prim).Bind(self.waypoint_material)

    # Visualize edges in the Waypoint Graph network
    def add_edge_to_scene(self, stage: Any, edge_prim_path: Any, point_from: Any, point_to: Any) -> Any:
        """Author a cylinder between two nodes and initialize its route weight.

        Args:
            stage: Stage where the edge prim is authored.
            edge_prim_path: Path for the generated edge prim.
            point_from: Start point of the edge cylinder.
            point_to: End point of the edge cylinder.

        Returns:
            Initial edge weight based on the distance between the points.
        """
        edge_prim_geom = UsdGeom.Cylinder.Define(stage, edge_prim_path)

        edge_vector = point_to - point_from
        edge_prim = edge_prim_geom.GetPrim()
        xf = UsdGeom.Xformable(edge_prim_geom)
        xf.ClearXformOpOrder()
        xf.AddTranslateOp().Set(point_from + edge_vector * 0.5)
        n = edge_vector.GetNormalized()
        r = Gf.Rotation(Gf.Vec3d(0, 0, 1), Gf.Vec3d(n[0], n[1], n[2]))
        xf.AddOrientOp(UsdGeom.XformOp.PrecisionDouble).Set(r.GetQuat())
        xf.AddScaleOp().Set(
            Gf.Vec3d(
                self.edge_radius / 3,
                self.edge_radius / 3,
                edge_vector.GetLength() / 2,
            )
        )
        edge_prim.CreateAttribute("baseweight", Sdf.ValueTypeNames.Float).Set(edge_vector.GetLength())
        edge_prim.CreateAttribute("weight", Sdf.ValueTypeNames.Float).Set(edge_vector.GetLength())
        UsdShade.MaterialBindingAPI(edge_prim).Bind(self.waypoint_material)

        return edge_prim.GetAttribute("weight").Get()

    # Assign Material to routes and edges
    def get_route_material(self, stage: Any, i: Any) -> Any:
        """Create and return an emissive material for one solved vehicle route.

        Args:
            stage: Stage where the route material prim is created.
            i: Route color index.

        Returns:
            Created route material.
        """
        route_material_name = "route_material_" + str(i)
        CreateAndBindMdlMaterialFromLibrary(
            mdl_name="OmniPBR.mdl",
            mtl_name="OmniPBR",
            bind_selected_prims=False,
            prim_name=route_material_name,
        ).do()

        route_material_path = f"/World/Looks/{route_material_name}"
        route_material = UsdShade.Material(stage.GetPrimAtPath(route_material_path))
        route_shader = UsdShade.Shader(stage.GetPrimAtPath(f"{route_material_path}/Shader"))
        route_shader.CreateInput("enable_emission", Sdf.ValueTypeNames.Bool).Set(True)
        route_shader.CreateInput("emissive_color", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(self.routes_color[i]))
        route_shader.CreateInput("emissive_intensity", Sdf.ValueTypeNames.Float).Set(100000)
        route_shader.CreateInput("ao_to_diffuse", Sdf.ValueTypeNames.Float).Set(1)
        return route_material

    # Visualize optimized routes
    def display_routes(self, stage: Any, graph: Any, waypoint_graph_edge_path: Any, routes: Any) -> Any:
        """Reset edge styling, then color each edge used by the cuOpt solution.

        Args:
            stage: Stage containing waypoint edge prims.
            graph: Graph model with edge path mappings.
            waypoint_graph_edge_path: Parent path for waypoint edge prims.
            routes: cuOpt route data keyed by vehicle.

        Returns:
            None.
        """
        all_edges = graph.path_edge_map.keys()
        for i, edge_path in enumerate(all_edges):
            edge_prim = stage.GetPrimAtPath(edge_path)
            # Material
            waypoint_material_path = self.waypoint_material_path
            if not stage.GetPrimAtPath(waypoint_material_path).IsValid():
                print("ISVALID")
                self.add_waypoint_material(stage)
            elif self.waypoint_material is None:
                self.waypoint_material = UsdShade.Material(stage.GetPrimAtPath(waypoint_material_path))
            UsdShade.MaterialBindingAPI(edge_prim).Bind(self.waypoint_material)

        vehicle_data = routes["vehicle_data"]
        for i, v_id in enumerate(vehicle_data.keys()):
            route_material = self.get_route_material(stage, i)
            v_routes = vehicle_data[v_id]["route"]
            for j in range(0, len(v_routes) - 1):
                edge_prim_path = f"{waypoint_graph_edge_path}/Edge_{v_routes[j]}_{v_routes[j+1]}"
                edge_prim = stage.GetPrimAtPath(edge_prim_path)

                UsdShade.MaterialBindingAPI(edge_prim).Bind(route_material)
                edge_prim_path_bi = f"{waypoint_graph_edge_path}/Edge_{v_routes[j+1]}_{v_routes[j]}"
                edge_prim_bi = stage.GetPrimAtPath(edge_prim_path_bi)
                if edge_prim_bi.IsValid():
                    UsdShade.MaterialBindingAPI(edge_prim_bi).Bind(route_material)


def visualize_and_record_node(model: Any, stage: Any, node_prim_path: Any, translation: Any) -> Any:
    """Create a node prim and record its model-index to USD-path mappings.

    Args:
        model: Graph model whose node mappings are updated.
        stage: Stage where the node prim is authored.
        node_prim_path: Path for the generated node prim.
        translation: Node position to apply to the generated prim.

    Returns:
        None.
    """
    model.visualization.add_node_to_scene(stage, node_prim_path, translation)

    # Data recording
    model.node_path_map[model.node_count] = node_prim_path
    model.path_node_map[node_prim_path] = model.node_count

    model.node_count += 1


def visualize_and_record_edge(model: Any, stage: Any, edge_prim_path: Any, point_from: Any, point_to: Any) -> Any:
    """Create an edge prim and record its weight plus USD-path mappings.

    Args:
        model: Graph model whose edge mappings and weights are updated.
        stage: Stage where the edge prim is authored.
        edge_prim_path: Path for the generated edge prim.
        point_from: Start point of the edge cylinder.
        point_to: End point of the edge cylinder.

    Returns:
        None.
    """
    weight = model.visualization.add_edge_to_scene(stage, edge_prim_path, point_from, point_to)

    # Data recording
    model.edge_path_map[model.edge_count] = edge_prim_path
    model.path_edge_map[edge_prim_path] = model.edge_count
    model.weights.append(weight)
    model.edge_count = model.edge_count + 1


def update_weights(stage: Any, model: Any, semantics: Any) -> Any:
    """Recompute graph edge weights from visible semantic-zone overlap penalties.

    Args:
        stage: Stage containing graph edges and semantic zone prims.
        model: Graph model whose weight list is updated.
        semantics: Semantic zone paths to evaluate against graph edges.

    Returns:
        None.
    """
    edges = model.path_edge_map.keys()

    # Only calculate for visible semantic zones
    vis_vol_paths = []
    print(semantics)
    for vol_path in semantics:
        if stage.GetPrimAtPath(vol_path).IsValid():
            prim_is_visible = True
            vol_prim = stage.GetPrimAtPath(vol_path)

            # check the prim
            vis_status = vol_prim.GetAttribute("visibility").Get()

            # if it's inherited check all parents
            if vis_status == "inherited":

                # check parents until root path
                while vol_prim.GetPath().pathString != "/":
                    parent = vol_prim.GetParent()
                    vis_status = parent.GetAttribute("visibility").Get()
                    if vis_status == "invisible":
                        prim_is_visible = False
                    vol_prim = parent
            else:
                prim_is_visible = False

            # if the prim and all it's parents are visible
            if prim_is_visible:
                vis_vol_paths.append(vol_path)
            else:
                print(f"{vol_path} is not visible at some level so will not be used")
        else:
            print("Deleted Semantic Zone Data Ignored.")

    for i, edge_path in enumerate(edges):
        edge_prim = stage.GetPrimAtPath(edge_path)
        base_weight = edge_prim.GetAttribute("baseweight").Get()
        edge_prim.GetAttribute("weight").Set(base_weight)
        current_weight = edge_prim.GetAttribute("weight").Get()

        for vol_path in vis_vol_paths:
            # print(vol_path, edge_path)
            vol_prim = stage.GetPrimAtPath(vol_path)
            #
            is_true, perc = edge_in_volume(edge_prim, vol_prim)
            if is_true:
                print("edge_in volume: ", perc * 100, " %")
                semantic_weight = vol_prim.GetAttribute("mfgstd:properties:semantic_weight").Get()
                current_weight = current_weight + base_weight * (semantic_weight - 1.0) * perc
                print(
                    "Base edge weight:",
                    base_weight,
                    "Semantic weight:",
                    semantic_weight,
                    "New edge weight:",
                    current_weight,
                )
        edge_prim.GetAttribute("weight").Set(current_weight)
        model.weights[i] = edge_prim.GetAttribute("weight").Get()


# Get Nodes closest to point (x,y,z)
def get_closest_node(stage: Any, model: Any, point: Any) -> Any:
    """Return the waypoint node prim path nearest to a 3D order location.

    Args:
        stage: Stage containing waypoint node prims.
        model: Graph model with node path mappings.
        point: Location to compare against waypoint node positions.

    Returns:
        Path of the nearest waypoint node prim, or ``None`` when no nodes exist.
    """
    min_dist = None
    closest_node_path = None
    for node_path in model.path_node_map:
        node_prim = stage.GetPrimAtPath(node_path)
        node_point = get_prim_translation(node_prim)
        distance = (node_point - point).GetLength()
        if min_dist is None:
            min_dist = distance
            closest_node_path = node_path
        elif min_dist > distance:
            min_dist = distance
            closest_node_path = node_path
    return closest_node_path


def visualize_waypoint_graph(
    stage: Any, model: Any, waypoint_graph_node_path: Any, waypoint_graph_edge_path: Any
) -> Any:
    """Create node and edge prims for a loaded waypoint graph model.

    Args:
        stage: Stage where waypoint graph prims are authored.
        model: Graph model containing node and edge data.
        waypoint_graph_node_path: Parent path for generated node prims.
        waypoint_graph_edge_path: Parent path for generated edge prims.

    Returns:
        None.
    """
    model.visualization = NetworkSimpleViz()

    check_build_base_path(stage, waypoint_graph_node_path, final_xform=True)
    stage.DefinePrim(waypoint_graph_node_path, "Xform")
    for i, node_loc in enumerate(model.nodes):
        node_prim_path = f"{waypoint_graph_node_path}/Node_{model.node_count}"
        visualize_and_record_node(model, stage, node_prim_path, node_loc)

    check_build_base_path(stage, waypoint_graph_edge_path, final_xform=True)
    stage.DefinePrim(waypoint_graph_edge_path, "Xform")

    offset_node_lookup = model.offset_node_lookup

    for i in range(0, len(model.offsets) - 1):
        for j in range(model.offsets[i], model.offsets[i + 1]):
            edge_prim_path = f"{waypoint_graph_edge_path}/Edge_{offset_node_lookup[i]}_{model.edges[j]}"

            if str(offset_node_lookup[i]) not in model.node_edge_map:
                model.node_edge_map[str(offset_node_lookup[i])] = [model.edges[j]]
            else:
                model.node_edge_map[str(offset_node_lookup[i])].append(model.edges[j])

            point_from = Gf.Vec3d(model.nodes[int(offset_node_lookup[i])])
            point_to = Gf.Vec3d(model.nodes[model.edges[j]])
            visualize_and_record_edge(model, stage, edge_prim_path, point_from, point_to)


def load_waypoint_graph_from_scene(stage: Any, model: Any) -> Any:
    """Populate a graph model from existing waypoint node and edge prims in the stage.

    Args:
        stage: Stage containing existing waypoint node and edge prims.
        model: Graph model to populate from the stage.

    Returns:
        None.
    """
    nodes = stage.GetPrimAtPath("/World/Network/WaypointGraph/Nodes").GetChildren()

    edge_names = stage.GetPrimAtPath("/World/Network/WaypointGraph/Edges").GetChildrenNames()

    offsets = []
    edges = []
    weights = []
    cur_offset = 0
    offset_node_lookup = {}

    for node in nodes:
        model.nodes.append(list(node.GetAttribute("xformOp:translate").Get()))
        node_i = node.GetName().split("_")[-1]
        offsets.append(cur_offset)
        model.node_path_map[int(node_i)] = node.GetPrimPath()
        model.path_node_map[node.GetPrimPath()] = int(node_i)
        for i in range(len(nodes)):
            edge_name = "Edge_" + node_i + "_" + str(i)
            edge_path = "/World/Network/WaypointGraph/Edges/" + edge_name
            if edge_name in edge_names:
                model.edge_path_map[len(edges)] = edge_path
                model.path_edge_map[edge_path] = len(edges)
                cur_offset += 1
                edges.append(i)
                weights.append(stage.GetPrimAtPath(edge_path).GetAttribute("weight").Get())

        offset_node_lookup[int(node_i)] = int(node_i)

    offsets.append(cur_offset)

    model.offsets = offsets
    model.edges = edges
    model.weights = weights
    model.offset_node_lookup = offset_node_lookup
    model.visualization = NetworkSimpleViz()
    offset_node_lookup = model.offset_node_lookup
    for i in range(0, len(model.offsets) - 1):
        for j in range(model.offsets[i], model.offsets[i + 1]):

            if str(offset_node_lookup[i]) not in model.node_edge_map:
                model.node_edge_map[str(offset_node_lookup[i])] = [model.edges[j]]
            else:
                model.node_edge_map[str(offset_node_lookup[i])].append(model.edges[j])
    model.visualization.waypoint_material_path = "/World/Network/Looks/waypoint_material"
