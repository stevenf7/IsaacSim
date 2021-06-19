# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
import time
import carb
from omni.isaac.python_app import OmniKitHelper

CONFIG = {
    "experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit',
    "renderer": "RayTracedLighting",
    "headless": True,
}

if __name__ == "__main__":
    # Example ROS bridge sample showing manual control over messages
    kit = OmniKitHelper(config=CONFIG)
    import omni
    from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
    from pxr import Sdf

    # enable ROS bridge extension
    ext_manager = omni.kit.app.get_app().get_extension_manager()
    ext_manager.set_extension_enabled_immediate("omni.isaac.ros_bridge", True)

    # Locate /Isaac folder on nucleus server to load sample

    result, nucleus_server = find_nucleus_server()
    if result is False:
        carb.log_error("Could not find nucleus server with /Isaac folder, exiting")
        exit()
    usd_path = nucleus_server + "/Isaac/Samples/ROS/Scenario/carter_warehouse_navigation.usd"
    omni.usd.get_context().open_stage(usd_path, None)
    # Wait two frames so that stage starts loading
    kit.app.update()
    kit.app.update()

    print("Loading stage...")
    while kit.is_loading():
        kit.update(1.0 / 60.0)
    print("Loading Complete")

    # Disable all ROS components so we can demonstrate publishing manually
    # Otherwise, if a component is enabled, it will publish every timestep
    omni.kit.commands.execute(
        "ChangeProperty", prop_path=Sdf.Path("/World/Carter_ROS/ROS_Camera_Stereo_Right.enabled"), value=False
    )
    omni.kit.commands.execute(
        "ChangeProperty", prop_path=Sdf.Path("/World/Carter_ROS/ROS_Camera_Stereo_Left.enabled"), value=False
    )
    omni.kit.commands.execute("ChangeProperty", prop_path=Sdf.Path("/World/Carter_ROS/ROS_Lidar.enabled"), value=False)
    omni.kit.commands.execute(
        "ChangeProperty", prop_path=Sdf.Path("/World/Carter_ROS/ROS_DifferentialBase.enabled"), value=False
    )
    omni.kit.commands.execute(
        "ChangeProperty", prop_path=Sdf.Path("/World/Carter_ROS/ROS_Carter_Lidar_Broadcaster.enabled"), value=False
    )
    omni.kit.commands.execute(
        "ChangeProperty", prop_path=Sdf.Path("/World/Carter_ROS/ROS_Carter_Broadcaster.enabled"), value=False
    )
    omni.kit.commands.execute("ChangeProperty", prop_path=Sdf.Path("/World/ROS_Clock.enabled"), value=False)
    kit.play()
    kit.update(1.0 / 60.0)
    # Tick all of the components once to make sure all of the ROS nodes are initialized
    omni.kit.commands.execute("RosBridgeTickComponent", path="/World/Carter_ROS/ROS_Camera_Stereo_Right")
    omni.kit.commands.execute("RosBridgeTickComponent", path="/World/Carter_ROS/ROS_Camera_Stereo_Left")
    omni.kit.commands.execute("RosBridgeTickComponent", path="/World/Carter_ROS/ROS_Lidar")
    omni.kit.commands.execute("RosBridgeTickComponent", path="/World/Carter_ROS/ROS_DifferentialBase")
    omni.kit.commands.execute("RosBridgeTickComponent", path="/World/Carter_ROS/ROS_Carter_Lidar_Broadcaster")
    omni.kit.commands.execute("RosBridgeTickComponent", path="/World/Carter_ROS/ROS_Carter_Broadcaster")
    # Simulate for one second to warm up sim and let everything settle
    for frame in range(60):
        kit.update(1.0 / 60.0)

    # from rosgraph_msgs.msg import Clock
    # import rospy

    # # create a clock using sim time
    # result, prim = omni.kit.commands.execute(
    #     "ROSBridgeCreateClock", path="/ROS_Clock_Sim", clock_topic="/sim_time", sim_time=True
    # )
    # # create a clock using system time
    # result, prim = omni.kit.commands.execute(
    #     "ROSBridgeCreateClock", path="/ROS_Clock_System", clock_topic="/system_time", sim_time=False
    # )
    # # create a clock which we will publish manually, set enabled to false to make it manually controlled
    # result, prim = omni.kit.commands.execute(
    #     "ROSBridgeCreateClock", path="/ROS_Clock_Manual", clock_topic="/manual_time", sim_time=True, enabled=False
    # )
    # kit.update()
    # kit.update()

    # # Define ROS callbacks
    # def sim_clock_callback(data):
    #     print("sim time:", data.clock.to_sec())

    # def system_clock_callback(data):
    #     print("system time:", data.clock.to_sec())

    # def manual_clock_callback(data):
    #     print("manual stepped sim time:", data.clock.to_sec())

    # # Create rospy ndoe
    # rospy.init_node("isaac_sim_test_gripper", anonymous=True, disable_signals=True, log_level=rospy.ERROR)
    # # create subscribers
    # sim_clock_sub = rospy.Subscriber("sim_time", Clock, sim_clock_callback)
    # system_clock_sub = rospy.Subscriber("system_time", Clock, system_clock_callback)
    # manual_clock_sub = rospy.Subscriber("manual_time", Clock, manual_clock_callback)
    # time.sleep(1.0)
    # # start simulation
    # kit.play()

    # # perform a fixed number of steps with fixed step size
    # for frame in range(20):

    #     # publish manual clock every 10 frames
    #     if frame % 10 == 0:
    #         result, status = omni.kit.commands.execute("RosBridgeTickComponent", path="/ROS_Clock_Manual")

    #     kit.update(1.0 / 60.0)  # runs with a non-realtime clock
    #     # This sleep is to make this sample run a bit more deterministically for the subscriber callback
    #     # In general this sleep is not needed
    #     time.sleep(0.1)

    # # perform a fixed number of steps with realtime clock
    # for frame in range(20):

    #     # publish manual clock every 10 frames
    #     if frame % 10 == 0:
    #         result, status = omni.kit.commands.execute("RosBridgeTickComponent", path="/ROS_Clock_Manual")

    #     kit.update()  # runs with a realtime clock
    #     # This sleep is to make this sample run a bit more deterministically for the subscriber callback
    #     # In general this sleep is not needed
    #     time.sleep(0.1)

    # # cleanup and shutdown
    # sim_clock_sub.unregister()
    # system_clock_sub.unregister()
    # manual_clock_sub.unregister()
    kit.stop()
    kit.shutdown()
