# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os
import carb
import omni
import asyncio
import math
import weakref
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

from omni.isaac.ui.ui_utils import setup_ui_headers, get_style, btn_builder

from .common import set_drive_parameters
from pxr import UsdLux, Sdf, Gf, UsdPhysics

EXTENSION_NAME = "Import UR10"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        """Initialize extension and UI elements"""
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._extension_path = ext_manager.get_extension_path(ext_id)

        self._menu_items = [
            MenuItemDescription(
                name="Importing",
                sub_menu=[
                    MenuItemDescription(name="UR10 URDF", onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
                ],
            )
        ]
        add_menu_items(self._menu_items, "Isaac Examples")

        self._build_ui()

    def _build_ui(self):
        self._window = omni.ui.Window(
            EXTENSION_NAME, width=0, height=0, visible=False, dockPreference=ui.DockPreference.LEFT_BOTTOM
        )
        with self._window.frame:
            with ui.VStack(spacing=5, height=0):

                title = "Import a UR10 via URDF"
                doc_link = "https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/sample_urdf_import.html"
                ext_path = (
                    os.path.dirname(self._extension_path)
                    if os.path.isfile(self._extension_path)
                    else self._extension_path
                )

                overview = "This Example shows you import a UR10 robot arm via URDF.\n\nPress the 'Open in IDE' button to view the source code."
                author = "Isaac Sim Team"
                date = "07/01/2021"

                log_filename = EXTENSION_NAME.lower()
                log_filename = log_filename.replace(" ", "_") + ".log"

                setup_ui_headers(ext_path, __file__, title, doc_link, overview, author, date, log_filename)

                frame = ui.CollapsableFrame(
                    title="Command Panel",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )
                with frame:
                    with ui.VStack(style=get_style(), spacing=5):
                        dict = {
                            "label": "Load Robot",
                            "type": "button",
                            "text": "Load",
                            "tooltip": "Load a UR10 Robot into the Scene",
                            "on_clicked_fn": self._on_load_robot,
                        }
                        btn_builder(**dict)

                        dict = {
                            "label": "Configure Drives",
                            "type": "button",
                            "text": "Configure",
                            "tooltip": "Configure Joint Drives",
                            "on_clicked_fn": self._on_config_robot,
                        }
                        btn_builder(**dict)

                        dict = {
                            "label": "Move to Pose",
                            "type": "button",
                            "text": "move",
                            "tooltip": "Drive the Robot to a specific pose",
                            "on_clicked_fn": self._on_config_drives,
                        }
                        btn_builder(**dict)

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def _on_load_robot(self):
        load_stage = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._load_robot(load_stage))

    async def _load_robot(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            status, import_config = omni.kit.commands.execute("URDFCreateImportConfig")
            import_config.merge_fixed_joints = False
            import_config.fix_base = True
            omni.kit.commands.execute(
                "URDFParseAndImportFile",
                urdf_path=self._extension_path + "/data/urdf/robots/ur10/urdf/ur10_base.urdf",
                import_config=import_config,
            )

            viewport = omni.kit.viewport.get_default_viewport_window()
            viewport.set_camera_position("/OmniverseKit_Persp", 200, -200, 50, True)
            viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)

            stage = omni.usd.get_context().get_stage()
            scene = UsdPhysics.Scene.Define(stage, Sdf.Path("/physicsScene"))
            scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
            scene.CreateGravityMagnitudeAttr().Set(981.0)

            distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
            distantLight.CreateIntensityAttr(500)

    def _on_config_robot(self):
        stage = omni.usd.get_context().get_stage()

        joint_1 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/base_link/shoulder_pan_joint"), "angular")
        joint_2 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/shoulder_link/shoulder_lift_joint"), "angular")
        joint_3 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/upper_arm_link/elbow_joint"), "angular")
        joint_4 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/forearm_link/wrist_1_joint"), "angular")
        joint_5 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/wrist_1_link/wrist_2_joint"), "angular")
        joint_6 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/wrist_2_link/wrist_3_joint"), "angular")

        # Set the drive mode, target, stiffness, damping and max force for each joint
        set_drive_parameters(joint_1, "position", 0, math.radians(200000), math.radians(20000), 3300000.0 * 60)
        set_drive_parameters(joint_2, "position", 0, math.radians(200000), math.radians(20000), 3300000.0 * 60)
        set_drive_parameters(joint_3, "position", 0, math.radians(200000), math.radians(20000), 1500000.0 * 60)
        set_drive_parameters(joint_4, "position", 0, math.radians(200000), math.radians(20000), 560000.0 * 60)
        set_drive_parameters(joint_5, "position", 0, math.radians(200000), math.radians(20000), 560000.0 * 60)
        set_drive_parameters(joint_6, "position", 0, math.radians(200000), math.radians(20000), 560000.0 * 60)

        # PhysxSchema.PhysxJointAPI.Get(stage, "/ur10/base_link/shoulder_pan_joint").CreateMaxJointVelocityAttr(math.degrees(10.0))
        # PhysxSchema.PhysxJointAPI.Get(stage, "/ur10/shoulder_link/shoulder_lift_joint").CreateMaxJointVelocityAttr(math.degrees(10.0))
        # PhysxSchema.PhysxJointAPI.Get(stage, "/ur10/upper_arm_link/elbow_joint").CreateMaxJointVelocityAttr(math.degrees(10.0))
        # PhysxSchema.PhysxJointAPI.Get(stage, "/ur10/forearm_link/wrist_1_joint").CreateMaxJointVelocityAttr(math.degrees(10.0))
        # PhysxSchema.PhysxJointAPI.Get(stage, "/ur10/wrist_1_link/wrist_2_joint").CreateMaxJointVelocityAttr(math.degrees(10.0))
        # PhysxSchema.PhysxJointAPI.Get(stage, "/ur10/wrist_2_link/wrist_3_joint").CreateMaxJointVelocityAttr(math.degrees(10.0))

    def _on_config_drives(self):
        self._on_config_robot()  # make sure drives are configured first
        stage = omni.usd.get_context().get_stage()
        joint_1 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/base_link/shoulder_pan_joint"), "angular")
        joint_2 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/shoulder_link/shoulder_lift_joint"), "angular")
        joint_3 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/upper_arm_link/elbow_joint"), "angular")
        joint_4 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/forearm_link/wrist_1_joint"), "angular")
        joint_5 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/wrist_1_link/wrist_2_joint"), "angular")
        joint_6 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/wrist_2_link/wrist_3_joint"), "angular")
        set_drive_parameters(joint_1, "position", 45)
        set_drive_parameters(joint_2, "position", 45)
        set_drive_parameters(joint_3, "position", 45)
        set_drive_parameters(joint_4, "position", 45)
        set_drive_parameters(joint_5, "position", 45)
        set_drive_parameters(joint_6, "position", 45)
