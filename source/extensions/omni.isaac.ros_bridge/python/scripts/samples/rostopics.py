# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# This is an example script showing how to use rosbridge to publish joint_states of an articulated robot

import carb
from pxr import UsdPhysics, Sdf, Gf, UsdGeom, PhysxSchema
import omni.usd
import omni
import omni.ui as ui
import omni.isaac.RosBridgeSchema as ROSSchema
from omni.isaac.utils.scripts.test_utils import load_test_file
import asyncio
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
import weakref
import math

EXTENSION_NAME = "Ros Topics"


def set_drive_parameters(drive, target_type, target_value, stiffness, damping, max_force=None):
    """Enable velocity drive for a given joint"""

    if target_type == "position":
        if not drive.GetTargetPositionAttr():
            drive.CreateTargetPositionAttr(target_value)
        else:
            drive.GetTargetPositionAttr().Set(target_value)
    elif target_type == "velocity":
        if not drive.GetTargetVelocityAttr():
            drive.CreateTargetVelocityAttr(target_value)
        else:
            drive.GetTargetVelocityAttr().Set(target_value)

    if not drive.GetStiffnessAttr():
        drive.CreateStiffnessAttr(stiffness)
    else:
        drive.GetStiffnessAttr().Set(stiffness)

    if not drive.GetDampingAttr():
        drive.CreateDampingAttr(damping)
    else:
        drive.GetDampingAttr().Set(damping)

    if max_force is not None:
        if not drive.GetMaxForceAttr():
            drive.CreateMaxForceAttr(max_force)
        else:
            drive.GetMaxForceAttr().Set(max_force)


