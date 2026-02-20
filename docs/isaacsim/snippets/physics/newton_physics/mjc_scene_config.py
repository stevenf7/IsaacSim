# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# [snippet-start]
from isaacsim.core.simulation_manager.impl.mjc_scene import NewtonMjcScene

mjc_scene = NewtonMjcScene("/World/PhysicsScene")
mjc_scene.set_dt(0.002)
mjc_scene.set_integrator("implicit")  # euler, rk4, implicit, implicitfast
mjc_scene.set_solver("newton")  # pgs, cg, newton
mjc_scene.set_iterations(100)
mjc_scene.set_tolerance(1e-8)
mjc_scene.set_cone("elliptic")  # pyramidal, elliptic
