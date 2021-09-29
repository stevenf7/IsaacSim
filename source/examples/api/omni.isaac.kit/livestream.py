# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.isaac.kit import SimulationApp

# This sample enables a livestream server to connect to when running headless
CONFIG = {
    "width": 1280,
    "height": 720,
    "window_width": 1920,
    "window_height": 1080,
    "headless": True,
    "renderer": "RayTracedLighting",
    "display_options": 3807,  # Set display options to show default grid
}


# Start the omniverse application
kit = SimulationApp(launch_config=CONFIG)

# Enable Livestream extension
kit.set_setting("/app/window/drawMouse", True)
kit.set_setting("/app/livestream/proto", "ws")
kit.set_extension_enabled("omni.kit.livestream.core", True)
kit.set_extension_enabled("omni.kit.livestream.native", True)

# Run until closed
while kit.is_running():
    # Run in realtime mode, we don't specify the step size
    kit.update()

kit.close()
