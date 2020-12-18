import os
from omni.isaac.synthetic_utils import OmniKitHelper

CONFIG = {
    "experience": f'{os.environ["EXP_PATH"]}/isaac-sim-python.json',
    "renderer": "RayTracedLighting",
    "headless": True,
}

if __name__ == "__main__":
    # Example usage, with step size test
    kit = OmniKitHelper(config=CONFIG)
    import omni.physx

    # Create callbacks to both editor and physics step callbacks
    def editor_update(dt):
        print("kit update step:", dt, "seconds")

    def physics_update(dt):
        print("physics update step:", dt, "seconds")

    # start simulation
    kit.play()

    # assign callbacks
    update_sub = kit.editor.subscribe_to_update_events(editor_update)
    physics_sub = omni.physx.acquire_physx_interface().subscribe_physics_step_events(physics_update)

    # perform step experiments
    print("Rendering and Physics with 1 second step size:")
    kit.update(1.0)
    print("Rendering and Physics with 1/60 seconds step:")
    kit.update(1.0 / 60.0)
    print("Rendering 1/30 seconds step size and Physics 1/120 seconds step size:")
    kit.update(1.0 / 30.0, 1.0 / 120.0, 4)

    # cleanup
    update_sub = None
    physics_sub = None
    kit.stop()
