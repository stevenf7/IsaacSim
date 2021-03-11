import os
import carb
from omni.isaac.synthetic_utils import OmniKitHelper
import random

CONFIG = {
    "experience": f'{os.environ["EXP_PATH"]}/isaac-sim.python.kit',
    "renderer": "RayTracedLighting",
    "headless": True,
}

if __name__ == "__main__":
    # Simple example showing how to start and stop the helper
    kit = OmniKitHelper(config=CONFIG)
    kit.update(1.0 / 60.0)
    kit.shutdown()
