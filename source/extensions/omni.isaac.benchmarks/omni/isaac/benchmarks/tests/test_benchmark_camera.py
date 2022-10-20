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

import omni.graph.core.tests as ogts
import omni.graph.core as og
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import add_reference_to_stage, open_stage_async
from omni.isaac.core.utils.viewports import get_viewport_names
from omni.isaac.core.utils.physics import simulate_async
from omni.isaac.core.utils.rotations import euler_angles_to_quat

# from omni.isaac.core.prims._impl.single_prim_wrapper import set_default_state
from omni.kit.viewport.utility import (
    create_viewport_window,
    get_num_viewports,
    capture_viewport_to_file,
    get_viewport_from_window_name,
)
from omni.isaac.core.utils.viewports import get_viewport_names, get_id_from_index, get_window_from_id, set_camera_view

from omni.kit.widget.viewport.capture import FileCapture

import numpy as np
from ..utils.logger import log_header, log_stamp
import yaml


class TestBenchmarkCamera(ogts.OmniGraphTestCase):
    async def setUp(self):
        await ogts.setup_test_environment()
        self._timeline = omni.timeline.get_timeline_interface()
        # clear all the viewports
        for i in range(get_num_viewports()):
            window = get_window_from_id(get_id_from_index(i))
            if window:
                window.destroy()

    # ----------------------------------------------------------------------
    async def tearDown(self):
        # clear all the viewports
        # for window_name in get_viewport_names():
        #     window = get_viewport_from_window_name(window_name)
        #     window.destroy()
        await omni.kit.stage_templates.new_stage_async()

    # ----------------------------------------------------------------------
    async def test_benchmark_camera_sequence(self):
        # use benchmark_camera_single.usd for this test
        test_description = "test up to N cameras/viewports for the same scene, no robots"
        stage = omni.usd.get_context().get_stage()
        n_camera = 3
        n_avg = 5  # number of times to take sample and average
        n_resolution = np.array([[1280, 720], [1920, 1080]])
        scene = "warehouse"
        assets_root_path = get_assets_root_path()
        if assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return
        # (result, error) = await open_stage_async(assets_root_path + "/Isaac/Environments/Simple_Warehouse/warehouse.usd")
        # (result, error) = await add_reference_to_stage(usd_path = assets_root_path + "/Isaac/Environments/Simple_Warehouse/warehouse.usd", prim_path = "/World/Warehouse")

        # setup data logging file
        data_dir, data_file_path = log_header()
        # log_stamp(data_file_path)
        test_params = {
            "resolutions": str(n_resolution),
            "n_camera": n_camera,
            "n_avg": n_avg,
            "scene": scene,
            "robot": "None",
            "sensors": "None",
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
                @ fps_raw: [n_camera x n_avg x n_camera], rows are filled to the i'th row depending on how many viewports are open at each round, 0 fills the rest of the rows up to n_camera
                @ fps_mean: [mx1], m = # of total cameras added, (e.g. the i'th element = the fps average across n_avg samples of having i viewports/cameras open) 
                @ fps_var_samples: [mx1], variance across samples (if large means performance isn't stable)
                @ fps_var_viewports: [mx1], variance across viewports (if large then viewports are rendering at different rates)
        """

        # clear all existing viewports (except for one)
        def clear_all_viewports():
            for i in reversed(range(get_num_viewports())):
                window = get_window_from_id(get_id_from_index(i))
                if window:
                    window.destroy()

        self._timeline.play()

        for r in range(np.shape(n_resolution)[0]):
            resolution = n_resolution[r]
            print("resolution is set at ", resolution)
            # data arrays
            fps_raw = np.zeros([n_camera, n_avg, n_camera])
            fps_mean = np.zeros([n_camera, 1])
            fps_var_samples = np.zeros([n_camera, 1])
            fps_var_viewports = np.zeros([n_camera, 1])

            clear_all_viewports()
            for i in range(n_camera):

                # add a camera on stage
                camera_path = "/World/Camera_" + str(i)
                viewport_name = "Viewport " + str(i)
                stage = omni.usd.get_context().get_stage()
                camera_prim = stage.DefinePrim(camera_path, "Camera")
                q = euler_angles_to_quat([90, 0, 90 + 360 / n_camera], degrees=True)
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

                # take a sample 2 seconds apart
                for j in range(n_avg):
                    for s in range(120):
                        await omni.kit.app.get_app().next_update_async()

                    viewport_names = get_viewport_names()
                    for k in range(get_num_viewports()):
                        viewport_window = get_viewport_from_window_name(window_name=viewport_names[k])
                        fps_raw[i, j, k] = viewport_window.fps
                        # print("fps",viewport_window.fps)
                        # print("resolution", viewport_window.resolution)
                        # print("camera", viewport_window.camera_path)

                    # end of cycling through viewports
                # end of taking multiple samples
                # get memory data
                # memory_array[] = dat
                cpu_memory = []
                gpu_memory = []
            # end of adding cameras
            resolution_data = {
                "resolution": str(resolution),
                "data": {"fps_raw": str(fps_raw), "cpu_memory": cpu_memory, "gpu_memory": gpu_memory},
            }
            with open(data_file_path, "a") as f:
                yaml.safe_dump(resolution_data, f)
                # yaml.safe_dump(memory_data,f)
            f.close()

            print("fps_raw: ", fps_raw)

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
