# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.isaac.kit import SimulationApp
import numpy as np


# Simple example showing how to publish a custom message from isaac sdk
kit = SimulationApp({"renderer": "RayTracedLighting", "headless": True})
# Perform any omniverse imports here after the app loads
from omni.isaac.core.utils.extensions import enable_extension, get_extension_path, get_extension_id
import omni

# enable SDK bridge extension
enable_extension("omni.isaac.robot_engine_bridge")

# perform imports provided by this extension
from omni.isaac.pyalice import Application, Composite

# Create pyalice application
reb_extension_path = get_extension_path(get_extension_id("omni.isaac.robot_engine_bridge"))

app = Application(name="custom_message", asset_path=reb_extension_path, modules=["engine_tcp_udp"])
simulation_node = app.add("simulation")
tcp_pub = simulation_node.add(app.registry.isaac.alice.TcpPublisher, "output")
tcp_pub.config.port = 55001

app.start()
omni.timeline.get_timeline_interface().play()  # Start simulation

for frame in range(1000):
    # publish a custom compositite proto message each frame
    entities = [["frame", "time", 1], ["custom", "none", 1]]
    values = np.array([frame, 1.0], dtype=np.dtype("float64"))
    msg = Composite.create_composite_message(entities, values)
    app.publish("simulation", "output", "custom_message", msg)
    # Render a single frame
    kit.update()

app.stop()  # Stop pyalice application

kit.close()  # Cleanup application
