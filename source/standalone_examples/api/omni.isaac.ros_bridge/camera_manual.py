# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
from omni.isaac.kit import SimulationApp
import sys

CAMERA_STAGE_PATH = "/Camera"
ROS_CAMERA_GRAPH_PATH = "/ROS_Camera"
BACKGROUND_STAGE_PATH = "/background"
BACKGROUND_USD_PATH = "/Isaac/Environments/Simple_Warehouse/warehouse_with_forklifts.usd"

CONFIG = {"renderer": "RayTracedLighting", "headless": False}

# Example ROS bridge sample demonstrating the manual loading of stages and manual publishing of images
simulation_app = SimulationApp(CONFIG)
import omni
from omni.isaac.core import SimulationContext
from omni.isaac.core.utils import stage, extensions, nucleus
from pxr import Gf, UsdGeom, Usd
from omni.kit.viewport.utility import get_active_viewport
import omni.graph.core as og

# enable ROS bridge extension
extensions.enable_extension("omni.isaac.ros_bridge")

simulation_app.update()

# check if rosmaster node is running
# this is to prevent this sample from waiting indefinetly if roscore is not running
# can be removed in regular usage
import rosgraph

if not rosgraph.is_master_online():
    carb.log_error("Please run roscore before executing this script")
    simulation_app.close()
    exit()

simulation_context = SimulationContext(stage_units_in_meters=1.0)

# Locate Isaac Sim assets folder to load environment and robot stages
assets_root_path = nucleus.get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    simulation_app.close()
    sys.exit()

# Loading the simple_room environment
stage.add_reference_to_stage(assets_root_path + BACKGROUND_USD_PATH, BACKGROUND_STAGE_PATH)

# Creating a Camera prim
camera_prim = UsdGeom.Camera(omni.usd.get_context().get_stage().DefinePrim(CAMERA_STAGE_PATH, "Camera"))
xform_api = UsdGeom.XformCommonAPI(camera_prim)
xform_api.SetTranslate(Gf.Vec3d(-1, 5, 1))
xform_api.SetRotate((90, 0, 0), UsdGeom.XformCommonAPI.RotationOrderXYZ)
camera_prim.GetHorizontalApertureAttr().Set(21)
camera_prim.GetVerticalApertureAttr().Set(16)
camera_prim.GetProjectionAttr().Set("perspective")
camera_prim.GetFocalLengthAttr().Set(24)
camera_prim.GetFocusDistanceAttr().Set(400)

simulation_app.update()

# Creating an on-demand push graph with cameraHelper nodes to generate ROS image publishers

keys = og.Controller.Keys
(ros_camera_graph, _, _, _) = og.Controller.edit(
    {
        "graph_path": ROS_CAMERA_GRAPH_PATH,
        "evaluator_name": "push",
        "pipeline_stage": og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND,
    },
    {
        keys.CREATE_NODES: [
            ("OnTick", "omni.graph.action.OnTick"),
            ("createViewport", "omni.isaac.core_nodes.IsaacCreateViewport"),
            ("setActiveCamera", "omni.graph.ui.SetActiveViewportCamera"),
            ("cameraHelperRgb", "omni.isaac.ros_bridge.ROS1CameraHelper"),
            ("cameraHelperInfo", "omni.isaac.ros_bridge.ROS1CameraHelper"),
            ("cameraHelperDepth", "omni.isaac.ros_bridge.ROS1CameraHelper"),
        ],
        keys.CONNECT: [
            ("OnTick.outputs:tick", "createViewport.inputs:execIn"),
            ("createViewport.outputs:execOut", "setActiveCamera.inputs:execIn"),
            ("createViewport.outputs:viewport", "setActiveCamera.inputs:viewport"),
            ("setActiveCamera.outputs:execOut", "cameraHelperRgb.inputs:execIn"),
            ("setActiveCamera.outputs:execOut", "cameraHelperInfo.inputs:execIn"),
            ("setActiveCamera.outputs:execOut", "cameraHelperDepth.inputs:execIn"),
            ("createViewport.outputs:viewport", "cameraHelperRgb.inputs:viewport"),
            ("createViewport.outputs:viewport", "cameraHelperInfo.inputs:viewport"),
            ("createViewport.outputs:viewport", "cameraHelperDepth.inputs:viewport"),
        ],
        keys.SET_VALUES: [
            ("createViewport.inputs:viewportId", 0),
            ("setActiveCamera.inputs:primPath", CAMERA_STAGE_PATH),
            ("cameraHelperRgb.inputs:frameId", "sim_camera"),
            ("cameraHelperRgb.inputs:topicName", "rgb"),
            ("cameraHelperRgb.inputs:type", "rgb"),
            ("cameraHelperInfo.inputs:frameId", "sim_camera"),
            ("cameraHelperInfo.inputs:topicName", "camera_info"),
            ("cameraHelperInfo.inputs:type", "camera_info"),
            ("cameraHelperDepth.inputs:frameId", "sim_camera"),
            ("cameraHelperDepth.inputs:topicName", "depth"),
            ("cameraHelperDepth.inputs:type", "depth"),
        ],
    },
)

