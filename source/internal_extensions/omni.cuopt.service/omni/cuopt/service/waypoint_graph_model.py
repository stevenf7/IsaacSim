# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Waypoint graph model and loaders for cuOpt route-optimization examples."""

from typing import Any

from .common import read_json


class WaypointGraphModel:
    """Store waypoint nodes, CSR edge arrays, weights, and USD path lookup maps."""

    def __init__(self) -> None:

        self.nodes = []
        self.offsets = []
        self.edges = []
        self.weights = []

        self.node_count = 0
        self.edge_count = 0

        self.node_path_map = {}
        self.path_node_map = {}
        self.node_edge_map = {}
        self.edge_path_map = {}
        self.path_edge_map = {}


def load_waypoint_graph_from_file(stage: Any, waypoint_graph_json: Any) -> Any:
    """Load waypoint graph JSON and convert its adjacency list to cuOpt CSR arrays."""
    model = WaypointGraphModel()

    waypoint_graph_data = read_json(waypoint_graph_json)

    model.nodes = waypoint_graph_data["node_locations"]

    graph = waypoint_graph_data["graph"]

    # Convert the graph to CSR and save it to the graph model
    offsets = []
    edges = []
    cur_offset = 0
    offset_node_lookup = {}
    ordered_keys = sorted([int(x) for x in graph])
    for i, node in enumerate(ordered_keys):
        offsets.append(cur_offset)
        cur_offset += len(graph[str(node)]["edges"])

        edges = edges + graph[str(node)]["edges"]
        offset_node_lookup[i] = node

    offsets.append(cur_offset)

    model.offsets = offsets
    model.edges = edges
    model.offset_node_lookup = offset_node_lookup

    return model


def load_waypoint_graph_from_scene(stage: Any, waypoint_graph_json: Any) -> Any:
    """Read waypoint node and edge prims from the scene into cuOpt CSR arrays."""
    model = WaypointGraphModel()

    nodes = stage.GetPrimAtPath("/World/Network/WaypointGraph/Nodes").GetChildren()

    edge_names = stage.GetPrimAtPath("/World/Network/WaypointGraph/Edges").GetChildrenNames()

    offsets = []
    edges = []
    cur_offset = 0
    offset_node_lookup = {}

    for node in nodes:
        model.nodes.append(list(node.GetAttribute("xformOp:translate").Get()))
        node_i = node.GetName().split("_")[-1]
        offsets.append(cur_offset)

        for i in range(len(nodes)):
            if "Edge_" + node_i + "_" + str(i) in edge_names:
                cur_offset += 1
                edges.append(i)
        offset_node_lookup[int(node_i)] = int(node_i)

    offsets.append(cur_offset)

    model.offsets = offsets
    model.edges = edges
    model.offset_node_lookup = offset_node_lookup

    return model
