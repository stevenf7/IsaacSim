import carb
import omni
from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.isaac.urdf import _urdf
import asyncio

# from omni.physx import _physx
from .common import import_robot, set_drive_parameters, remove_all_schema_multiple_attributes
from pxr import Usd, UsdGeom, UsdLux, Sdf, Gf, PhysicsSchema, PhysxSchema


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._urdf_interface = _urdf.acquire_urdf_interface()
        self._window = omni.kit.ui.Window(
            "Import Kaya",
            300,
            200,
            menu_path="Isaac Robotics/URDF/Kaya",
            open=False,
            dock=omni.kit.ui.DockPreference.LEFT_BOTTOM,
        )
        load_robot_btn = self._window.layout.add_child(omni.kit.ui.Button("Load Robot"))
        load_robot_btn.set_clicked_fn(self._on_load_robot)

        config_robot_btn = self._window.layout.add_child(omni.kit.ui.Button("Configure Robot"))
        config_robot_btn.set_clicked_fn(self._on_config_robot)

    def on_shutdown(self):
        _urdf.release_urdf_interface(self._urdf_interface)
        self._window = None

    def _on_load_robot(self, widget):
        load_stage = asyncio.ensure_future(omni.kit.asyncapi.new_stage())
        asyncio.ensure_future(self._load_kaya(load_stage))

    async def _load_kaya(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            stage = omni.usd.get_context().get_stage()
            prim = stage.GetDefaultPrim()
            prim.SetActive(False)

            import_config = _urdf.ImportConfig()
            import_config.merge_fixed_joints = True
            import_config.import_inertia_tensor = True
            import_config.distance_scale = 10
            import_robot(self._urdf_interface, "data/urdf/robots/kaya/urdf/kaya.urdf", import_config)

            editor = omni.kit.editor.get_editor_interface()
            editor.set_camera_position("/OmniverseKit_Persp", -51, 63, 25, True)
            editor.set_camera_target("/OmniverseKit_Persp", 220, -218, -160, True)

    def _on_config_robot(self, widget):
        stage = omni.usd.get_context().get_stage()
        scene = PhysicsSchema.PhysicsScene.Define(stage, Sdf.Path("/physicsScene"))
        scene.CreateGravityAttr().Set(Gf.Vec3f(0.0, 0.0, -981.0))

        omni.kit.commands.execute(
            "AddGroundPlaneCommand",
            stage=stage,
            planePath="/groundPlane",
            axis="Z",
            size=1500.0,
            position=Gf.Vec3f(-25),
            color=Gf.Vec3f(0.5),
        )

        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)

        kaya_prim = stage.GetPrimAtPath("/kaya")
        physicsArticulationAPI = PhysicsSchema.ArticulationAPI.Get(stage, kaya_prim.GetPath())
        physicsArticulationAPI.GetFixBaseAttr().Set(False)
        # Make all rollers spin freely by removing extra drive API
        for axle in range(0, 2 + 1):
            for ring in range(0, 1 + 1):
                for roller in range(0, 4 + 1):
                    prim_path = (
                        "/kaya/axle_"
                        + str(axle)
                        + "/roller_"
                        + str(axle)
                        + "_"
                        + str(ring)
                        + "_"
                        + str(roller)
                        + "_joint"
                    )
                    prim = stage.GetPrimAtPath(prim_path)
                    remove_all_schema_multiple_attributes(PhysicsSchema.DriveAPI, prim, "drive", "angular")
                    PhysicsSchema.PhysicsSchemaMultipleAPI.UnapplyAPISchema(prim, "DriveAPI:angular")

        # set each axis to spin at a rate of 1 rad/s
        axle_0 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/kaya/base_link/axle_0_joint"), "angular")
        axle_1 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/kaya/base_link/axle_1_joint"), "angular")
        axle_2 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/kaya/base_link/axle_2_joint"), "angular")

        set_drive_parameters(axle_0, "velocity", 2, 0, 1e8, 1e10)
        set_drive_parameters(axle_1, "velocity", 2, 0, 1e8, 1e10)
        set_drive_parameters(axle_2, "velocity", 2, 0, 1e8, 1e10)

        usd_context = omni.usd.get_context()
        selection = usd_context.get_selection()
        selection.set_selected_prim_paths(["/kaya"], True)
