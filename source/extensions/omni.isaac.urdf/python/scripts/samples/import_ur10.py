import carb
import omni
import asyncio
import math
import weakref
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription


from .common import set_drive_parameters
from pxr import UsdLux, Sdf, Gf, UsdPhysics

EXTENSION_NAME = "Import UR10"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._window = omni.ui.Window(
            EXTENSION_NAME, width=600, height=400, visible=False, dockPreference=ui.DockPreference.LEFT_BOTTOM
        )
        self._menu_items = [
            MenuItemDescription(
                name="Importing",
                sub_menu=[
                    MenuItemDescription(name="UR10 URDF", onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
                ],
            )
        ]
        add_menu_items(self._menu_items, "Isaac Examples")
        with self._window.frame:
            with ui.VStack(height=0):
                ui.Button("Load Robot", clicked_fn=self._on_load_robot)
                ui.Button("Configure Robot", clicked_fn=self._on_config_robot)

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._extension_path = ext_manager.get_extension_path(ext_id)

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
            status, import_config = omni.kit.commands.execute("CreateURDFImportConfigCommand")
            import_config.merge_fixed_joints = False
            import_config.fix_base = True
            omni.kit.commands.execute(
                "ParseAndImportURDFCommand",
                urdf_path=self._extension_path + "/data/urdf/robots/ur10/urdf/ur10_base.urdf",
                import_config=import_config,
            )

            viewport = omni.kit.viewport.get_default_viewport_window()
            viewport.set_camera_position("/OmniverseKit_Persp", 200, -200, 50, True)
            viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)

    def _on_config_robot(self):
        stage = omni.usd.get_context().get_stage()
        scene = UsdPhysics.Scene.Define(stage, Sdf.Path("/physicsScene"))
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(981.0)

        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)

        joint_1 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/base_link/shoulder_pan_joint"), "angular")
        joint_2 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/shoulder_link/shoulder_lift_joint"), "angular")
        joint_3 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/upper_arm_link/elbow_joint"), "angular")
        joint_4 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/forearm_link/wrist_1_joint"), "angular")
        joint_5 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/wrist_1_link/wrist_2_joint"), "angular")
        joint_6 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/ur10/wrist_2_link/wrist_3_joint"), "angular")

        # Set the drive mode, target, stiffness, damping and max force for each joint
        set_drive_parameters(joint_1, "position", 45, math.radians(20000), math.radians(2000))
        set_drive_parameters(joint_2, "position", 45, math.radians(20000), math.radians(2000))
        set_drive_parameters(joint_3, "position", 45, math.radians(20000), math.radians(2000))
        set_drive_parameters(joint_4, "position", 45, math.radians(20000), math.radians(2000))
        set_drive_parameters(joint_5, "position", 45, math.radians(20000), math.radians(2000))
        set_drive_parameters(joint_6, "position", 45, math.radians(20000), math.radians(2000))

        # PhysxSchema.PhysxJointAPI.Get(stage, "/ur10/base_link/shoulder_pan_joint").CreateMaxJointVelocityAttr(math.degrees(10.0))
        # PhysxSchema.PhysxJointAPI.Get(stage, "/ur10/shoulder_link/shoulder_lift_joint").CreateMaxJointVelocityAttr(math.degrees(10.0))
        # PhysxSchema.PhysxJointAPI.Get(stage, "/ur10/upper_arm_link/elbow_joint").CreateMaxJointVelocityAttr(math.degrees(10.0))
        # PhysxSchema.PhysxJointAPI.Get(stage, "/ur10/forearm_link/wrist_1_joint").CreateMaxJointVelocityAttr(math.degrees(10.0))
        # PhysxSchema.PhysxJointAPI.Get(stage, "/ur10/wrist_1_link/wrist_2_joint").CreateMaxJointVelocityAttr(math.degrees(10.0))
        # PhysxSchema.PhysxJointAPI.Get(stage, "/ur10/wrist_2_link/wrist_3_joint").CreateMaxJointVelocityAttr(math.degrees(10.0))
