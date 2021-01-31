import carb
import omni
import asyncio
import math
import weakref
import omni.ui as ui

# import omni.physx as _physx
from .common import set_drive_parameters
from pxr import UsdLux, Sdf, Gf, UsdPhysics, PhysxSchema

EXTENSION_NAME = "Import Franka"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._window = omni.ui.Window(
            EXTENSION_NAME, width=600, height=400, visible=False, dockPreference=ui.DockPreference.LEFT_BOTTOM
        )
        omni.kit.menu.utils.add_menu_items(
            [
                omni.kit.menu.utils.MenuItemDescription(
                    name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback()
                )
            ],
            "Isaac/URDF",
        )
        with self._window.frame:
            with ui.VStack(height=0):
                ui.Button("Load Robot", clicked_fn=self._on_load_robot)
                ui.Button("Configure Robot", clicked_fn=self._on_config_robot)

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._extension_path = ext_manager.get_extension_path(ext_id)

    def on_shutdown(self):
        self._window = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def _on_load_robot(self):
        load_stage = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._load_franka(load_stage))

    async def _load_franka(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            status, import_config = omni.kit.commands.execute("CreateURDFImportConfigCommand")
            import_config.merge_fixed_joints = False
            import_config.fix_base = True
            omni.kit.commands.execute(
                "ParseAndImportURDFCommand",
                urdf_path=self._extension_path + "/data/urdf/robots/franka_description/robots/panda_arm_hand.urdf",
                import_config=import_config,
            )

            viewport = omni.kit.viewport.get_default_viewport_window()
            viewport.set_camera_position("/OmniverseKit_Persp", 122, -124, 113, True)
            viewport.set_camera_target("/OmniverseKit_Persp", -96, 108, 0, True)

    def _on_config_robot(self):
        stage = omni.usd.get_context().get_stage()
        scene = UsdPhysics.Scene.Define(stage, Sdf.Path("/physicsScene"))
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(981.0)
        omni.kit.commands.execute(
            "AddGroundPlaneCommand",
            stage=stage,
            planePath="/groundPlane",
            axis="Z",
            size=1500.0,
            position=Gf.Vec3f(0),
            color=Gf.Vec3f(0.5),
        )
        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)

        PhysxSchema.PhysxArticulationAPI.Get(stage, "/panda").CreateSolverPositionIterationCountAttr(32)
        PhysxSchema.PhysxArticulationAPI.Get(stage, "/panda").CreateSolverVelocityIterationCountAttr(8)

        joint_1 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link0/panda_joint1"), "angular")
        joint_2 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link1/panda_joint2"), "angular")
        joint_3 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link2/panda_joint3"), "angular")
        joint_4 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link3/panda_joint4"), "angular")
        joint_5 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link4/panda_joint5"), "angular")
        joint_6 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link5/panda_joint6"), "angular")
        joint_7 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link6/panda_joint7"), "angular")
        finger_1 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_hand/panda_finger_joint1"), "linear")
        finger_2 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_hand/panda_finger_joint2"), "linear")

        # Set the drive mode, target, stiffness, damping and max force for each joint
        set_drive_parameters(joint_1, "position", math.degrees(0.012), math.radians(60000), math.radians(3000))
        set_drive_parameters(joint_2, "position", math.degrees(-0.57), math.radians(60000), math.radians(3000))
        set_drive_parameters(joint_3, "position", math.degrees(0), math.radians(60000), math.radians(3000))
        set_drive_parameters(joint_4, "position", math.degrees(-2.81), math.radians(60000), math.radians(3000))
        set_drive_parameters(joint_5, "position", math.degrees(0), math.radians(25000), math.radians(3000))
        set_drive_parameters(joint_6, "position", math.degrees(3.037), math.radians(15000), math.radians(3000))
        set_drive_parameters(joint_7, "position", math.degrees(0.741), math.radians(5000), math.radians(3000))
        set_drive_parameters(finger_1, "position", 4, 6000, 1000)
        set_drive_parameters(finger_2, "position", 4, 6000, 1000)

        # Set Max Joint velocity on all joints

        PhysxSchema.PhysxJointAPI.Get(stage, joint_1.GetPath()).CreateMaxJointVelocityAttr(math.degrees(10.0))
        PhysxSchema.PhysxJointAPI.Get(stage, joint_2.GetPath()).CreateMaxJointVelocityAttr(math.degrees(10.0))
        PhysxSchema.PhysxJointAPI.Get(stage, joint_3.GetPath()).CreateMaxJointVelocityAttr(math.degrees(10.0))
        PhysxSchema.PhysxJointAPI.Get(stage, joint_4.GetPath()).CreateMaxJointVelocityAttr(math.degrees(10.0))
        PhysxSchema.PhysxJointAPI.Get(stage, joint_5.GetPath()).CreateMaxJointVelocityAttr(math.degrees(10.0))
        PhysxSchema.PhysxJointAPI.Get(stage, joint_6.GetPath()).CreateMaxJointVelocityAttr(math.degrees(10.0))
        PhysxSchema.PhysxJointAPI.Get(stage, joint_7.GetPath()).CreateMaxJointVelocityAttr(math.degrees(10.0))
        PhysxSchema.PhysxJointAPI.Get(stage, finger_1.GetPath()).CreateMaxJointVelocityAttr(math.degrees(10.0))
        PhysxSchema.PhysxJointAPI.Get(stage, finger_2.GetPath()).CreateMaxJointVelocityAttr(math.degrees(10.0))
