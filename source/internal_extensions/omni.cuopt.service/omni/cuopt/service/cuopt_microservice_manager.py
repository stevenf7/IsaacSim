# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
import time

import requests


class cuOptRunner:
    def __init__(self, cuopt_url: str):
        """
        Note that a cuOpt server at a single url manages one problem at a time.

        Initializing another instance of cuOptRunner at the same url will clear
        optimization data currently set on.
        """
        self.cuopt_url = cuopt_url
        self.data_parameters = {"return_data_state": False}

        requests.delete(cuopt_url + "clear_optimization_data")
        print(f"\n - OPTIMIZATION DATA AT {cuopt_url} HAS BEEN CLEARED - \n")

    def get_routes(self, cuopt_problem_data):
        solver_response = requests.post(self.cuopt_url + "request", json=cuopt_problem_data).json()
        while "response" not in solver_response:
            reqId = solver_response["reqId"]
            solver_response = requests.get(self.cuopt_url + "solution" + f"/{reqId}").json()
            time.sleep(1)

        print(f"SOLVER RESPONSE: {solver_response}\n")
        return solver_response["response"]["solver_response"]
