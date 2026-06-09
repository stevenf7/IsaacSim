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
    """Submit one optimization problem at a time to a cuOpt microservice URL."""

    def __init__(self, cuopt_url: str) -> None:
        """Initialize a runner and clear any existing optimization data at the URL.

        A cuOpt microservice URL stores one active problem at a time, so constructing
        a runner deletes stale state before submitting a new request.
        """
        self.cuopt_url = cuopt_url
        self.data_parameters = {"return_data_state": False}

        requests.delete(cuopt_url + "clear_optimization_data")
        print(f"\n - OPTIMIZATION DATA AT {cuopt_url} HAS BEEN CLEARED - \n")

    def get_routes(self, cuopt_problem_data: Any) -> Any:
        """Post a routing problem, poll until solved, and return the solver response."""
        solver_response = requests.post(self.cuopt_url + "request", json=cuopt_problem_data).json()
        while "response" not in solver_response:
            reqId = solver_response["reqId"]
            solver_response = requests.get(self.cuopt_url + "solution" + f"/{reqId}").json()
            time.sleep(1)

        print(f"SOLVER RESPONSE: {solver_response}\n")
        return solver_response["response"]["solver_response"]
