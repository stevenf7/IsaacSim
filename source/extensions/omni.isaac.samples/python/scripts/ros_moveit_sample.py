# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
import omni.kit.commands
import omni.ext
import omni.appwindow
import weakref
import omni.kit.settings
import gc
import asyncio
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

from pxr import Gf

from omni.isaac.utils.scripts.scene_utils import setup_physics, create_background
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server

MENU_NAME = "MoveIt"
FRANKA_STAGE_PATH = "/Franka"


class Extension(omni.ext.IExt):
    def on_startup(self):
        """Initialize extension and UI elements"""
        self._timeline = omni.timeline.get_timeline_interface()
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._window = None

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._nucleus_path = nucleus_server

        menu_items = [MenuItemDescription(name=MENU_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())]
        self._menu_items = [
            MenuItemDescription(name="Communicating", sub_menu=[MenuItemDescription(name="ROS", sub_menu=menu_items)])
        ]
        add_menu_items(self._menu_items, "Isaac Examples")

    def _menu_callback(self):
        self._on_environment_setup()

    def add_clock(self):
        omni.kit.commands.execute("ROSBridgeCreateClock", path="/ROS_Clock")
        pass

    def add_joint_state(self, stage_path):
        omni.kit.commands.execute(
            "ROSBridgeCreateJointState", path="/ROS_JointState", articulation_prim_rel=[stage_path]
        )
        pass

    def add_pose_tree(self, stage_path):
        omni.kit.commands.execute("ROSBridgeCreatePoseTree", path="/ROS_PoseTree", target_prims_rel=[stage_path])
        pass

    def create_franka(self, stage_path):
        usd_path = "/Isaac/Robots/Franka/franka_alt_fingers.usd"
        asset_path = self._nucleus_path + usd_path
        prim = self._stage.DefinePrim(stage_path, "Xform")
        prim.GetReferences().AddReference(asset_path)
        rot_mat = Gf.Matrix3d(Gf.Rotation((0, 0, 1), 90))
        omni.kit.commands.execute(
            "TransformPrimCommand",
            path=prim.GetPath(),
            old_transform_matrix=None,
            new_transform_matrix=Gf.Matrix4d().SetRotate(rot_mat).SetTranslateOnly(Gf.Vec3d(0, -64, 0)),
        )

        pass

    def create_environment(self, usd_path, background_path):

        create_background(
            self._stage, self._nucleus_path + usd_path, background_path=background_path, offset=Gf.Vec3d(0, 0, 0)
        )
        pass

    async def _create_moveit_sample(self):
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        self._viewport.set_camera_position("/OmniverseKit_Persp", 120, 120, 80, True)
        self._viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 50, True)
        self._stage = self._usd_context.get_stage()

        self.create_franka(FRANKA_STAGE_PATH)
        await omni.kit.app.get_app().next_update_async()
        self.create_environment("/Isaac/Environments/Simple_Room/simple_room.usd", "/background")
        await omni.kit.app.get_app().next_update_async()
        setup_physics(self._stage)
        await omni.kit.app.get_app().next_update_async()
        self.add_clock()
        self.add_joint_state(FRANKA_STAGE_PATH)
        self.add_pose_tree(FRANKA_STAGE_PATH)
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()

    def _on_environment_setup(self):
        asyncio.ensure_future(self._create_moveit_sample())

    def on_shutdown(self):
        """Cleanup objects on extension shutdown"""
        self._timeline.stop()
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None
        gc.collect()
