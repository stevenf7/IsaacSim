# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
from omni.isaac.kit import SimulationApp
import os
import sys

CARTER_STAGE_PATH = "/Carter"
CARTER_USD_PATH = "/Isaac/Robots/Carter/carter_v1.usd"
BACKGROUND_STAGE_PATH = "/FlatGrid"
BACKGROUND_USD_PATH = "/Isaac/Environments/Grid/default_environment.usd"

EXTENSION_NAME = "omni.isaac.gxf_bridge"
GXF_APP_YAML_FILENAME = "test_clock_sync.yaml"

CONFIG = {"renderer": "RayTracedLighting", "headless": True}

simulation_app = SimulationApp(CONFIG)
import omni
from omni.isaac.core import SimulationContext
from omni.isaac.core.utils import stage, extensions, nucleus
import omni.kit.commands

import omni.graph.core as og

# Enable GXF bridge extension
extensions.enable_extension(EXTENSION_NAME)

simulation_context = SimulationContext(set_defaults=True)

assets_root_path = nucleus.get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    simulation_app.close()
    sys.exit()


# Loading the flat grid environment
stage.add_reference_to_stage(assets_root_path + BACKGROUND_USD_PATH, BACKGROUND_STAGE_PATH)

simulation_app.update()

# Add clock timestamp publisher
graph_path = "/ActionGraph"

try:
    keys = og.Controller.Keys
    (graph, nodes, _, _) = og.Controller.edit(
        {"graph_path": graph_path, "evaluator_name": "execution"},
        {
            keys.CREATE_NODES: [
                ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                ("ReadSimTime", "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                # Node used to publish timestamp
                ("GXFPublishTimestamp", "omni.isaac.gxf_bridge.GXFPublishTimestamp"),
            ],
            keys.CONNECT: [
                ("OnPlaybackTick.outputs:tick", "GXFPublishTimestamp.inputs:execIn"),
                ("ReadSimTime.outputs:simulationTime", "GXFPublishTimestamp.inputs:timeStamp"),
            ],
            keys.SET_VALUES: [
                ("GXFPublishTimestamp.inputs:outputComponent", "channel_primary_clock"),
                ("GXFPublishTimestamp.inputs:outputEntity", "tcp_server"),
            ],
        },
    )
except Exception as e:
    print(e)

simulation_app.update()

# Get path to GXF bridge extension
ext_manager = omni.kit.app.get_app().get_extension_manager()
ext_id = ext_manager.get_enabled_extension_id(EXTENSION_NAME)
gxf_extension_path = ext_manager.get_extension_path(ext_id)
gxf_extension_lib = os.path.join(gxf_extension_path, "lib")
allocator_yaml_path = os.path.join(gxf_extension_path, "data", "config", "isaac_sim_allocator.yaml")

# Get path to this directory
app_folder = carb.tokens.get_tokens_interface().resolve("${app}/../")
package_path = os.path.abspath(app_folder)
script_path = os.path.join(package_path, "standalone_examples", "testing", EXTENSION_NAME)
test_app_path = os.path.join(script_path, GXF_APP_YAML_FILENAME)

# Create test application
result, status = omni.kit.commands.execute(
    "RobotEngineBridgeGxfCreateApplication",
    base_path=gxf_extension_lib,
    manifest_file="manifest.yaml",
    graph_files=[test_app_path, allocator_yaml_path],
)

# need to initialize physics getting any articulation..etc
simulation_context.initialize_physics()

# Run for 5 steps
frame = 0
while simulation_app.is_running():
    if frame > 5:
        break
    simulation_context.step(render=True)
    frame = frame + 1

result, status = omni.kit.commands.execute("RobotEngineBridgeGxfDestroyApplication")
simulation_app.close()
