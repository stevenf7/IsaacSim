# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
from .common import read_json


class TransportVehicles:
    def __init__(self):
        self.num_vehicles = None
        self.vehicle_xyz_locations = None
        self.graph_locations = None
        self.vehicle_capacities = None
        self.vehicle_time_windows = None

    # Load Fleet info from json data
    def load_sample(self, vehicles_json_path):
        vehicles_data = read_json(vehicles_json_path)

        self.num_vehicles = len(vehicles_data["vehicle_locations"])
        self.vehicle_xyz_locations = vehicles_data["vehicle_locations"]
        self.vehicle_capacities = vehicles_data["capacities"]
        if "vehicle_time_windows" in vehicles_data:
            self.vehicle_time_windows = vehicles_data["vehicle_time_windows"]

        self.graph_locations = vehicles_data["vehicle_locations"]
