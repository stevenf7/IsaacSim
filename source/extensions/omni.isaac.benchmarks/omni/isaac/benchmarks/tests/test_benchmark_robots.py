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

from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import open_stage_async


from omni.isaac.wheeled_robots.robots import WheeledRobot
from omni.isaac.core.utils.types import ArticulationAction


from omni.kit.viewport.utility import (
    get_active_viewport,
    create_viewport_window,
    get_viewport_from_window_name,
    get_active_viewport_and_window,
    get_num_viewports,
)
from omni.isaac.core.utils.viewports import set_camera_view, get_viewport_names
from omni.kit.widget.viewport.capture import FileCapture

import numpy as np
from ..utils.logger import log_header, get_memory_stats
from ..utils.helper import delete_all_viewports, delete_prim_and_children
import yaml
import asyncio


class TestBenchmarkRobots(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        pass

    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    # ----------------------------------------------------------------------
    async def test_benchmark_robots_only(self):
        test_description = "test up to N robots, no sensors, no camera, single scene"
        print(test_description)
        n_robot = 3  # there might be a limit to this due to the positioning of the robot on the scene
        n_avg = 5  # number of times to take sample and average
        n_resolution = np.array([[1280, 720], [1920, 1080]])
        robot_path = "/Isaac/Robots/Carter/carter_v2.usd"
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
            "n_robot": n_robot,
            "n_avg": n_avg,
            "scene": scene_path,
            "robot": robot_path,
            "sensors": "None",
            "fps_raw format": {"row": "data when j robots are loaded", "column": "samples"},
        }

        with open(data_file_path, "a") as f:
            yaml.safe_dump(test_params, f)
        f.close()

        """
            data collection loop: for each loop, add a robot and turn off lidar
            data formats:
                @ gpu memory: [nxm],  n = # of gpus, m = # of total robots added
                @ cpu memory: [mx1], m = # of total robots added
                @ fps_raw: [n_robot x n_avg], row = j'th row means j robots are loaded when taken data in this row, column = samples
        """
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()

        for r in range(np.shape(n_resolution)[0]):
            resolution = n_resolution[r]
            print("resolution is set at ", resolution)

            ## Delete current viewports and open a new one for a new resolution
            delete_all_viewports()
            await omni.kit.app.get_app().next_update_async()
            create_viewport_window(name="Viewport")
            viewport_api, active_window = get_active_viewport_and_window()
            viewport_api.set_texture_resolution(resolution)
            await omni.kit.app.get_app().next_update_async()
            await omni.kit.app.get_app().next_update_async()
            set_camera_view(eye=[-6, -15.5, 6.5], target=[-6, 10.5, -1], camera_prim_path="/OmniverseKit_Persp")

            # remove all robots that may already be on stage
            delete_prim_and_children("/Robots")
            await omni.kit.app.get_app().next_update_async()

            # test loop
            stage = omni.usd.get_context().get_stage()
            fps_raw = np.zeros([n_robot, n_avg])
            cpu_raw = np.zeros([n_robot, n_avg])
            gpu_raw = np.zeros([n_robot, n_avg])
            for i in range(n_robot):
                robot_prim_path = "/Robots/Robot_" + str(i)
                robot_usd_path = assets_root_path + robot_path
                # position the robot robot
                robot_position = np.array([-2 * i, 0, 0])
                current_robot = WheeledRobot(
                    prim_path=robot_prim_path,
                    wheel_dof_names=["joint_wheel_left", "joint_wheel_right"],
                    create_robot=True,
                    usd_path=robot_usd_path,
                    position=robot_position,
                )
                # disable lidar sensors
                lidar_prim_path = robot_prim_path + "/chassis_link/carter_lidar"
                lidar_prim = stage.GetPrimAtPath(lidar_prim_path)
                lidar_prim.GetAttribute("enabled").Set(False)

                await omni.kit.app.get_app().next_update_async()
                await omni.kit.app.get_app().next_update_async()
                current_robot.initialize()
                # start the robot rotating in place so not to run into each
                current_robot.apply_wheel_actions(
                    ArticulationAction(joint_positions=None, joint_efforts=None, joint_velocities=5 * np.array([0, 1]))
                )

                # take a sample 2 seconds apart
                for j in range(n_avg):
                    for s in range(120):
                        await omni.kit.app.get_app().next_update_async()
                    # get performance data
                    viewport_window = get_active_viewport()
                    fps_raw[i, j] = viewport_window.fps
                    # get memory data
                    memory_usage = get_memory_stats()
                    cpu_raw[i, j] = memory_usage["System Memory"]["RAM"]
                    gpu_raw[i, j] = memory_usage["System Memory"]["VRAM"]

                # end of taking multiple samples

            # end of adding robots
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

        # save a snapshot of scene to make sure the robots are all in good positions
        image_path = data_dir + "/robot_only_snapshot"
        viewport_window = get_active_viewport()
        capture = viewport_window.schedule_capture(FileCapture(image_path))
        captured_aovs = await capture.wait_for_result()
        if captured_aovs:
            print(f'AOV "{captured_aovs[0]}" was written to "{image_path}"')
        else:
            print(f'No image was written to "{image_path}"')

    # ----------------------------------------------------------------------
    async def test_benchmark_robots_lidar(self):
        test_description = "test up to N robots, each with a lidar sensor, no cameras, single viewport"
        print(test_description)
        n_robot = 3  # there might be a limit to this due to the positioning of the robot on the scene
        n_avg = 5  # number of times to take sample and average
        n_resolution = np.array([[1280, 720], [1920, 1080]])
        robot_path = "/Isaac/Robots/Carter/carter_v2.usd"
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
            "n_robots": n_robot,
            "n_avg": n_avg,
            "scene": scene_path,
            "robot": robot_path,
            "sensors": "lidar",
            "fps_raw format": {"row": "data when j robots are loaded", "column": "samples"},
        }

        with open(data_file_path, "a") as f:
            yaml.safe_dump(test_params, f)
        f.close()

        """
            data collection loop: for each loop, add a robot and turn on the lidar
            data formats:
                @ gpu memory: [nxm],  n = # of gpus, m = # of total cameras added
                @ cpu memory: [mx1], m = # of total cameras added
                @ fps_raw: [n_robot x n_avg], row = j'th row means j robots are loaded when taken data in this row, column = samples
        """
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()

        for r in range(np.shape(n_resolution)[0]):
            resolution = n_resolution[r]
            print("resolution is set at ", resolution)

            ## Delete current viewports and open a new one for a new resolution
            delete_all_viewports()
            await omni.kit.app.get_app().next_update_async()
            create_viewport_window(name="Viewport")
            viewport_api, active_window = get_active_viewport_and_window()
            viewport_api.set_texture_resolution(resolution)
            await omni.kit.app.get_app().next_update_async()
            await omni.kit.app.get_app().next_update_async()
            set_camera_view(eye=[-6, -15.5, 6.5], target=[-6, 10.5, -1], camera_prim_path="/OmniverseKit_Persp")

            # remove all robots that may already be on stage
            delete_prim_and_children("/Robots")
            await omni.kit.app.get_app().next_update_async()

            # test loop
            stage = omni.usd.get_context().get_stage()
            fps_raw = np.zeros([n_robot, n_avg])
            cpu_raw = np.zeros([n_robot, n_avg])
            gpu_raw = np.zeros([n_robot, n_avg])
            for i in range(n_robot):
                robot_prim_path = "/Robots/Robot_" + str(i)
                robot_usd_path = assets_root_path + robot_path
                # position the robot robot
                robot_position = np.array([-2 * i, 0, 0])
                current_robot = WheeledRobot(
                    prim_path=robot_prim_path,
                    wheel_dof_names=["joint_wheel_left", "joint_wheel_right"],
                    create_robot=True,
                    usd_path=robot_usd_path,
                    position=robot_position,
                )
                # make sure the lidars are enabled
                lidar_prim_path = robot_prim_path + "/chassis_link/carter_lidar"
                lidar_prim = stage.GetPrimAtPath(lidar_prim_path)
                lidar_prim.GetAttribute("enabled").Set(True)
                # lidar_prim.GetAttribute("drawLines").Set(True)

                await omni.kit.app.get_app().next_update_async()
                await omni.kit.app.get_app().next_update_async()
                current_robot.initialize()
                # start the robot rotating in place so not to run into each
                current_robot.apply_wheel_actions(
                    ArticulationAction(joint_positions=None, joint_efforts=None, joint_velocities=5 * np.array([0, 1]))
                )

                # take a sample 2 seconds apart
                for j in range(n_avg):
                    for s in range(120):
                        await omni.kit.app.get_app().next_update_async()
                    # get performance data
                    viewport_window = get_active_viewport()
                    fps_raw[i, j] = viewport_window.fps
                    # get memory data
                    memory_usage = get_memory_stats()
                    cpu_raw[i, j] = memory_usage["System Memory"]["RAM"]
                    gpu_raw[i, j] = memory_usage["System Memory"]["VRAM"]

                # end of taking multiple samples

            # end of adding robots
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

        # save a snapshot of scene to make sure the robots are all in good positions
        image_path = data_dir + "/robot_lidar_snapshot"
        viewport_window = get_active_viewport()
        capture = viewport_window.schedule_capture(FileCapture(image_path))
        captured_aovs = await capture.wait_for_result()
        if captured_aovs:
            print(f'AOV "{captured_aovs[0]}" was written to "{image_path}"')
        else:
            print(f'No image was written to "{image_path}"')

    # ----------------------------------------------------------------------
    async def test_benchmark_robots_camera(self):
        test_description = "test up to N robots, each with a camera with dedicated viewports, no sensors"
        print(test_description)
        n_robot = 3  # there might be a limit to this due to the positioning of the robot on the scene
        n_avg = 5  # number of times to take sample and average
        n_resolution = np.array([[1280, 720], [1920, 1080]])
        robot_path = "/Isaac/Robots/Carter/carter_v2.usd"
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
            "n_robot": n_robot,
            "n_avg": n_avg,
            "scene": scene_path,
            "robot": robot_path,
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
            data collection loop: for each loop, add a robot and a corresponding viewport
            data formats:
                @ gpu memory: [nxm],  n = # of gpus, m = # of total cameras added
                @ cpu memory: [mx1], m = # of total cameras added
                @ fps_raw: [n_robot x n_avg x n_robot], rows are filled to the i'th column depending on how many viewports are open at each round, 0 fills the rest of the rows up to n_camera
        """
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()

        for r in range(np.shape(n_resolution)[0]):
            resolution = n_resolution[r]
            print("resolution is set at ", resolution)
            ## Delete current viewports
            delete_all_viewports()
            await omni.kit.app.get_app().next_update_async()

            # remove all robots that may already be on stage
            delete_prim_and_children("/Robots")
            await omni.kit.app.get_app().next_update_async()

            # test loop
            stage = omni.usd.get_context().get_stage()
            cpu_raw = np.zeros([n_robot, n_avg])
            gpu_raw = np.zeros([n_robot, n_avg])
            fps_raw = np.zeros([n_robot, n_avg, n_robot])

            for i in range(n_robot):

                # add a viewport
                viewport_name = "Viewport " + str(i)
                create_viewport_window(name=viewport_name)
                viewport_window = get_viewport_from_window_name(window_name=viewport_name)
                stage = omni.usd.get_context().get_stage()
                viewport_window.set_texture_resolution(resolution)
                # wait until the window is actually created
                while viewport_name not in get_viewport_names():
                    await omni.kit.app.get_app().next_update_async()
                # wait until the scene is loaded in the given viewport
                while omni.usd.get_context().get_stage_loading_status()[2] > 0:
                    print("asset still loading, waiting to finish")
                    await asyncio.sleep(1.0)
                await omni.kit.app.get_app().next_update_async()

                # add a robot
                robot_prim_path = "/Robots/Robot_" + str(i)
                robot_camera_prim_path = (
                    robot_prim_path + "/chassis_link/stereo_cam_right/stereo_cam_right_sensor_frame/camera_sensor_right"
                )
                robot_usd_path = assets_root_path + robot_path
                # position the robot robot
                robot_position = np.array([-2 * i, 0, 0])
                current_robot = WheeledRobot(
                    prim_path=robot_prim_path,
                    wheel_dof_names=["joint_wheel_left", "joint_wheel_right"],
                    create_robot=True,
                    usd_path=robot_usd_path,
                    position=robot_position,
                )

                # make sure the lidars are disabled
                lidar_prim_path = robot_prim_path + "/chassis_link/carter_lidar"
                lidar_prim = stage.GetPrimAtPath(lidar_prim_path)
                lidar_prim.GetAttribute("enabled").Set(False)

                # set the new viewport's camera to the robot's right stereo
                viewport_window.set_active_camera(robot_camera_prim_path)
                await omni.kit.app.get_app().next_update_async()
                await omni.kit.app.get_app().next_update_async()

                # move the robot
                current_robot.initialize()
                # start the robot rotating in place so not to run into each
                current_robot.apply_wheel_actions(
                    ArticulationAction(joint_positions=None, joint_efforts=None, joint_velocities=5 * np.array([0, 1]))
                )

                # take a sample 2 seconds apart
                for j in range(n_avg):
                    for s in range(120):
                        await omni.kit.app.get_app().next_update_async()

                    # get performance data from each viewport
                    viewport_names = get_viewport_names()
                    for k in range(get_num_viewports()):
                        viewport_window = get_viewport_from_window_name(window_name=viewport_names[k])
                        fps_raw[i, j, k] = viewport_window.fps

                    # get memory data
                    memory_usage = get_memory_stats()
                    cpu_raw[i, j] = memory_usage["System Memory"]["RAM"]
                    gpu_raw[i, j] = memory_usage["System Memory"]["VRAM"]

                # end of taking multiple samples

            # end of adding robots
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

    # ----------------------------------------------------------------------
    async def test_benchmark_robots_camera_lidar(self):
        test_description = "test up to N robots, each with a camera with dedicated viewports, lidars on"
        print(test_description)
        n_robot = 3  # there might be a limit to this due to the positioning of the robot on the scene
        n_avg = 5  # number of times to take sample and average
        n_resolution = np.array([[1280, 720], [1920, 1080]])
        robot_path = "/Isaac/Robots/Carter/carter_v2.usd"
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
            "n_robot": n_robot,
            "n_avg": n_avg,
            "scene": scene_path,
            "robot": robot_path,
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
            data collection loop: for each loop, add a robot and a corresponding viewport
            data formats:
                @ gpu memory: [nxm],  n = # of gpus, m = # of total cameras added
                @ cpu memory: [mx1], m = # of total cameras added
                @ fps_raw: [n_robot x n_avg x n_robot], rows are filled to the i'th column depending on how many viewports are open at each round, 0 fills the rest of the rows up to n_camera
        """
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()

        for r in range(np.shape(n_resolution)[0]):
            resolution = n_resolution[r]
            print("resolution is set at ", resolution)
            ## Delete current viewports
            delete_all_viewports()
            await omni.kit.app.get_app().next_update_async()

            # remove all robots that may already be on stage
            delete_prim_and_children("/Robots")
            await omni.kit.app.get_app().next_update_async()

            # test loop
            stage = omni.usd.get_context().get_stage()
            cpu_raw = np.zeros([n_robot, n_avg])
            gpu_raw = np.zeros([n_robot, n_avg])
            fps_raw = np.zeros([n_robot, n_avg, n_robot])

            for i in range(n_robot):

                # add a viewport
                viewport_name = "Viewport " + str(i)
                create_viewport_window(name=viewport_name)
                viewport_window = get_viewport_from_window_name(window_name=viewport_name)
                stage = omni.usd.get_context().get_stage()
                viewport_window.set_texture_resolution(resolution)
                # wait until the window is actually created
                while viewport_name not in get_viewport_names():
                    await omni.kit.app.get_app().next_update_async()
                # wait until the scene is loaded in the given viewport
                while omni.usd.get_context().get_stage_loading_status()[2] > 0:
                    print("asset still loading, waiting to finish")
                    await asyncio.sleep(1.0)
                await omni.kit.app.get_app().next_update_async()

                # add a robot
                robot_prim_path = "/Robots/Robot_" + str(i)
                robot_camera_prim_path = (
                    robot_prim_path + "/chassis_link/stereo_cam_right/stereo_cam_right_sensor_frame/camera_sensor_right"
                )
                robot_usd_path = assets_root_path + robot_path
                # position the robot robot
                robot_position = np.array([-2 * i, 0, 0])
                current_robot = WheeledRobot(
                    prim_path=robot_prim_path,
                    wheel_dof_names=["joint_wheel_left", "joint_wheel_right"],
                    create_robot=True,
                    usd_path=robot_usd_path,
                    position=robot_position,
                )

                # make sure the lidars are disabled
                lidar_prim_path = robot_prim_path + "/chassis_link/carter_lidar"
                lidar_prim = stage.GetPrimAtPath(lidar_prim_path)
                lidar_prim.GetAttribute("enabled").Set(True)

                # set the new viewport's camera to the robot's right stereo
                viewport_window.set_active_camera(robot_camera_prim_path)
                await omni.kit.app.get_app().next_update_async()
                await omni.kit.app.get_app().next_update_async()

                # move the robot
                current_robot.initialize()
                # start the robot rotating in place so not to run into each
                current_robot.apply_wheel_actions(
                    ArticulationAction(joint_positions=None, joint_efforts=None, joint_velocities=5 * np.array([0, 1]))
                )

                # take a sample 2 seconds apart
                for j in range(n_avg):
                    for s in range(120):
                        await omni.kit.app.get_app().next_update_async()

                    # get performance data from each viewport
                    viewport_names = get_viewport_names()
                    for k in range(get_num_viewports()):
                        viewport_window = get_viewport_from_window_name(window_name=viewport_names[k])
                        fps_raw[i, j, k] = viewport_window.fps

                    # get memory data
                    memory_usage = get_memory_stats()
                    cpu_raw[i, j] = memory_usage["System Memory"]["RAM"]
                    gpu_raw[i, j] = memory_usage["System Memory"]["VRAM"]

                # end of taking multiple samples

            # end of adding robots
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
