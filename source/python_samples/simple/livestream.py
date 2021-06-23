# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
from omni.isaac.python_app import OmniKitHelper
import carb
import omni

# This sample enables a livestream server to connect to when running headless
CONFIG = {
    "experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit',
    "width": 1280,
    "height": 720,
    "sync_loads": True,
    "headless": True,
    "renderer": "RayTracedLighting",
}

if __name__ == "__main__":
    import argparse

    # Set up command line arguments
    parser = argparse.ArgumentParser("Livestream sample")
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--webrtc", help="Use Webrtc backend", action="store_true")
    g.add_argument("--websocket", help="Use Websocket backend", action="store_true")
    g.add_argument("--kitremote", help="Use Kit remote backend", action="store_true")

    args, unknown = parser.parse_known_args()

    # Start the omniverse application
    kit = OmniKitHelper(config=CONFIG)

    # enable ROS bridge extension
    ext_manager = omni.kit.app.get_app().get_extension_manager()
    kit.set_setting("/app/window/drawMouse", True)
    ext_manager.set_extension_enabled_immediate("omni.kit.livestream.core", True)
    if args.webrtc:
        ext_manager.set_extension_enabled_immediate("omni.services.streamclient.webrtc", True)
    elif args.websocket:
        kit.set_setting("/ngx/enabled", False)
        kit.set_setting("/app/livestream/proto", "ws")
        ext_manager.set_extension_enabled_immediate("omni.services.streamclient.websocket", True)
    else:
        kit.set_setting("/app/livestream/proto", "ws")
        ext_manager.set_extension_enabled_immediate("omni.kit.livestream.native", True)

    # Run until closed
    while kit.app.is_running():
        # Run in realtime mode, we don't specify the step size
        kit.update()

    kit.stop()
    kit.shutdown()
