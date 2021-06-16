import os
from omni.isaac.python_app import OmniKitHelper

CONFIG = {
    "experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit',
    "renderer": "RayTracedLighting",
    "headless": True,
}

if __name__ == "__main__":
    # Simple example showing how to start and stop the helper
    kit = OmniKitHelper(config=CONFIG)

    ### Perform any omniverse imports here after the helper loads ###

    kit.play()  # Start simulation
    kit.update(1.0 / 60.0)  # Render a single frame
    kit.stop()  # Stop Simulation
    kit.shutdown()  # Cleanup application
