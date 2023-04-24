# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import omni.graph.core as og
import omni.kit.commands
import omni.usd
from omni.kit.viewport.utility import get_num_viewports
from omni.usd.commands import DeletePrimsCommand
from pxr import Gf, UsdGeom


def delete_prim_and_children(prim_path: str):
    """deleting the prim at given path as well as all its children"""
    DeletePrimsCommand([prim_path]).do()


def add_physx_lidar(prim_path, translation=Gf.Vec3f(0, 0, 0), orientation=Gf.Vec4f(0, 0, 0, 0)):
    result, lidar = omni.kit.commands.execute(
        "RangeSensorCreateLidar",
        path=prim_path,
        parent=None,
        min_range=0.4,
        max_range=100.0,
        draw_points=True,
        draw_lines=True,
        horizontal_fov=360.0,
        vertical_fov=30.0,
        horizontal_resolution=0.4,
        vertical_resolution=4.0,
        rotation_rate=0.0,
        high_lod=False,
        yaw_offset=0.0,
    )
    lidar_prim = lidar.GetPrim()

    if "xformOp:translate" not in lidar_prim.GetPropertyNames():
        UsdGeom.Xformable(lidar_prim).AddTranslateOp()
    if "xformOp:orient" not in lidar_prim.GetPropertyNames():
        UsdGeom.Xformable(lidar_prim).AddOrientOp()

    lidar_prim.GetAttribute("xformOp:translate").Set(translation)
    lidar_prim.GetAttribute("xformOp:orient").Set(orientation)


def add_ros_camera(
    camera_prim_path,
    graph_path=None,
    camera_topic=None,
    sim_camera_id=None,
    viewport_name=None,
    viewport_resolution=[1280, 720],
    # camera_info_topic=None,
    # sim_camera_info_id=None,
    # camera_info = None,
):

    n_viewport = get_num_viewports()
    if not viewport_name:
        viewport_name = "Viewport " + str(n_viewport)  # assuming the viewports are 0-indexed
        print("new viewport named {}".format(viewport_name))
    if not camera_topic:
        camera_topic = "/rgb_" + str(n_viewport)
    if not graph_path:
        graph_path = "/ROS_camera_" + str(n_viewport)
    if not sim_camera_id:
        sim_camera_id = "sim_camera" + str(n_viewport)

    (ros_camera_graph, _, _, _) = og.Controller.edit(
        {"graph_path": graph_path, "evaluator_name": "execution"},
        {
            og.Controller.Keys.CREATE_NODES: [
                ("OnTick", "omni.graph.action.OnTick"),
                ("createViewport", "omni.isaac.core_nodes.IsaacCreateViewport"),
                ("setActiveCamera", "omni.graph.ui.SetActiveViewportCamera"),
                ("setViewportResolution", "omni.isaac.core_nodes.IsaacSetViewportResolution"),
                ("cameraHelperRgb", "omni.isaac.ros_bridge.ROS1CameraHelper"),
                # ("cameraHelperInfo", "omni.isaac.ros_bridge.ROS1CameraHelper"),
            ],
            og.Controller.Keys.CONNECT: [
                ("OnTick.outputs:tick", "createViewport.inputs:execIn"),
                ("createViewport.outputs:execOut", "setActiveCamera.inputs:execIn"),
                ("createViewport.outputs:viewport", "setActiveCamera.inputs:viewport"),
                ("createViewport.outputs:execOut", "setViewportResolution.inputs:execIn"),
                ("createViewport.outputs:viewport", "setViewportResolution.inputs:viewport"),
                ("setActiveCamera.outputs:execOut", "cameraHelperRgb.inputs:execIn"),
                # ("setActiveCamera.outputs:execOut", "cameraHelperInfo.inputs:execIn"),
                ("createViewport.outputs:viewport", "cameraHelperRgb.inputs:viewport"),
                # ("createViewport.outputs:viewport", "cameraHelperInfo.inputs:viewport"),
            ],
            og.Controller.Keys.SET_VALUES: [
                ("createViewport.inputs:name", viewport_name),
                ("setActiveCamera.inputs:primPath", camera_prim_path),
                ("setViewportResolution.inputs:height", int(viewport_resolution[1])),
                ("setViewportResolution.inputs:width", int(viewport_resolution[0])),
                ("cameraHelperRgb.inputs:frameId", sim_camera_id),
                ("cameraHelperRgb.inputs:topicName", camera_topic),
                ("cameraHelperRgb.inputs:type", "rgb"),
                # ("cameraHelperInfo.inputs:frameId", sim_camera_info_id),
                # ("cameraHelperInfo.inputs:topicName", camera_info_topic),
                # ("cameraHelperInfo.inputs:type", camera_info),
            ],
        },
    )

    return ros_camera_graph
