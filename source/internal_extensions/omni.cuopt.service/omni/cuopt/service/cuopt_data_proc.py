# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


"""Convert loaded waypoint graph, order, and fleet samples into cuOpt payloads."""

from typing import Any


def preprocess_cuopt_data(graph: Any, task: Any, fleet: Any) -> Any:
    """Build cuOpt waypoint-graph, fleet, and task dictionaries from sample models."""
    waypoint_graph_data = {
        "waypoint_graph": {
            "0": {
                "offsets": graph.offsets,
                "edges": graph.edges,
                "weights": graph.weights,
            }
        }
    }

    fleet_data = {
        "vehicle_locations": fleet.graph_locations,
        "capacities": fleet.vehicle_capacities,
        "vehicle_time_windows": fleet.vehicle_time_windows,
    }

    task_data = {
        "task_locations": task.graph_locations,
        "demand": task.order_demand,
        "task_time_windows": task.order_time_windows,
        "service_times": task.order_service_times,
    }

    return waypoint_graph_data, fleet_data, task_data
