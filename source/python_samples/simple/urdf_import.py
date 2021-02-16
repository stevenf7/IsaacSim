import os
import carb
from omni.isaac.synthetic_utils import OmniKitHelper

CONFIG = {
    "experience": f'{os.environ["EXP_PATH"]}/isaac-sim.python.kit',
    "renderer": "RayTracedLighting",
    "headless": True,
}

if __name__ == "__main__":
    # Example usage, with step size test
    kit = OmniKitHelper(config=CONFIG)
    import omni.kit.commands
    from pxr import Sdf, Gf, UsdPhysics, UsdLux

    # setting up import configuration:
    status, import_config = omni.kit.commands.execute("CreateURDFImportConfigCommand")
    import_config.merge_fixed_joints = False
    import_config.convex_decomp = False
    import_config.import_inertia_tensor = True
    import_config.fix_base = False

    # Get path to extension data:
    ext_manager = omni.kit.app.get_app().get_extension_manager()
    ext_id = ext_manager.get_enabled_extension_id("omni.isaac.urdf")
    extension_path = ext_manager.get_extension_path(ext_id)
    # import URDF
    omni.kit.commands.execute(
        "ParseAndImportURDFCommand",
        urdf_path=extension_path + "/data/urdf/robots/carter/urdf/carter.urdf",
        import_config=import_config,
    )
    # get stage handle
    stage = omni.usd.get_context().get_stage()

    # enable physics
    scene = UsdPhysics.Scene.Define(stage, Sdf.Path("/physicsScene"))
    # set gravity
    scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
    scene.CreateGravityMagnitudeAttr().Set(981.0)

    # add ground plane
    omni.kit.commands.execute(
        "AddGroundPlaneCommand",
        stage=stage,
        planePath="/groundPlane",
        axis="Z",
        size=1500.0,
        position=Gf.Vec3f(0, 0, -50),
        color=Gf.Vec3f(0.5),
    )

    # add lighting
    distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
    distantLight.CreateIntensityAttr(500)

    # get handle to the Drive API for both wheels
    left_wheel_drive = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/carter/chassis_link/left_wheel"), "angular")
    right_wheel_drive = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/carter/chassis_link/right_wheel"), "angular")

    # Set the velocity drive target in degrees/second
    left_wheel_drive.GetTargetVelocityAttr().Set(150)
    right_wheel_drive.GetTargetVelocityAttr().Set(150)

    # Set the drive damping, which controls the strength of the velocity drive
    left_wheel_drive.GetDampingAttr().Set(15000)
    right_wheel_drive.GetDampingAttr().Set(15000)

    # Set the drive stiffness, which controls the strength of the position drive
    # In this case because we want to do velocity control this should be set to zero
    left_wheel_drive.GetStiffnessAttr().Set(0)
    right_wheel_drive.GetStiffnessAttr().Set(0)

    # start simulation
    kit.play()

    # perform step experiments
    for frame in range(100):
        kit.update(1.0 / 60.0)

    kit.stop()
    kit.shutdown()
