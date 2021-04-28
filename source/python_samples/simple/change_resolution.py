import os
import carb
from omni.isaac.python_app import OmniKitHelper
import random

CONFIG = {
    "experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit',
    "renderer": "RayTracedLighting",
    "headless": True,
}

if __name__ == "__main__":
    # Simple example showing how to change resolution
    kit = OmniKitHelper(config=CONFIG)
    kit.update(1.0 / 60.0)
    for i in range(100):
        width = random.randint(128, 1980)
        height = random.randint(128, 1980)
        kit.set_setting("/app/renderer/resolution/width", width)
        kit.set_setting("/app/renderer/resolution/height", height)
        kit.update(1.0 / 60.0)
        print(f"resolution set to: {width}, {height}")

    # cleanup
    kit.shutdown()
