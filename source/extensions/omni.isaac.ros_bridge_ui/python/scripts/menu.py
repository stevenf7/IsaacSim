# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import omni.kit.commands

from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from pxr import Gf
import weakref


class RosBridgeMenu:
    def __init__(self):
        self._usd_context = omni.usd.get_context()
        self._menus = []

        menu_items = [
            MenuItemDescription(name="Clock", onclick_fn=lambda a=weakref.proxy(self): a.add_clock()),
            MenuItemDescription(name="Camera", onclick_fn=lambda a=weakref.proxy(self): a.add_camera()),
            MenuItemDescription(name="Joint State", onclick_fn=lambda a=weakref.proxy(self): a.add_joint_state()),
            MenuItemDescription(name="Lidar", onclick_fn=lambda a=weakref.proxy(self): a.add_lidar()),
            MenuItemDescription(name="Pose Tree", onclick_fn=lambda a=weakref.proxy(self): a.add_pose_tree()),
            MenuItemDescription(name="Teleport", onclick_fn=lambda a=weakref.proxy(self): a.add_teleport()),
            MenuItemDescription(
                name="Surface Gripper", onclick_fn=lambda a=weakref.proxy(self): a.add_surface_gripper()
            ),
            MenuItemDescription(
                name="Differential Base", onclick_fn=lambda a=weakref.proxy(self): a.add_differential_base()
            ),
        ]

        self._menu_items = [
            MenuItemDescription(
                name="Isaac", glyph="plug.svg", sub_menu=[MenuItemDescription(name="ROS", sub_menu=menu_items)]
            )
        ]
        add_menu_items(self._menu_items, "Create")

    def _get_stage_and_path(self):
        self._stage = omni.usd.get_context().get_stage()
        selectedPrims = omni.usd.get_context().get_selection().get_selected_prim_paths()

        if len(selectedPrims) > 0:
            curr_prim = selectedPrims[-1]
        else:
            curr_prim = None
        return curr_prim

    def add_camera(self):
        result, prim = omni.kit.commands.execute(
            "ROSBridgeCreateCamera", path="/ROS_Camera", parent=self._get_stage_and_path()
        )

        pass

    def add_clock(self):
        result, prim = omni.kit.commands.execute(
            "ROSBridgeCreateClock", path="/ROS_Clock", parent=self._get_stage_and_path()
        )
        pass

    def add_joint_state(self):
        result, prim = omni.kit.commands.execute(
            "ROSBridgeCreateJointState", path="/ROS_JointState", parent=self._get_stage_and_path()
        )
        pass

    def add_lidar(self):
        result, prim = omni.kit.commands.execute(
            "ROSBridgeCreateLidar", path="/ROS_Lidar", parent=self._get_stage_and_path()
        )
        pass

    def add_pose_tree(self):
        result, prim = omni.kit.commands.execute(
            "ROSBridgeCreatePoseTree", path="/ROS_PoseTree", parent=self._get_stage_and_path()
        )

        pass

    # def add_sink(self):
    #     prim = ROSSchema.RosSink.Define(self._stage, self.get_path("/ROS_Sink"))
    #     self.setup_base_prim(prim)
    #     prim.CreatePosePubTopicAttr("/body_pos")
    #     prim.CreateVelPubTopicAttr("/body_vel")
    #     prim.CreateAccPubTopicAttr("/body_acc")

    #     prim.CreateTargetPrimsRel()
    #     prim.CreateQueueSizeAttr(0)

    #     pass

    def add_teleport(self):
        result, prim = omni.kit.commands.execute(
            "ROSBridgeCreateTeleport", path="/ROS_Teleport", parent=self._get_stage_and_path()
        )

        pass

    def add_surface_gripper(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "ROSBridgeCreateSurfaceGripper",
            path="/ROS_SurfaceGripper",
            parent=self._get_stage_and_path(),
            d6_joint_prim_rel=None,
            parent_prim_rel=None,
            gripper_entity="gripper",
            grip_threshold=1,
            force_limit=1e10,
            torque_limit=1e10,
            bend_angle=0,
            stiffness=1e10,
            damping=1e3,
            offset_position=Gf.Vec3f(0, 0, 0),
            offset_rotation=Gf.Quatf(1.0),
        )
        pass

    def add_differential_base(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "ROSBridgeCreateDifferentialBase",
            path="/ROS_DifferentialBase",
            parent=self._get_stage_and_path(),
            enabled=True,
            chassis_prim_rel=None,
            left_wheel_joint_name="",
            right_wheel_joint_name="",
            robot_front=Gf.Vec3f(1, 0, 0),
            wheel_radius=0.0,
            wheel_base=0.0,
            max_speed=Gf.Vec2f(1.5, 1.0),
            time_without_command=0.2,
            acceleration_smoothing=1.0,
        )
        pass

    def shutdown(self):
        remove_menu_items(self._menu_items, "Create")
        self._menus = None
