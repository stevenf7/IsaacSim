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
from omni.isaac.core.utils.stage import add_reference_to_stage, open_stage_async
from omni.isaac.core.utils.physics import simulate_async
from omni.isaac.core.utils.rotations import euler_angles_to_quat

# from omni.isaac.core.prims._impl.single_prim_wrapper import set_default_state
from omni.kit.viewport.utility import get_active_viewport_and_window


import numpy as np
from ..utils.logger import log_header, log_stamp, get_cpu_info, get_gpu_info
import yaml
import asyncio


class TestBenchmarkLidar(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        self._timeline = omni.timeline.get_timeline_interface()
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        pass

    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    # ----------------------------------------------------------------------
    async def test_benchmark_lidar_sequence(self):
        test_description = "test up to N lidars for the same scene, no robots"
        stage = omni.usd.get_context().get_stage()
        n_sensor = 3
        n_avg = 5  # number of times to take sample and average
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
        # log_stamp(data_file_path)
        test_params = {
            "n_sensor": n_sensor,
            "n_avg": n_avg,
            "scene": scene_path,
            "robot": "None",
            "sensors": "Physics Lidar",
            "fps_raw format": {
                "row": "data from each viewport n",
                "column": "samples",
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
                @ fps_raw: [n_sensors x n_avg], 
                @ fps_mean: [mx1], m = # of total cameras added, (e.g. the i'th element = the fps average across n_avg samples of having i viewports/cameras open) 
                @ fps_var_samples: [mx1], variance across samples (if large means performance isn't stable)
                @ fps_var_viewports: [mx1], variance across viewports (if large then viewports are rendering at different rates)
        """

        def add_lidar(prim_path, translation=Gf.Vec3f(0, 0, 0), orientation=Gf.Vec4f(0, 0, 0, 0)):
            result, lidar = omni.kit.commands.execute(
                "RangeSensorCreateLidar",
                path=prim_path,
                parent=None,
                min_range=0.4,
                max_range=100.0,
                draw_points=True,
                draw_lines=True,
                horizontal_fov=360.0,
                vertical_fov=30.0,
                horizontal_resolution=0.4,
                vertical_resolution=4.0,
                rotation_rate=0.0,
                high_lod=False,
                yaw_offset=0.0,
            )
            lidar_prim = lidar.GetPrim()

            if "xformOp:translate" not in lidar_prim.GetPropertyNames():
                UsdGeom.Xformable(lidar_prim).AddTranslateOp()
            if "xformOp:orient" not in lidar_prim.GetPropertyNames():
                UsdGeom.Xformable(lidar_prim).AddOrientOp()

            lidar_prim.GetAttribute("xformOp:translate").Set(translation)
            lidar_prim.GetAttribute("xformOp:orient").Set(orientation)

        # data arrays
        fps_raw = np.zeros([n_sensor, n_avg])
        fps_mean = np.zeros([n_sensor, 1])
        fps_var_samples = np.zeros([n_sensor, 1])
        fps_var_viewports = np.zeros([n_sensor, 1])

        for i in range(n_sensor):

            # add a sensor on stage
            sensor_path = "/World/Lidar_" + str(i)
            sensor_translation = Gf.Vec3f([-8, 13, 2.0])  # these positions are used for full_warehouse.usd
            q = euler_angles_to_quat([90, 0, 90 + i * 360 / n_sensor], degrees=True)
            sensor_orientation = Gf.Quatf(q[0], q[1], q[2], q[3])
            add_lidar(prim_path=sensor_path, translation=sensor_translation, orientation=sensor_orientation)
            # Run for a second
            self._timeline.play()
            await simulate_async(1.0)
            self._timeline.pause()
            print("lidar {} added at {}".format(i, sensor_path))

            # take a sample one second apart (#TODO: or should it be take a sample that last n seconds and then average)
            for j in range(n_avg):
                for s in range(60):
                    await omni.kit.app.get_app().next_update_async()

                viewport_api, active_window = get_active_viewport_and_window()
                fps_raw[i, j] = viewport_api.fps
                # print("fps",viewport_window.fps)

            # end of taking multiple samples
            # get memory data
            cpu_info = get_cpu_info()
            gpu_info = get_gpu_info()

        # end of adding cameras
        per_res_data = {"data": {"fps_raw": str(fps_raw), "cpu_info": cpu_info, "gpu_info": gpu_info}}
        with open(data_file_path, "a") as f:
            yaml.safe_dump(per_res_data, f)
        f.close()

        print("fps_raw: ", fps_raw)
        print("cpu_info: ", cpu_info)
        print("gpu_info: ", gpu_info)
