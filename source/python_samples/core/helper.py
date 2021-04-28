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
    kit.update(1.0 / 60.0)
    kit.shutdown()
