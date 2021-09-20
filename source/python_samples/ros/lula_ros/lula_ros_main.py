# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
import carb
from omni.isaac.python_app import OmniKitHelper

CONFIG = {
    "experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit',
    "renderer": "RayTracedLighting",
    "headless": False,
}

if __name__ == "__main__":
    kit = OmniKitHelper(config=CONFIG)
    import omni

    # enable ROS bridge extension
    ext_manager = omni.kit.app.get_app().get_extension_manager()
    ext_manager.set_extension_enabled_immediate("omni.isaac.ros_bridge", True)
    # get asset base path
    dc_id = ext_manager.get_enabled_extension_id("omni.isaac.dynamic_control")
    dc_extension_path = ext_manager.get_extension_path(dc_id)

    # Note that this is not the system level rospy, but one compiled for omniverse
    import argparse
    import sys
    import rospy
    from sensor_msgs.msg import JointState
    import franka
    import rmpflow_commander
    from joint_state_meta import JointStateMeta
    from interpolated_command_listener import InterpolatedCommandListener
    from omni.isaac.dynamic_control import _dynamic_control
    from pxr import Gf, UsdGeom, UsdLux, Sdf, UsdPhysics, PhysxSchema
    from omni.physx.scripts.physicsUtils import add_ground_plane

    # check if rosmaster node is running
    # this is to prevent this sample from waiting indefinetly if roscore is not running
    # can be removed in regular usage
    kit.update()
    result, check = omni.kit.commands.execute("RosBridgeRosMasterCheck")
    if not check:
        carb.log_error("Please run roscore before executing this script")
        kit.stop()
        kit.shutdown()
        exit()

    # make node at the start before we do anything else
    node_name = "lula_ros"
    rospy.init_node(node_name, anonymous=True, disable_signals=True, log_level=rospy.ERROR)
    parser = argparse.ArgumentParser(node_name)
    parser.add_argument(
        "--is_real_robot", action="store_true", help="Set this flag when using Isaac Sim to control a physical robot."
    )
    args = parser.parse_args()

    omni.usd.get_context().new_stage()
    stage = kit.get_stage()
    # create a simple env with a physics scene, a ground plane and a light
    scene = UsdPhysics.Scene.Define(stage, "/physics")
    scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
    scene.CreateGravityMagnitudeAttr().Set(981.0)

    PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath("/physics"))
    physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(stage, "/physics")
    physxSceneAPI.CreateEnableGPUDynamicsAttr(False)
    physxSceneAPI.CreateBroadphaseTypeAttr("MBP")
    physxSceneAPI.CreateSolverTypeAttr("TGS")
    add_ground_plane(stage, "/groundPlane", "Z", 1000.0, Gf.Vec3f(0.0), Gf.Vec3f(1.0))
    light_prim = UsdLux.DistantLight.Define(stage, Sdf.Path("/World/defaultLight"))
    light_prim.CreateIntensityAttr(500)

    viewport = omni.kit.viewport.get_default_viewport_window()
    viewport.set_camera_position("/OmniverseKit_Persp", 150, -50, 50, True)
    viewport.set_camera_target("/OmniverseKit_Persp", 0, 50, 50, True)

    asset_path = dc_extension_path + "/data/usd/robots/franka/franka.usd"

    dc = _dynamic_control.acquire_dynamic_control_interface()
    rmp_robot = franka.Panda(stage, dc, asset_path, "/panda")
    sim_robot = franka.Panda(stage, dc, asset_path, "/sim_panda")  # our physical robot being simulated

    # move the simulated robot so it doesn't intersect rmp_robot
    omni.kit.commands.execute(
        "TransformPrimCommand",
        path=sim_robot.prim.GetPath(),
        old_transform_matrix=None,
        new_transform_matrix=Gf.Matrix4d().SetTranslateOnly(Gf.Vec3d(0, 100, 0)),
    )

    commander = rmpflow_commander.ROSJointCommander(stage, dc)
    kit.play()
    kit.update()

    rmp_robot.register()
    sim_robot.register()
    rmp_robot.disable_gravity(True)
    sim_robot.disable_gravity(True)

    #### Create a target prim for Motion Generation
    target_prim = UsdGeom.Sphere.Define(stage, "/target")
    target_prim.CreateRadiusAttr(5)

    # Create obstacle.
    obs_prim = UsdGeom.Cube.Define(stage, "/obs")
    obs_prim.CreateSizeAttr(20)
    obs_prim.AddTranslateOp().Set(Gf.Vec3d(75.0, 0.0, 50.0))
    obs_prim.AddRotateXYZOp().Set(Gf.Vec3d(180.0, 0.0, 180.0))

    # settle objects over 3 seconds (3x60 frames)
    for f in range(60 * 3):
        kit.update()

    commander.register(rmp_robot, target_prim, obs_prim)

    joint_state_topic = "/robot/joint_state"
    if not args.is_real_robot:
        js_pub = rospy.Publisher(joint_state_topic, JointState, queue_size=10)
    js_meta = JointStateMeta(joint_state_topic)

    interpolated_command_listener = InterpolatedCommandListener(sim_robot)

    print("\n")
    print("=" * 60)
    if args.is_real_robot:
        print("mode: connecting to real robot")
    else:
        print("mode: using simulated robot")
    print("=" * 60)
    print()

    # run indefinetly until closed
    while kit.app.is_running():
        js_meta.validate_num_publishers()

        commander.update()  # run motion policy and publish/subscribe to ros lula stack
        # code to run our "physical robot":
        # Set the joint state target to the interpolated values
        # this lets physx act as the controller and simulated to the desired pose rather than teleport
        states = (
            interpolated_command_listener.get_latest_interpolated_dof_states()
        )  # this will return none until we get the first interpolated message
        if states is not None:
            sim_robot.set_position_targets(states["pos"])

        if not args.is_real_robot:
            # publish latest "physical" robot state
            joint_state_msg = sim_robot.get_joint_state_message()
            if joint_state_msg is None:
                carb.log_warn("Joint states message is None. Breaking from kit loop.")
                break
            js_pub.publish(joint_state_msg)
        kit.update()  # simulate one frame

    # cleanup and shutdown
    js_pub.unregister()
    kit.stop()
    kit.shutdown()
