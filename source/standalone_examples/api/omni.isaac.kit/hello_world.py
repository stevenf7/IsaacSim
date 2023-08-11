# Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni
from omni.isaac.kit import SimulationApp

# The most basic usage for creating a simulation app
kit = SimulationApp()

for i in range(100):
    kit.update()

omni.kit.app.get_app().print_and_log("Hello World!")

kit.close()  # Cleanup application
