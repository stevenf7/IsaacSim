# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# [snippet-start]
from isaacsim.core.simulation_manager import SimulationManager

engines = SimulationManager.get_available_physics_engines(verbose=True)
success = SimulationManager.switch_physics_engine("newton")
if success:
    print("Switched to Newton physics engine")
