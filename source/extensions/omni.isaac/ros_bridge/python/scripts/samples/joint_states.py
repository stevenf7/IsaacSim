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
from pxr import PhysicsSchema, Sdf
import omni.usd
import omni
import omni.kit.ui
import omni.kit.editor
import omni.isaac.RosBridgeSchema as ROSSchema
from omni.isaac.utils.scripts.test_utils import load_test_file
import asyncio


class Extension(omni.ext.IExt):
    def on_startup(self):
        # setting up the UI on the menu bar for this example
        self._window = omni.kit.ui.Window(
            "Joint State",
            300,
            200,
            menu_path="Isaac Robotics/ROS/Joint State",
            open=False,
            dock=omni.kit.ui.DockPreference.LEFT_BOTTOM,
        )
        sublayout = self._window.layout.add_child(omni.kit.ui.ColumnLayout())
        load_robot_btn = sublayout.add_child(omni.kit.ui.Button("Load Robot"))
        load_robot_btn.set_clicked_fn(self._on_load_robot)

        connect_js_btn = sublayout.add_child(omni.kit.ui.Button("Connect Joint State Node"))
        connect_js_btn.set_clicked_fn(self._on_connect_js)

        connect_camera_btn = sublayout.add_child(omni.kit.ui.Button("Connect Camera Node"))
        connect_camera_btn.set_clicked_fn(self._on_connect_camera)

        self._editor_event_subscription = None
        self._editor = omni.kit.editor.get_editor_interface()

    def on_shutdown(self):
        self._window = None

    # loading the robot
    def _on_load_robot(self, widget):
        asyncio.ensure_future(load_test_file("assets/robots/franka/franka.usd"))

    # Starting up the joint_state rosnode and connect it to the robot
    def _on_connect_js(self, widget):
        # check robot is loaded and articulation exist
        self.stage = omni.usd.get_context().get_stage()
        robot_prim = self.stage.GetPrimAtPath("/panda")
        assert robot_prim.HasAPI(PhysicsSchema.ArticulationAPI)

        # setup ROSnode to publish and receive joint state info
        js_prim = ROSSchema.RosJointState.Define(self.stage, Sdf.Path("/ROS_JointState"))

        # adding prefix to the published /joint_state topic if needed
        js_prim.CreateRosNodePrefixAttr("")
        js_prim.CreateEnabledAttr(True)

        # publisher topic
        js_prim.CreateJointStatePubTopicAttr("/joint_state")
        # subscripber topic
        js_prim.CreateJointStateSubTopicAttr("/joint_command")

        js_prim.CreateArticulationPrimRel()
        js_prim.CreateQueueSizeAttr(0)

        # The joint_state rosnode must be connected to the root of the robot's articulation in order to publish its states
        ROS_prim = self.stage.GetPrimAtPath("/ROS_JointState")
        ROS_prim.GetRelationship("articulationPrim").SetTargets(["/panda"])

        # editor must be playing for messages to be published and received
        if not self._editor.is_playing():
            self._editor.play()

    # adding camera topic
    def _on_connect_camera(self, widget):
        # add camera prim to path
        camera_prim = ROSSchema.RosCamera.Define(self.stage, Sdf.Path("/ROS_Camera"))
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

        # enable RGB
        camera_prim.CreateRgbEnabledAttr(True)
        # enable depth
        camera_prim.CreateDepthEnabledAttr(True)
        camera_prim.CreateQueueSizeAttr(10)

        # make sure editor is playing for sending and receiving ros messages
        if not self._editor.is_playing():
            self._editor.play()

        # use image_view to view the published image:
        # rosrun image_view image_view image:=/rgb
        # rosrun image_view image_view image:=/depth
