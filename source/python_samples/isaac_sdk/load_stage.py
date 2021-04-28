import os
from pxr import UsdGeom, Usd, Gf
from omni.isaac.python_app import OmniKitHelper
import carb
import omni

# This sample loads a usd stage and creates a robot engine bridge application and starts simulation
# Useful for testing an Isaac SDK sample scene using python
CONFIG = {
    "experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit',
    "width": 1280,
    "height": 720,
    "sync_loads": True,
    "headless": False,
    "renderer": "RayTracedLighting",
}


class UsdLoadSample:
    def __init__(self):
        self.kit = OmniKitHelper(config=CONFIG)
        self.usd_path = ""

    def start(self):
        self.kit.play()

    def stop(self):
        self.kit.stop()
        omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")

    def load_stage(self, args):
        from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return False
        self._asset_path = nucleus_server + "/Isaac"
        self.usd_path = self._asset_path + args.usd_path
        omni.usd.get_context().open_stage(self.usd_path, None)
        return True

    def configure_bridge(self, json_file: str = "isaacsim.app.json"):
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
        reb_extension_path = ext_manager.get_extension_path(ext_id)
        app_file = f"{reb_extension_path}/resources/isaac_engine/json/{json_file}"
        carb.log_info(f"create application with: {reb_extension_path} {app_file}")
        return omni.kit.commands.execute(
            "RobotEngineBridgeCreateApplication", asset_path=reb_extension_path, app_file=app_file
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser("Usd Load sample")
    parser.add_argument("--usd_path", type=str, help="path to usd file")
    args, unknown = parser.parse_known_args()
    sample = UsdLoadSample()
    if sample.load_stage(args):
        while sample.kit.is_loading():
            sample.kit.update(1.0 / 60.0)
        sample.configure_bridge()
        sample.start()
        while sample.kit.app.is_running():
            sample.kit.update(1.0 / 60.0)
        sample.stop()