# Run the ROS Camera graph once to generate ROS image publishers in SDGPipeline
og.Controller.evaluate_sync(ros_camera_graph)

simulation_app.update()

# Re-route the execution connections in between each of the IsaacSimulationGate nodes and their downstream nodes to make them run through branch nodes.
# Since the SDGPipeline graph runs every frame, a branch node can act as a custom gate for our publishers.
# When the condition input of the branch node is set to True, the downstream nodes will operate whenever the IsaacSimulationGate node triggers an execution.
# By default the condition input of a branch node is set to False. Run the following code to setup the branch nodes:
SD_GRAPH_PATH = "/Render/PostProcess/SDGPipeline"

viewport_api = get_active_viewport()

if viewport_api is not None:
    import omni.syntheticdata._syntheticdata as sd

    curr_stage = omni.usd.get_context().get_stage()

    # Required for editing the SDGPipeline graph which exists in the Session Layer
    with Usd.EditContext(curr_stage, curr_stage.GetSessionLayer()):

        # Get name of rendervar for RGB sensor type
        rv_rgb = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.Rgb.name)

        # Get path to IsaacSimulationGate node in RGB pipeline
        rgb_camera_gate_path = omni.syntheticdata.SyntheticData._get_node_path(
            rv_rgb + "IsaacSimulationGate", viewport_api.get_render_product_path()
        )

        # Get path to IsaacConvertRGBAToRGB node in RGB pipeline
        rgb_conversion_path = omni.syntheticdata.SyntheticData._get_node_path(
            rv_rgb + "IsaacConvertRGBAToRGB", viewport_api.get_render_product_path()
        )

        # Get name of rendervar for DistanceToImagePlane sensor type
        rv_depth = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(
            sd.SensorType.DistanceToImagePlane.name
        )

        # Get path to IsaacSimulationGate node in Depth pipeline
        depth_camera_gate_path = omni.syntheticdata.SyntheticData._get_node_path(
            rv_depth + "IsaacSimulationGate", viewport_api.get_render_product_path()
        )

        # Get path to ROS1PublishImage node in Depth pipeline
        depth_publisher_path = omni.syntheticdata.SyntheticData._get_node_path(
            rv_depth + "ROS1PublishImage", viewport_api.get_render_product_path()
        )

        # Get path to IsaacSimulationGate node in CameraInfo pipeline
        camera_info_gate_path = omni.syntheticdata.SyntheticData._get_node_path(
            "PostProcessDispatch" + "IsaacSimulationGate", viewport_api.get_render_product_path()
        )

        # Get path to ROS1PublishCameraInfo node in CameraInfo pipeline
        camera_info_publisher_path = omni.syntheticdata.SyntheticData._get_node_path(
            "ROS1PublishCameraInfo", viewport_api.get_render_product_path()
        )

        # In SDGPipeline graph, we will re-route execution connections to manually publish ROS images
        keys = og.Controller.Keys
        og.Controller.edit(
            SD_GRAPH_PATH,
            {
                keys.CREATE_NODES: [
                    # Creating Branch nodes that will allow manual publishing of ROS images
                    ("RgbPublisherBranch", "omni.graph.action.Branch"),
                    ("DepthPublisherBranch", "omni.graph.action.Branch"),
                    ("InfoPublisherBranch", "omni.graph.action.Branch"),
                ],
                keys.DISCONNECT: [
                    # Disconnecting the exec connections between each IsaacSimulationGate node and their downstream node
                    (rgb_camera_gate_path + ".outputs:execOut", rgb_conversion_path + ".inputs:execIn"),
                    (depth_camera_gate_path + ".outputs:execOut", depth_publisher_path + ".inputs:execIn"),
                    (camera_info_gate_path + ".outputs:execOut", camera_info_publisher_path + ".inputs:execIn"),
                ],
                keys.CONNECT: [
                    # Connecting the execution output of each IsaacSimulationGate node to the execution input of their respective branch node
                    (rgb_camera_gate_path + ".outputs:execOut", SD_GRAPH_PATH + "/RgbPublisherBranch.inputs:execIn"),
                    (
                        depth_camera_gate_path + ".outputs:execOut",
                        SD_GRAPH_PATH + "/DepthPublisherBranch.inputs:execIn",
                    ),
                    (camera_info_gate_path + ".outputs:execOut", SD_GRAPH_PATH + "/InfoPublisherBranch.inputs:execIn"),
                    # Connecting the execution True output of each Branch node to the execution input of the respective downstream nodes
                    (SD_GRAPH_PATH + "/RgbPublisherBranch.outputs:execTrue", rgb_conversion_path + ".inputs:execIn"),
                    (SD_GRAPH_PATH + "/DepthPublisherBranch.outputs:execTrue", depth_publisher_path + ".inputs:execIn"),
                    (
                        SD_GRAPH_PATH + "/InfoPublisherBranch.outputs:execTrue",
                        camera_info_publisher_path + ".inputs:execIn",
                    ),
                ],
            },
        )