class Extension(omni.ext.IExt):
    def on_startup(self):
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dynamic_control")
        self._dc_extension_path = ext_manager.get_extension_path(ext_id)
        # setting up the UI on the menu bar for this example
        self._window = omni.ui.Window(EXTENSION_NAME, width=600, height=400, visible=False)
        menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        self._menu_items = [
            MenuItemDescription(name="Communicating", sub_menu=[MenuItemDescription(name="ROS", sub_menu=menu_items)])
        ]
        add_menu_items(self._menu_items, "Isaac Examples")
        with self._window.frame:
            with ui.VStack():
                ui.Button("Load Robot", tooltip="Loads robot into stage", clicked_fn=self._on_load_robot)
                with ui.HStack(height=0):
                    ui.Label("Control Mode")
                    self._velocity_combo = ui.ComboBox(0, "Position Control", "Velocity Control").model
                    ui.Button(
                        "Connect Joint State Topics",
                        tooltip="start a joint_state and joint_command topic to publish and receive joint states",
                        clicked_fn=self._on_connect_js,
                    )
                ui.Button(
                    "Connect Camera Topics",
                    tooltip="Connect Camera Ros Topics and start publishing",
                    clicked_fn=self._on_connect_camera,
                )
                ui.Button(
                    "Connect TF Topics",
                    tooltip="Connect TF Ros Topics and start publishing",
                    clicked_fn=self._on_connect_tf,
                )
                ui.Button(
                    "Add Cube", tooltip="Add a Cube to the scene and append to TF tree", clicked_fn=self._on_add_cube
                )

        self._stage = omni.usd.get_context().get_stage()
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._timeline = omni.timeline.get_timeline_interface()

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    # Fix camera location and angle
    async def _setup_camera(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            self._viewport.set_camera_position("/OmniverseKit_Persp", 59, 120, 164, True)
            self._viewport.set_camera_target("/OmniverseKit_Persp", -190, -346, -263, True)

            # timeline must be playing for articulation to work, so start it now
            if not self._timeline.is_playing():
                self._timeline.play()

    # load robot
    def _on_load_robot(self):
        task = asyncio.ensure_future(load_test_file(self._dc_extension_path + "/data/usd/robots/franka/franka.usd"))
        asyncio.ensure_future(self._setup_camera(task))

    def _on_connect_js(self):

        # check robot is loaded and articulation exist
        self._stage = omni.usd.get_context().get_stage()
        robot_prim = self._stage.GetPrimAtPath("/panda")
        assert robot_prim.HasAPI(PhysxSchema.PhysxArticulationAPI)

        # setup Rostopic to publish and receive joint state info
        js_prim = ROSSchema.RosJointState.Define(self._stage, Sdf.Path("/ROS_JointState"))

        # adding prefix to the published /joint_states topic if needed
        js_prim.CreateEnabledAttr(True)
        # publisher topic
        js_prim.CreateJointStatePubTopicAttr("/joint_states")
        # subscriber topic
        js_prim.CreateJointStateSubTopicAttr("/joint_command")

        js_prim.CreateArticulationPrimRel()
        js_prim.CreateQueueSizeAttr(0)

        # The joint_state rostopic must be connected to the root of the robot's articulation in order to publish its states
        ROS_prim = self._stage.GetPrimAtPath("/ROS_JointState")
        ROS_prim.GetRelationship("articulationPrim").SetTargets(["/panda"])
        panda_joint1_drive = UsdPhysics.DriveAPI.Get(
            self._stage.GetPrimAtPath("/panda/panda_link0/panda_joint1"), "angular"
        )
        panda_joint2_drive = UsdPhysics.DriveAPI.Get(
            self._stage.GetPrimAtPath("/panda/panda_link1/panda_joint2"), "angular"
        )
        panda_joint3_drive = UsdPhysics.DriveAPI.Get(
            self._stage.GetPrimAtPath("/panda/panda_link2/panda_joint3"), "angular"
        )
        panda_joint4_drive = UsdPhysics.DriveAPI.Get(
            self._stage.GetPrimAtPath("/panda/panda_link3/panda_joint4"), "angular"
        )
        panda_joint5_drive = UsdPhysics.DriveAPI.Get(
            self._stage.GetPrimAtPath("/panda/panda_link4/panda_joint5"), "angular"
        )
        panda_joint6_drive = UsdPhysics.DriveAPI.Get(
            self._stage.GetPrimAtPath("/panda/panda_link5/panda_joint6"), "angular"
        )
        panda_joint7_drive = UsdPhysics.DriveAPI.Get(
            self._stage.GetPrimAtPath("/panda/panda_link6/panda_joint7"), "angular"
        )
        panda_finger1_drive = UsdPhysics.DriveAPI.Get(
            self._stage.GetPrimAtPath("/panda/panda_hand/panda_finger_joint1"), "linear"
        )
        panda_finger2_drive = UsdPhysics.DriveAPI.Get(
            self._stage.GetPrimAtPath("/panda/panda_hand/panda_finger_joint2"), "linear"
        )

        if self._velocity_combo.get_item_value_model().as_int == 1:
            # set all joints to velocity control
            set_drive_parameters(panda_joint1_drive, "velocity", 0.0, 0, math.radians(1e7), 1e8)
            set_drive_parameters(panda_joint2_drive, "velocity", 0.0, 0, math.radians(1e7), 1e8)
            set_drive_parameters(panda_joint3_drive, "velocity", 0.0, 0, math.radians(1e7), 1e8)
            set_drive_parameters(panda_joint4_drive, "velocity", 0.0, 0, math.radians(1e7), 1e8)
            set_drive_parameters(panda_joint5_drive, "velocity", 0.0, 0, math.radians(1e7), 1e8)
            set_drive_parameters(panda_joint6_drive, "velocity", 0.0, 0, math.radians(1e7), 1e8)
            set_drive_parameters(panda_joint7_drive, "velocity", 0.0, 0, math.radians(1e7), 1e8)

        else:
            # set all joints to position control
            set_drive_parameters(
                panda_joint1_drive, "position", math.degrees(0.0), math.radians(60000), math.radians(3000), 87000
            )
            set_drive_parameters(
                panda_joint2_drive, "position", math.degrees(-1.3), math.radians(60000), math.radians(3000), 87000
            )
            set_drive_parameters(
                panda_joint3_drive, "position", math.degrees(0.0), math.radians(60000), math.radians(3000), 87000
            )
            set_drive_parameters(
                panda_joint4_drive, "position", math.degrees(-2.87), math.radians(60000), math.radians(3000), 87000
            )
            set_drive_parameters(
                panda_joint5_drive, "position", math.degrees(0), math.radians(25000), math.radians(3000), 12000
            )
            set_drive_parameters(
                panda_joint6_drive, "position", math.degrees(2), math.radians(25000), math.radians(3000), 12000
            )
            set_drive_parameters(
                panda_joint7_drive, "position", math.degrees(0.75), math.radians(5000), math.radians(3000), 12000
            )
            set_drive_parameters(panda_finger1_drive, "position", 0, math.radians(6000), math.radians(1000), 1200)
            set_drive_parameters(panda_finger2_drive, "position", 0, math.radians(6000), math.radians(1000), 1200)

    # adding camera topic
    def _on_connect_camera(self):
        self._stage = omni.usd.get_context().get_stage()
        # add camera prim to path
        camera_prim = ROSSchema.RosCamera.Define(self._stage, Sdf.Path("/ROS_Camera"))
        # adding prefix to the publisher topic if needed
        camera_prim.CreateRosNodePrefixAttr("")
        camera_prim.CreateEnabledAttr(True)
        # publisher topic for camera_info
        camera_prim.CreateCameraInfoPubTopicAttr("/camera_info")
        # publisher topic for rgb
        camera_prim.CreateRgbPubTopicAttr("/rgb")
        # publisher topic for depth
        camera_prim.CreateDepthPubTopicAttr("/depth")
        camera_prim.CreateFrameIdAttr("/sim_camera")

        # enable existing viewport
        camera_prim.CreateUseExistingViewportAttr(True)
        # enable RGB
        camera_prim.CreateRgbEnabledAttr(True)
        # enable depth
        camera_prim.CreateDepthEnabledAttr(True)
        camera_prim.CreateQueueSizeAttr(10)

        # make sure timeline is playing for sending and receiving ros messages
        if not self._timeline.is_playing():
            self._timeline.play()

        # use image_view to view the published image:
        # rosrun image_view image_view image:=/rgb
        # rosrun image_view image_view image:=/depth

    # adding the tf topic
    def _on_connect_tf(self):
        self._stage = omni.usd.get_context().get_stage()
        # setup rostpic for the tf tree
        tf_prim = ROSSchema.RosPoseTree.Define(self._stage, Sdf.Path("/ROS_PoseTree"))
        tf_prim.CreateEnabledAttr(True)
        # create the publishing topic
        tf_prim.CreatePoseTreePubTopicAttr("/tf")
        tf_prim.CreateTargetPrimsRel()
        tf_prim.CreateQueueSizeAttr(0)

        # The tf rostopic must be connected to the root of the robot's articulation in order to publish its transforms
        ROS_prim = self._stage.GetPrimAtPath("/ROS_PoseTree")
        # if one doesn't exist already, create one.
        if not ROS_prim:
            # create the topic if one does not exist
            tf_prim = ROSSchema.RosPoseTree.Define(self._stage, Sdf.Path("/ROS_PoseTree"))
            tf_prim.CreateEnabledAttr(True)
            # create the publishing topic
            tf_prim.CreatePoseTreePubTopicAttr("/tf")
            tf_prim.CreateTargetPrimsRel()
            tf_prim.CreateQueueSizeAttr(0)
            ROS_prim.GetRelationship("targetPrims").SetTargets(["/panda"])
        else:
            ROS_prim.GetRelationship("targetPrims").AddTarget(Sdf.Path("/panda"))

        # timeline must be playing for messages to be published and received
        if not self._timeline.is_playing():
            self._timeline.play()

    def _on_add_cube(self):
        # first create a cube
        self._stage = omni.usd.get_context().get_stage()
        CubePath = "/cube"
        # offset to some position in space
        offset = Gf.Vec3f(50.0, 0.0, 50.0)
        size = 10  # cm
        cubeGeom = UsdGeom.Cube.Define(self._stage, CubePath)
        cubeGeom.CreateSizeAttr(size)
        cubeGeom.AddTranslateOp().Set(offset)

        # add the cube to tf tree
        ROS_prim = self._stage.GetPrimAtPath("/ROS_PoseTree")
        if not ROS_prim:
            # create the topic if one does not exist
            tf_prim = ROSSchema.RosPoseTree.Define(self._stage, Sdf.Path("/ROS_PoseTree"))
            tf_prim.CreateEnabledAttr(True)
            # create the publishing topic
            tf_prim.CreatePoseTreePubTopicAttr("/tf")
            tf_prim.CreateTargetPrimsRel()
            tf_prim.CreateQueueSizeAttr(0)
            ROS_prim = self._stage.GetPrimAtPath("/ROS_PoseTree")
            ROS_prim.GetRelationship("targetPrims").SetTargets(["/cube"])
        else:
            ROS_prim.GetRelationship("targetPrims").AddTarget(Sdf.Path("/cube"))
