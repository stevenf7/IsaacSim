# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
from omni.isaac.python_app import OmniKitHelper
import numpy as np

CONFIG = {
    "experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit',
    "renderer": "RayTracedLighting",
    "headless": True,
}

if __name__ == "__main__":
    # Simple example showing how to publish a custom message from isaac sdk
    kit = OmniKitHelper(config=CONFIG)
    # Perform any omniverse imports here after the helper loads
    import omni

    # enable SDK bridge extension
    ext_manager = omni.kit.app.get_app().get_extension_manager()
    ext_manager.set_extension_enabled_immediate("omni.isaac.robot_engine_bridge", True)

    from omni.isaac.pyalice import Application, Composite

    # Create pyalice application
    ext_manager = omni.kit.app.get_app().get_extension_manager()
    ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
    reb_extension_path = ext_manager.get_extension_path(ext_id)

    app = Application(name="custom_message", asset_path=reb_extension_path, modules=["engine_tcp_udp"])
    simulation_node = app.add("simulation")
    tcp_pub = simulation_node.add(app.registry.isaac.alice.TcpPublisher, "output")
    tcp_pub.config.port = 55001

    app.start()
    kit.play()  # Start simulation

    for frame in range(1000):
        # publish a custom compositite proto message each frame
        entities = [["frame", "time", 1], ["custom", "none", 1]]
        values = np.array([frame, 1.0], dtype=np.dtype("float64"))
        msg = Composite.create_composite_message(entities, values)
        app.publish("simulation", "output", "custom_message", msg)
        # Render a single frame
        kit.update(1.0 / 60.0)

    app.stop()  # Stop pyalice application
    kit.stop()  # Stop Simulation
    kit.shutdown()  # Cleanup application
