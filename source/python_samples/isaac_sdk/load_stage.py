import os
from omni.isaac.python_app import OmniKitHelper
import carb
import omni

# This sample loads a usd stage and creates a robot engine bridge application and starts simulation
# Disposes average fps of the simulation for given time
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
    def __init__(self, args):
        CONFIG["headless"] = args.headless
        self.kit = OmniKitHelper(config=CONFIG)
        self.usd_path = ""
        from pxr import Gf
        self.Gf = Gf
        self._viewport = omni.kit.viewport.get_viewport_interface()

    def start(self):
        self.kit.play()

    def stop(self):
        self.kit.stop()
        omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")
        self.kit.shutdown()

    def load_stage(self, args):
        from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return False
        self._asset_path = nucleus_server + "/Isaac"
        self.usd_path = self._asset_path + args.usd_path
        omni.usd.get_context().open_stage(self.usd_path, None)
        # Wait two frames so that stage starts loading
        self.kit.app.update()
        self.kit.app.update()
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

    def create_reb_camera(self, cameraIndex, name, width, height):
        result, self.occluded_provider = omni.kit.commands.execute(
            "RobotEngineBridgeCreateCamera",
            path="/World/REB_Provider",
            parent=None,
            rgb_output_component="output",
            rgb_output_channel="encoder_color_{}".format(cameraIndex),
            depth_output_component="output",
            depth_output_channel="encoder_depth_{}".format(cameraIndex),
            segmentation_output_component="output",
            segmentation_output_channel="encoder_segmentation_{}".format(cameraIndex),
            bbox2d_output_component="output",
            bbox2d_output_channel="encoder_bbox_{}".format(cameraIndex),
            bbox2d_class_list="",
            bbox3d_output_component="output",
            bbox3d_output_channel="encoder_bbox3d_{}".format(cameraIndex),
            bbox3d_class_list="",
            rgb_enabled=True,
            depth_enabled=False,
            segmentaion_enabled=True,
            bbox2d_enabled=False,
            bbox3d_enabled=False,
            camera_prim_rel=["{}".format(name)],
            resolution=self.Gf.Vec2i(int(width), int(height)),
        )
        self.occluded_provider.GetEnabledAttr().Set(True)

    def create_viewport(self, name, pose_x, pose_y, resolution = (1280, 720), size = (350, 350)):
        viewport_handle_1 = self._viewport.create_instance()
        viewport_window_1 = self._viewport.get_viewport_window(viewport_handle_1)
        viewport_window_1.set_active_camera("{}".format(name))
        viewport_window_1.set_texture_resolution(resolution)
        viewport_window_1.set_window_pos(pose_x, pose_y)
        viewport_window_1.set_window_size(size)

    def create_multi_viewport(self,args):
        # Need to set this before setting viewport window size
        carb.settings.acquire_settings_interface().set_int("/app/renderer/resolution/width",-1)
        carb.settings.acquire_settings_interface().set_int("/app/renderer/resolution/height",-1)

if __name__ == "__main__":
    import argparse
    import time

    parser = argparse.ArgumentParser("Usd Load sample")
    parser.add_argument("--usd_path", type=str, help="Path to usd file", required=True)
    parser.add_argument("--headless", default=False, action="store_true", help="Run stage headless")
    parser.add_argument("--test", default=False, action="store_true", help="Run in test mode")
    parser.add_argument("--perf_timeout", type=int, default=60, help="Total perf time")
    parser.add_argument("--add_rebcamera", nargs="*", type=str, default=[],
                         help="Total number of REBCamera to add")
    parser.add_argument("--add_viewport", dest='add_viewport', action='store_true',
                         help="Whether to show viewport for all Camera")

    args, unknown = parser.parse_known_args()
    sample = UsdLoadSample(args)
    if sample.load_stage(args):
        print("Loading stage...")
        while sample.kit.is_loading():
            sample.kit.update(1.0 / 60.0)
        print("Loading Complete")
        # Add parameterized rebcamera along with viewport
        if args.add_rebcamera is not None:
            reb_count=0
            if(args.add_viewport):
               # viewport settings
               sample.create_multi_viewport(args)
            pose_x = 720
            pose_y = 0
            for name in args.add_rebcamera:
                info = name.split(',')
                sample.create_reb_camera(reb_count, info[0], info[1], info[2])
                if(args.add_viewport):
                  sample.create_viewport(info[0], pose_x, pose_y)
                  pose_x = pose_x-20
                  pose_y = pose_y+50
                reb_count = reb_count+1
        sample.configure_bridge()
        sample.start()
        if args.test is True:
            for i in range(10):
                sample.kit.update()
        else:
            # Calculate average fps
            while sample._viewport.get_viewport_window().get_fps() < 1 :
                sample.kit.update(1.0 / 60.0)

            fps_count = 0
            start_time = time.perf_counter()
            end_time = start_time + args.perf_timeout
            count = 0

            while sample.kit.app.is_running() and end_time > time.perf_counter():
                    sample.kit.update(1.0 / 60.0)
                    fps = sample._viewport.get_viewport_window().get_fps()
                    fps_count = fps_count + fps
                    count = count + 1

    print(f"\n\ ----------- Avg. FPS over {args.perf_timeout} sec : {fps_count/count}-----------")
    sample.stop()
