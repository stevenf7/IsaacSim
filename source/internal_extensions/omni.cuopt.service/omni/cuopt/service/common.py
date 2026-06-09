# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Shared JSON, connection, and route-formatting helpers for cuOpt examples."""

import json
from typing import Any

import requests

from .cuopt_thin_client import CuOptServiceClient


def read_json(json_file_path: Any) -> Any:
    """Read a sample-data JSON file used by the cuOpt service examples.

    Args:
        json_file_path: Path to the JSON file to read.

    Returns:
        Parsed JSON data.
    """
    with open(json_file_path) as json_file:
        json_data = json.load(json_file)

    return json_data


def show_vehicle_routes(routes: Any) -> Any:
    """Format a cuOpt solver response into the route summary shown in example UIs.

    Args:
        routes: Solver response containing vehicle counts, solution cost, and vehicle routes.

    Returns:
        Human-readable route summary.
    """
    message = f"Solution found using {routes['num_vehicles']} vehicles \nSolution cost: {routes['solution_cost']} \n\n"
    for v_id, data in routes["vehicle_data"].items():
        message = message + "For vehicle -" + str(v_id) + " route is: \n"
        path = ""
        route_ids = data["route"]
        for index, route_id in enumerate(route_ids):
            path += str(route_id)
            if index != (len(route_ids) - 1):
                path += "-> "
        message = message + path + "\n\n"
    return message


def test_connection_microservice(ip: Any, port: Any) -> None:
    """Probe the local cuOpt microservice health endpoint and return a UI status message.

    Args:
        ip: Hostname or IP address for the cuOpt microservice.
        port: Port for the cuOpt microservice.

    Returns:
        Status message describing whether the microservice is reachable.
    """
    cuopt_url = f"http://{ip}:{port}/cuopt/"

    cuopt_status_info = f"working"

    try:
        cuopt_response = requests.get(cuopt_url + "health")
        if cuopt_response.status_code == 200:
            cuopt_status_info = "SUCCESS: cuOpt Microservice is Running"
        else:
            cuopt_status_info = "FAILURE: cuOpt Microservice found but not running correctly"

    except BaseException:
        cuopt_status_info = f"FAILURE: cuOpt Microservice was not found running at {cuopt_url}"
    return cuopt_status_info


def test_connection_managed_service(auth: Any, function_name: Any, function_id: Any) -> None:
    """Create a managed-service client from the supplied SAK/function selector.

    Args:
        auth: Secret access key used to authenticate with the managed service.
        function_name: Name of the managed cuOpt function to use.
        function_id: ID of the managed cuOpt function to use.

    Returns:
        Status message and client instance, or ``None`` when the client cannot be created.
    """
    print(auth, function_name, function_id)
    try:
        client = CuOptServiceClient(sak=auth, function_name=function_name, function_id=function_id)
        cuopt_status_info = "SUCCESS: cuOpt Managed Service is Accessible"
    except BaseException:
        client = None
        cuopt_status_info = "FAILURE: cuOpt Managed Service is not Accessible"
    return cuopt_status_info, client
