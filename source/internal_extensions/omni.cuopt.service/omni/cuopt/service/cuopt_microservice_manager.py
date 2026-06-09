# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Thin request wrapper for a local cuOpt microservice route-solver endpoint."""

import time
from typing import Any

import requests


class cuOptRunner:
    """Submit one optimization problem at a time to a cuOpt microservice URL.

    Constructing a runner clears existing optimization data because the local
    cuOpt microservice URL stores one active problem at a time.

    Args:
        cuopt_url: Base URL for the cuOpt microservice endpoint.
    """

    def __init__(self, cuopt_url: str) -> None:
        self.cuopt_url = cuopt_url
        self.data_parameters = {"return_data_state": False}

        requests.delete(cuopt_url + "clear_optimization_data")
        print(f"\n - OPTIMIZATION DATA AT {cuopt_url} HAS BEEN CLEARED - \n")

    def get_routes(self, cuopt_problem_data: Any) -> Any:
        """Post a routing problem, poll until solved, and return the solver response.

        Args:
            cuopt_problem_data: Routing problem payload to submit to the cuOpt microservice.

        Returns:
            Solver response for the submitted routing problem.
        """
        solver_response = requests.post(self.cuopt_url + "request", json=cuopt_problem_data).json()
        while "response" not in solver_response:
            reqId = solver_response["reqId"]
            solver_response = requests.get(self.cuopt_url + "solution" + f"/{reqId}").json()
            time.sleep(1)

        print(f"SOLVER RESPONSE: {solver_response}\n")
        return solver_response["response"]["solver_response"]
