# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# [snippet-start]
from isaacsim.core.simulation_manager import PhysicsScene

physics_scene = PhysicsScene("/World/PhysicsScene")
physics_scene.set_gravity((0.0, 0.0, -9.81))
physics_scene.set_dt(0.001)
physics_scene.set_enabled_gravity(True)
physics_scene.set_max_solver_iterations(100)
