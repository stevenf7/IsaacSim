# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


# python
from typing import Optional
import numpy as np

# omniverse
from pxr import UsdGeom, Gf
import omni.kit.commands
import omni.kit.viewport_legacy
import omni.usd
import omni.graph.core as og
from omni.isaac.quadruped.robots import Unitree


class UnitreeVision(Unitree):
    """[Summary]
    
    For unitree based quadrupeds (A1 or Go1) with camera
    """

    def __init__(
        self,
        prim_path: str,
        name: str = "unitree_quadruped",
        physics_dt: Optional[float] = 1 / 400.0,
        usd_path: Optional[str] = None,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        model: Optional[str] = "A1",
        is_ros2: Optional[bool] = False,
        way_points: Optional[np.ndarray] = None,
    ) -> None:
        """
        [Summary]
        
        initialize robot, set up sensors and controller
        
        Arguments:
            prim_path {str} -- prim path of the robot on the stage
            name {str} -- name of the quadruped
            physics_dt {float} -- physics downtime of the controller
            usd_path {str} -- robot usd filepath in the directory
            position {np.ndarray} -- position of the robot
            orientation {np.ndarray} -- orientation of the robot
            model {str} -- robot model (can be either A1 or Go1)
            way_points {np.ndarray} -- waypoints for the robot

        """
        super().__init__(prim_path, name, physics_dt, usd_path, position, orientation, model, way_points)

        self.image_width = 640
        self.image_height = 480

        self.cameras = [
            # 0name, 1offset, 2orientation, 3hori aperture, 4vert aperture, 5projection, 6focal length, 7focus distance
            ("/camera_left", Gf.Vec3d(0.2693, 0.025, 0.067), (90, 0, -90), 21, 16, "perspective", 24, 400),
            ("/camera_right", Gf.Vec3d(0.2693, -0.025, 0.067), (90, 0, -90), 21, 16, "perspective", 24, 400),
        ]
        self.camera_graphs = []

        # after stage is defined
        self._stage = omni.usd.get_context().get_stage()

        # add cameras on the imu link
        for i in range(len(self.cameras)):
            # add camera prim
            camera = self.cameras[i]
            camera_path = self._prim_path + "/imu_link" + camera[0]
            camera_prim = UsdGeom.Camera(self._stage.DefinePrim(camera_path, "Camera"))
            xform_api = UsdGeom.XformCommonAPI(camera_prim)
            xform_api.SetRotate(camera[2], UsdGeom.XformCommonAPI.RotationOrderXYZ)
            xform_api.SetTranslate(camera[1])
            camera_prim.GetHorizontalApertureAttr().Set(camera[3])
            camera_prim.GetVerticalApertureAttr().Set(camera[4])
            camera_prim.GetProjectionAttr().Set(camera[5])
            camera_prim.GetFocalLengthAttr().Set(camera[6])
            camera_prim.GetFocusDistanceAttr().Set(camera[7])

            self.is_ros2 = is_ros2

            ros_version = "ROS1"
            ros_bridge_version = "ros_bridge."
            self.ros_vp_offset = 1
            if self.is_ros2:
                ros_version = "ROS2"
                ros_bridge_version = "ros2_bridge."
                self.ros_vp_offset = 0  # Only create 2 viewports

            # Creating an on-demand push graph with cameraHelper nodes to generate ROS image publishers

            keys = og.Controller.Keys
            (camera_graph, _, _, _) = og.Controller.edit(
                {
                    "graph_path": "/ROS_" + camera[0].split("/")[-1],
                    "evaluator_name": "push",
                    "pipeline_stage": og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND,
                },
                {
                    keys.CREATE_NODES: [
                        ("OnTick", "omni.graph.action.OnTick"),
                        ("createViewport", "omni.isaac.core_nodes.IsaacCreateViewport"),
                        ("setActiveCamera", "omni.graph.ui.SetActiveViewportCamera"),
                        ("cameraHelperRgb", "omni.isaac." + ros_bridge_version + ros_version + "CameraHelper"),
                        ("cameraHelperInfo", "omni.isaac." + ros_bridge_version + ros_version + "CameraHelper"),
                    ],
                    keys.CONNECT: [
                        ("OnTick.outputs:tick", "createViewport.inputs:execIn"),
                        ("createViewport.outputs:execOut", "setActiveCamera.inputs:execIn"),
                        ("createViewport.outputs:viewport", "setActiveCamera.inputs:viewport"),
                        ("setActiveCamera.outputs:execOut", "cameraHelperRgb.inputs:execIn"),
                        ("setActiveCamera.outputs:execOut", "cameraHelperInfo.inputs:execIn"),
                        ("createViewport.outputs:viewport", "cameraHelperRgb.inputs:viewport"),
                        ("createViewport.outputs:viewport", "cameraHelperInfo.inputs:viewport"),
                    ],
                    keys.SET_VALUES: [
                        ("createViewport.inputs:viewportId", i + self.ros_vp_offset),
                        ("setActiveCamera.inputs:primPath", camera_path),
                        ("cameraHelperRgb.inputs:frameId", camera[0]),
                        ("cameraHelperRgb.inputs:nodeNamespace", "/isaac_a1"),
                        ("cameraHelperRgb.inputs:topicName", "camera_forward" + camera[0] + "/rgb"),
                        ("cameraHelperRgb.inputs:type", "rgb"),
                        ("cameraHelperInfo.inputs:frameId", camera[0]),
                        ("cameraHelperInfo.inputs:nodeNamespace", "/isaac_a1"),
                        ("cameraHelperInfo.inputs:topicName", camera[0] + "/camera_info"),
                        ("cameraHelperInfo.inputs:type", "camera_info"),
                    ],
                },
            )

            self.camera_graphs.append(camera_graph)

        for graph in self.camera_graphs:
            og.Controller.evaluate_sync(graph)

        self.vp_interface = omni.kit.viewport_legacy.get_viewport_interface()
        self.viewports = []
        for instance in self.vp_interface.get_instance_list():
            viewport = self.vp_interface.get_viewport_window(instance)

            viewport.set_window_size(self.image_width + 8, self.image_height + 30)
            viewport.set_texture_resolution(self.image_width, self.image_height)

            self.viewports.append(viewport)

        self.dockViewports()
        self.setCameraExeutionStep(1)

    def dockViewports(self) -> None:
        """
        [Summary]
    
        For instantiating and docking view ports
        """
        # first, set main viewport
        main_viewport = omni.kit.viewport_legacy.get_default_viewport_window()
        main_viewport.set_camera_position("/OmniverseKit_Persp", 3, 3, 3, True)
        main_viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)
        main_viewport.set_camera_move_velocity(0)

        left_camera_viewport = omni.ui.Workspace.get_window("Viewport 2")
        right_camera_viewport = omni.ui.Workspace.get_window("Viewport 3")
        if main_viewport is not None and left_camera_viewport is not None and right_camera_viewport is not None:
            left_camera_viewport.dock_in(self.main_viewport, omni.ui.DockPosition.RIGHT, 2 / 3.0)
            right_camera_viewport.dock_in(left_camera_viewport, omni.ui.DockPosition.RIGHT, 0.5)

    def setCameraExeutionStep(self, step: np.uint) -> None:
        """
        [Summary]
        
        Sets the execution step in the omni.isaac.core_nodes.IsaacSimulationGate node located in the camera sensor pipeline

        """
        for viewport in self.viewports[self.ros_vp_offset :]:
            if viewport is not None:
                import omni.syntheticdata._syntheticdata as sd

                rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.Rgb.name)
                rgb_camera_gate_path = omni.syntheticdata.SyntheticData._get_node_path(
                    rv + "IsaacSimulationGate", viewport.get_render_product_path()
                )

                camera_info_gate_path = omni.syntheticdata.SyntheticData._get_node_path(
                    "PostProcessDispatch" + "IsaacSimulationGate", viewport.get_render_product_path()
                )
                og.Controller.attribute(rgb_camera_gate_path + ".inputs:step").set(step)
                og.Controller.attribute(camera_info_gate_path + ".inputs:step").set(step)

    def update(self) -> None:
        """
        [Summary]
        
        Update robot variables from the environment

        """
        super().update()

    def advance(self, dt, goal, path_follow=False) -> np.ndarray:
        """[summary]
        
        calls the unitree advance to compute torque
        
        Argument:
        dt {float} -- Timestep update in the world.
        goal {List[int]} -- x velocity, y velocity, angular velocity, state switch
        path_follow {bool} -- True for following a set of coordinates, False for keyboard control

        Returns:
        np.ndarray -- The desired joint torques for the robot.
        """
        super().advance(dt, goal, path_follow)
