# Copyright (c) 2018-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import omni.kit.test
import carb
from pxr import Gf, UsdGeom


from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import open_stage_async
from omni.isaac.core.utils.viewports import get_viewport_names
from omni.isaac.core.utils.rotations import euler_angles_to_quat

# from omni.isaac.core.prims._impl.single_prim_wrapper import set_default_state
from omni.kit.viewport.utility import create_viewport_window, get_num_viewports, get_viewport_from_window_name
from omni.isaac.core.utils.viewports import get_viewport_names

from omni.kit.widget.viewport.capture import FileCapture

import numpy as np
from ..utils.logger import log_header, get_memory_stats
from ..utils.helper import delete_all_viewports
import yaml
import asyncio


class TestBenchmarkCamera(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        pass

    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    # ----------------------------------------------------------------------
    async def test_benchmark_camera_sequence(self):
        test_description = "test up to N cameras each with dedicated viewports, no robots"
        print(test_description)
        stage = omni.usd.get_context().get_stage()
        n_camera = 3
        n_avg = 5  # number of times to take sample and average
        n_resolution = np.array([[1280, 720], [1920, 1080]])
        # scene_path = "/Isaac/Environments/Simple_Room/simple_room.usd"
        scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
        assets_root_path = get_assets_root_path()
        if assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return
        (result, error) = await open_stage_async(assets_root_path + scene_path)
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("asset still loading, waiting to finish")
            await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()

        # setup data logging file
        data_dir, data_file_path = log_header()
        test_params = {
            "n_camera": n_camera,
            "n_avg": n_avg,
            "scene": scene_path,
            "robot": "None",
            "sensors": "camera",
            "fps_raw format": {
                "column": "data from each viewport n",
                "row": "samples",
                "z": "total number of viewports opened",
            },
        }

        with open(data_file_path, "a") as f:
            yaml.safe_dump(test_params, f)
        f.close()

        """
            data collection loop: for each loop, add a camera and a corresponding viewport
            to get fps data: averaging across viewports, and across n_avg samples.
            data formats:
                @ gpu memory: [nxm],  n = # of gpus, m = # of total cameras added
                @ cpu memory: [mx1], m = # of total cameras added
                @ fps_raw: [n_camera x n_avg x n_camera], rows are filled to the i'th column depending on how many viewports are open at each round, 0 fills the rest of the rows up to n_camera
        """

        timeline = omni.timeline.get_timeline_interface()
        timeline.play()

        for r in range(np.shape(n_resolution)[0]):
            resolution = n_resolution[r]
            print("resolution is set at ", resolution)
            delete_all_viewports()
            await omni.kit.app.get_app().next_update_async()

            # data arrays
            fps_raw = np.zeros([n_camera, n_avg, n_camera])
            cpu_raw = np.zeros([n_camera, n_avg])
            gpu_raw = np.zeros([n_camera, n_avg])

            for i in range(n_camera):

                # add a camera on stage
                camera_path = "/World/Camera_" + str(i)
                viewport_name = "Viewport " + str(i)
                stage = omni.usd.get_context().get_stage()
                camera_prim = stage.DefinePrim(camera_path, "Camera")
                camera_translation = Gf.Vec3f([-8, 13, 2.0])  # these positions are used for full_warehouse.usd
                if "xformOp:translate" not in camera_prim.GetPropertyNames():
                    UsdGeom.Xformable(camera_prim).AddTranslateOp()
                camera_prim.GetAttribute("xformOp:translate").Set(camera_translation)
                q = euler_angles_to_quat([90, 0, 90 + i * 360 / n_camera], degrees=True)
                camera_orientation = Gf.Quatf(q[0], q[1], q[2], q[3])
                if "xformOp:orient" not in camera_prim.GetPropertyNames():
                    UsdGeom.Xformable(camera_prim).AddOrientOp()
                camera_prim.GetAttribute("xformOp:orient").Set(
                    camera_orientation
                )  # rotate cameras to look at slightly different view, repeated views affect fps

                create_viewport_window(name=viewport_name)
                viewport_window = get_viewport_from_window_name(window_name=viewport_name)
                viewport_window.set_active_camera(camera_path)
                viewport_window.set_texture_resolution(resolution)
                # wait until the window is actually created
                while viewport_name not in get_viewport_names():
                    await omni.kit.app.get_app().next_update_async()
                # wait until the scene is loaded in the given viewport
                while omni.usd.get_context().get_stage_loading_status()[2] > 0:
                    print("asset still loading, waiting to finish")
                    await asyncio.sleep(1.0)
                await omni.kit.app.get_app().next_update_async()

                # take a sample 2 seconds apart
                for j in range(n_avg):
                    for s in range(120):
                        await omni.kit.app.get_app().next_update_async()

                    # get performance data from each viewport
                    viewport_names = get_viewport_names()
                    for k in range(get_num_viewports()):
                        viewport_window = get_viewport_from_window_name(window_name=viewport_names[k])
                        fps_raw[i, j, k] = viewport_window.fps
                        # print("fps",viewport_window.fps)
                        # print("resolution", viewport_window.resolution)
                        # print("camera", viewport_window.camera_path)

                    # end of cycling through viewports
                    # get memory data
                    memory_usage = get_memory_stats()
                    cpu_raw[i, j] = memory_usage["System Memory"]["RAM"]
                    gpu_raw[i, j] = memory_usage["System Memory"]["VRAM"]

                # end of taking multiple samples

            # end of adding cameras
            per_res_data = {
                "data": {
                    "resolution": str(resolution),
                    "fps_raw": str(fps_raw),
                    "cpu_raw": str(cpu_raw),
                    "gpu_raw": str(gpu_raw),
                }
            }
            with open(data_file_path, "a") as f:
                yaml.safe_dump(per_res_data, f)
            f.close()

            print("fps_raw: ", fps_raw)
            print("cpu_info: ", cpu_raw)
            print("gpu_info: ", gpu_raw)

        # end of trying different resolutions

        # save a snapshot of all the cameras to check if everything was added correctly
        viewport_names = get_viewport_names()
        for v in range(get_num_viewports()):
            image_path = data_dir + "/snapshot_" + str(v)
            viewport_window = get_viewport_from_window_name(window_name=viewport_names[v])
            capture = viewport_window.schedule_capture(FileCapture(image_path))
            captured_aovs = await capture.wait_for_result()
            if captured_aovs:
                print(f'AOV "{captured_aovs[0]}" was written to "{image_path}"')
            else:
                print(f'No image was written to "{image_path}"')
