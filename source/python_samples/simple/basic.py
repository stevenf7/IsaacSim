import os
from pxr import UsdGeom
from omni.isaac.synthetic_utils import OmniKitHelper
import omni.physx

CONFIG = {"experience": f'{os.environ["EXP_PATH"]}/isaac-sim-python.json'}


if __name__ == "__main__":
    # Example usage, with step size test
    kit = OmniKitHelper(config=CONFIG)

    stage = kit.get_stage()
    cube = UsdGeom.Cube.Define(stage, "/World/cube")
    UsdGeom.XformCommonAPI(cube).SetScale([100, 100, 100])
    # Create callbacks to print both editor and physics

    def editor_update(dt):
        print("kit update step:", dt, "seconds")

    def physics_update(dt):
        print("physics update step:", dt, "seconds")

    kit.play()
    update_sub = kit.editor.subscribe_to_update_events(editor_update)
    physics_sub = omni.physx._physx.acquire_physx_interface().subscribe_physics_step_events(physics_update)
    kit.update(1.0)
    kit.update(2.0)
    kit.update(1.0 / 60.0)
    kit.update(1.0)
    update_sub = None
    physics_sub = None
    kit.stop()
