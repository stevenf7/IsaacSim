# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
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
import asyncio
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
import weakref
import math

EXTENSION_NAME = "ROS Topics"


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
        self._window = omni.ui.Window(EXTENSION_NAME, width=400, height=200, visible=False)
        menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        self._menu_items = [
            MenuItemDescription(name="Communicating", sub_menu=[MenuItemDescription(name="ROS", sub_menu=menu_items)])
        ]
        add_menu_items(self._menu_items, "Isaac Examples")
        with self._window.frame:
            with ui.VStack(spacing=5):
                ui.Button("Load Robot", tooltip="Loads robot into stage", clicked_fn=self._on_load_robot)
                ui.Label("Robot must be reloaded if changing control mode", height=0)
                with ui.HStack(height=0, spacing=5):
                    ui.Label("Control Mode", width=0)
                    self._velocity_combo = ui.ComboBox(0, "Position", "Velocity").model
                ui.Button(
                    "Connect Joint State Topics",
                    tooltip="start a joint_state and joint_command topic to publish and receive joint states",
                    clicked_fn=self._on_connect_js,
                )
                ui.Button(
                    "Add Cube And Publish TF",
                    tooltip="Add a Cube to the scene and publish TF tree",
                    clicked_fn=self._on_add_cube,
                )

        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._timeline = omni.timeline.get_timeline_interface()

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    # Fix camera location and angle
    async def _setup_stage(self):
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        self._stage = omni.usd.get_context().get_stage()

        # Add physics scene
        scene = UsdPhysics.Scene.Define(self._stage, Sdf.Path("/PhysicsScene"))
        # Set gravity vector
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(981.0)
        # Set physics scene to use cpu physics
        PhysxSchema.PhysxSceneAPI.Apply(self._stage.GetPrimAtPath("/PhysicsScene"))
        physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(self._stage, "/PhysicsScene")
        physxSceneAPI.CreateEnableCCDAttr(True)
        physxSceneAPI.CreateEnableStabilizationAttr(True)
        physxSceneAPI.CreateEnableGPUDynamicsAttr(False)
        physxSceneAPI.CreateBroadphaseTypeAttr("MBP")
        physxSceneAPI.CreateSolverTypeAttr("TGS")

        await omni.kit.app.get_app().next_update_async()

        omni.kit.commands.execute(
            "CreateReferenceCommand",
            usd_context=omni.usd.get_context(),
            path_to="/panda",
            asset_path=self._dc_extension_path + "/data/usd/robots/franka/franka.usd",
            instanceable=False,
        )
        await omni.kit.app.get_app().next_update_async()

        # Create a camera
        omni.kit.commands.execute(
            "CreatePrimWithDefaultXform",
            prim_type="Camera",
            prim_path="/sim_camera",
            attributes={"focusDistance": 400, "focalLength": 24},
        )

        # Set Camera Pose
        self._viewport.set_active_camera("/sim_camera")
        await omni.kit.app.get_app().next_update_async()

        omni.kit.commands.execute(
            "TransformPrimCommand",
            path="/sim_camera",
            old_transform_matrix=Gf.Matrix4d(
                0.0, 1.0, -0.0, 0.0, -0.0, 0.0, 1.0, 0.0, 1.0, -0.0, 0.0, 0.0, 0.0, 0.0, -0.0, 1.0
            ),
            new_transform_matrix=Gf.Matrix4d(
                -0.642788,
                0.766045,
                0.0,
                0.0,
                -0.133022,
                -0.111619,
                0.984807,
                0.0,
                0.754407,
                0.633022,
                0.173648,
                0.0,
                175.0,
                150.0,
                70.0,
                1.0,
            ),
        )

        # adding camera topic
        omni.kit.commands.execute(
            "ROSBridgeCreateCamera",
            path="/ROS_Camera",
            enabled=True,
            resolution=Gf.Vec2i(1280, 720),
            frame_id="sim_camera",
            camera_info_topic="/camera_info",
            rgb_enabled=True,
            rgb_topic="/rgb",
            depth_enabled=True,
            depth_topic="/depth",
            segmentation_enabled=False,
            semantic_topic="/semantic",
            instance_topic="/instance",
            label_topic="/label",
            bbox2d_enabled=False,
            bbox2d_topic="/bbox_2d",
            bbox3d_enabled=False,
            bbox3d_topic="/bbox_3d",
            queue_size=10,
            camera_prim_rel=["/sim_camera"],
        )
        # timeline must be playing for articulation to work, so start it now
        if not self._timeline.is_playing():
            self._timeline.play()

    # load robot
    def _on_load_robot(self):
        asyncio.ensure_future(self._setup_stage())

    def _on_connect_js(self):
        # check robot is loaded and articulation exist
        self._stage = omni.usd.get_context().get_stage()
        robot_prim = self._stage.GetPrimAtPath("/panda")
        if not robot_prim:
            carb.log_error("Robot not found, please load robot before clicking this button")
            return
        ROS_prim = self._stage.GetPrimAtPath("/ROS_JointState")
        if not ROS_prim:
            omni.kit.commands.execute(
                "ROSBridgeCreateJointState",
                path="/ROS_JointState",
                enabled=True,
                state_topic="/joint_states",
                command_topic="/joint_command",
                articulation_prim_rel=["/panda"],
            )

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
            set_drive_parameters(panda_joint1_drive, "velocity", 0.0, 0, math.radians(1e7), 87000)
            set_drive_parameters(panda_joint2_drive, "velocity", 0.0, 0, math.radians(1e7), 87000)
            set_drive_parameters(panda_joint3_drive, "velocity", 0.0, 0, math.radians(1e7), 87000)
            set_drive_parameters(panda_joint4_drive, "velocity", 0.0, 0, math.radians(1e7), 87000)
            set_drive_parameters(panda_joint5_drive, "velocity", 0.0, 0, math.radians(1e7), 12000)
            set_drive_parameters(panda_joint6_drive, "velocity", 0.0, 0, math.radians(1e7), 12000)
            set_drive_parameters(panda_joint7_drive, "velocity", 0.0, 0, math.radians(1e7), 12000)

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

    def _on_add_cube(self):
        # first create a cube
        self._stage = omni.usd.get_context().get_stage()

        robot_prim = self._stage.GetPrimAtPath("/panda")
        if not robot_prim:
            carb.log_error("Robot not found, please load robot before clicking this button")
            return
        cube_path = "/cube"
        # offset to some position in space
        offset = Gf.Vec3f(50.0, 0.0, 50.0)
        size = 10  # cm
        cube_geom = self._stage.GetPrimAtPath(cube_path)
        if not cube_geom:
            cube_geom = UsdGeom.Cube.Define(self._stage, cube_path)
            cube_geom.CreateSizeAttr(size)
            cube_geom.AddTranslateOp().Set(offset)

        # adding tf topic and cube to the tf tree
        ROS_prim = self._stage.GetPrimAtPath("/ROS_PoseTree")
        if not ROS_prim:
            omni.kit.commands.execute(
                "ROSBridgeCreatePoseTree",
                path="/ROS_PoseTree",
                enabled=True,
                topic="/tf",
                queue_size=0,
                target_prims_rel=["/panda", "/sim_camera", cube_path],
            )
