import carb
import omni
from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.isaac.urdf import _urdf

# from omni.physx import _physx
from .common import import_robot, set_drive_parameters, remove_all_schema_multiple_attributes
from pxr import Usd, UsdGeom, UsdLux, Sdf, Gf, PhysicsSchema, PhysicsSchemaTools, PhysxSchema


class import_kaya:
    def __init__(self, urdf_interface):
        self._urdf_interface = urdf_interface
        self._window = omni.kit.ui.Window(
            "Import Kaya",
            300,
            200,
            menu_path="Isaac Robotics/URDF/Kaya",
            open=False,
            dock=omni.kit.ui.DockPreference.DISABLED,
        )
        load_robot_btn = self._window.layout.add_child(omni.kit.ui.Button("Load Robot"))
        load_robot_btn.set_clicked_fn(self._on_load_robot)

        config_robot_btn = self._window.layout.add_child(omni.kit.ui.Button("Configure Robot"))
        config_robot_btn.set_clicked_fn(self._on_config_robot)
        # self._physxIFace = _physx.acquire_physx_interface()

    def _on_load_robot(self, widget):
        # TODO: fix this workaround to clear stage
        stage = omni.usd.get_context().get_stage()
        prim = stage.GetDefaultPrim()
        prim.SetActive(False)

        import_config = _urdf.ImportConfig()
        import_config.merge_fixed_joints = True
        import_config.distance_scale = 10
        import_robot(self._urdf_interface, "data/urdf/robots/kaya/urdf/kaya.urdf", import_config)

    def _on_config_robot(self, widget):
        stage = omni.usd.get_context().get_stage()
        scene = PhysicsSchema.PhysicsScene.Define(stage, Sdf.Path("/physicsScene"))
        # scene.CreateGravityAttr().Set(Gf.Vec3f(0.0, 0.0, -981.0))
        PhysicsSchemaTools.addGroundPlane(stage, "/groundPlane", "Z", 1500.0, Gf.Vec3f(-50), Gf.Vec3f(0.5))
        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)

        carter_prim = stage.GetPrimAtPath("/kaya")
        physicsArticulationAPI = PhysicsSchema.ArticulationAPI.Get(stage, carter_prim.GetPath())
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

        set_drive_parameters(axle_0, "velocity", 1, 0, 1000000, 1e8)
        set_drive_parameters(axle_1, "velocity", 1, 0, 1000000, 1e8)
        set_drive_parameters(axle_2, "velocity", 1, 0, 1000000, 1e8)
