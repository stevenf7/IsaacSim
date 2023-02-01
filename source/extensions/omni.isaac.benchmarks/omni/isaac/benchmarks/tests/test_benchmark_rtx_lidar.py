# Copyright (c) 2018-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import omni.kit.test
from pxr import Gf


from omni.isaac.core.utils.render_product import create_hydra_texture
from omni.syntheticdata import sensors
from omni.isaac.core.utils.viewports import destroy_all_viewports

import numpy as np
from ..utils.logger import log_header, get_memory_stats
import yaml
import asyncio


class TestBenchmarkRtxLidar(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        pass

    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    # ----------------------------------------------------------------------
    async def test_benchmark_rtx_lidar(self):
        test_description = "test up to N RTX lidar, no robots"
        print(test_description)
        stage = omni.usd.get_context().get_stage()
        n_sensor = 3
        n_avg = 5  # number of times to take sample and average

        # setup data logging file
        data_dir, data_file_path = log_header()
        test_params = {
            "n_sensor": n_sensor,
            "n_avg": n_avg,
            "scene": "None",
            "robot": "None",
            "sensors": "RTX lidar",
            "raw data format": {"row": "data when j sensors are loaded", "column": "samples"},
        }

        with open(data_file_path, "a") as f:
            yaml.safe_dump(test_params, f)
        f.close()

        """
            data collection loop: for each loop, add a sensor, then averaging across n_avg samples.
        """

        destroy_all_viewports()
        await omni.kit.app.get_app().next_update_async()

        # data arrays
        cpu_raw = np.zeros([n_sensor, n_avg])
        gpu_raw = np.zeros([n_sensor, n_avg])

        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        for i in range(n_sensor):

            # add a camera on stage
            lidar_path = "/World/RtxLidar_" + str(i)
            sensor_translation = Gf.Vec3f([-8, 13 + i * 2.0, 2.0])  # these positions are used for full_warehouse.usd

            _, (_, sensor) = omni.kit.commands.execute(
                "IsaacSensorCreateRtxLidar",
                path=lidar_path,
                parent=None,
                config="Example_Rotary",
                translation=sensor_translation,
                orientation=Gf.Quatd(0.5, 0.5, -0.5, -0.5),  # Gf.Quatd is w,i,j,k
            )
            _, render_product_path = create_hydra_texture([1, 1], sensor.GetPath().pathString)

            # Create the post process graph that publishes the render var
            sensors.get_synthetic_data().activate_node_template(
                "RtxSensorCpu" + "IsaacReadRTXLidarFlatScan", 0, [render_product_path]
            )

            await omni.kit.app.get_app().next_update_async()

            # take a sample 2 seconds apart
            for j in range(n_avg):

                for s in range(120):
                    await omni.kit.app.get_app().next_update_async()

                # get memory data
                memory_usage = get_memory_stats()
                cpu_raw[i, j] = memory_usage["System Memory"]["RAM"]
                gpu_raw[i, j] = memory_usage["System Memory"]["VRAM"]

            # end of taking multiple samples

        timeline.stop()

        # end of adding cameras
        per_res_data = {"data": {"cpu_raw": str(cpu_raw), "gpu_raw": str(gpu_raw)}}
        with open(data_file_path, "a") as f:
            yaml.safe_dump(per_res_data, f)
        f.close()

        print("cpu_info: ", cpu_raw)
        print("gpu_info: ", gpu_raw)

    # end of trying different resolutions