# Need to initialize physics getting any articulation..etc
simulation_context.initialize_physics()

simulation_context.play()

frame = 0

while simulation_app.is_running():
    # Run with a fixed step size
    simulation_context.step(render=True)

    # Rotate camera by 0.5 degree every frame
    xform_api.SetRotate((90, 0, frame / 4.0), UsdGeom.XformCommonAPI.RotationOrderXYZ)

    # Disable the Branch nodes to stop publishers by setting the condition inputs to False
    og.Controller.set(og.Controller.attribute(SD_GRAPH_PATH + "/RgbPublisherBranch.inputs:condition"), False)
    og.Controller.set(og.Controller.attribute(SD_GRAPH_PATH + "/DepthPublisherBranch.inputs:condition"), False)
    og.Controller.set(og.Controller.attribute(SD_GRAPH_PATH + "/InfoPublisherBranch.inputs:condition"), False)

    # Publish the ROS rgb image message every 5 frames
    if frame % 5 == 0:
        # Enable rgb Branch node to start publishing rgb image
        og.Controller.set(og.Controller.attribute(SD_GRAPH_PATH + "/RgbPublisherBranch.inputs:condition"), True)

    # Publish the ROS Depth image message every 60 frames
    if frame % 60 == 0:
        # Enable depth Branch node to start publishing depth image
        og.Controller.set(og.Controller.attribute(SD_GRAPH_PATH + "/DepthPublisherBranch.inputs:condition"), True)

    # Publish the ROS Camera Info message every frame
    og.Controller.set(og.Controller.attribute(SD_GRAPH_PATH + "/InfoPublisherBranch.inputs:condition"), True)

    frame = frame + 1

simulation_context.stop()
simulation_app.close()
