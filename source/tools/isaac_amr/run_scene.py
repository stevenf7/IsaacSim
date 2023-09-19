# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import argparse
import sys
import time

import carb
import numpy as np
from isaac_amr import GXF_BRIDGE_EXTENSION_NAME, STATUS_FILE_PATH
from omni.isaac.kit import SimulationApp


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        "Play scene with GXF application.", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--headless", action="store_false", help="Run sim in headless mode.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-n", "--num-frames", type=int, default=60, help="Number of frames to run simulation for.")
    group.add_argument(
        "--run-indefinitely", action="store_true", help="True to run simulation indefinitely, False otherwise."
    )
    parser.add_argument("-r", "--rate", type=int, default=60, help="Frame rate (Hz)")
    parser.add_argument("--use-default-atlas", action="store_true", help="Use default atlas entity/component.")
    parser.add_argument(
        "--use-default-clock", action="store_true", help="Use default scheduler entity/clock component."
    )
    parser.add_argument(
        "--use-release-assets", action="store_true", help="Use release assets instead of release candidate assets."
    )
    parser.add_argument(
        "--tcp-server-addr",
        default="127.0.0.1",
        help="TCP server address - for scenes creating GXF app from OmniGraph.",
    )
    parser.add_argument(
        "--tcp-server-port",
        type=int,
        default=7000,
        help="TCP server port - for scenes creating GXF app from OmniGraph.",
    )
    parser.add_argument(
        "--robot", choices=["carter_v2_3"], default=None, help="Type of robot to place or move in scene"
    )
    parser.add_argument(
        "--initial-pos",
        type=float,
        nargs=2,
        default=[0.0, 0.0],
        help="Initial (x, y) position of robot in world coordinates.",
    )
    parser.add_argument(
        "--initial-yaw", type=float, default=0.0, help="Initial yaw position of robot in world coordinates (degrees)."
    )
    parser.add_argument("--status-file", type=str, default=STATUS_FILE_PATH, help="Path to status file.")

    parser.add_argument("scene", type=str, help="Path to scene in Nucleus server")
    parser.add_argument("yaml_path", type=str, nargs="*", help="Path to GXF app YAML file.")

    args, unknown_args = parser.parse_known_args()

    # Create simulation application
    simulation_app = SimulationApp({"renderer": "RayTracedLighting", "headless": args.headless})

    from omni.isaac.core import SimulationContext
    from omni.isaac.core.utils import extensions, nucleus, rotations
    from omni.isaac.core.utils.stage import add_reference_to_stage
    from pxr import Gf

    # Enable GXF bridge extension
    extensions.enable_extension(GXF_BRIDGE_EXTENSION_NAME)
    from omni.isaac.gxf_bridge import AmrAssetTier, GxfRobot, GxfRobotType

    # Open the specified USD scene
    assets_root_path = nucleus.get_assets_root_path()
    if assets_root_path is None:
        carb.log_error("Could not find Isaac Sim assets folder")
        with open(args.status_file, "w") as status_file:
            status_file.write("Could not find Isaac Sim assets folder.\n")
        simulation_app.close()
        sys.exit(1)

    scene_path = assets_root_path + args.scene
    result = add_reference_to_stage(usd_path=scene_path, prim_path="/World")
    if not result:
        with open(args.status_file, "w") as status_file:
            status_file.write("Could not find provided scene in Nucleus.\n")
        simulation_app.close()
        sys.exit(1)

    # Wait two frames so that stage starts loading
    simulation_app.update()
    simulation_app.update()

    print("Loading stage...")
    from omni.isaac.core.utils.stage import is_stage_loading

    while is_stage_loading():
        simulation_app.update()
    print("Loading Complete")

    # Start simulation context
    simulation_context = SimulationContext(
        physics_dt=1.0 / args.rate, rendering_dt=1.0 / args.rate, stage_units_in_meters=1.0
    )

    # Place or move robot in scene:
    if args.robot:
        prim_path = "/" + args.robot

        if args.robot == "carter_v2_3":
            robot_type = GxfRobotType.CARTER_V2_3
        elif args.robot == "carter_v2_4":
            robot_type = GxfRobotType.CARTER_V2_4
        else:
            carb.log_error(f"Incorrect robot_type provided: {args.robot}.")
            with open(args.status_file, "w") as status_file:
                status_file.write(f"Incorrect robot_type provided: {args.robot}.")
            simulation_app.close()
            sys.exit(1)

        if args.use_release_assets:
            asset_tier = AmrAssetTier.EXTERNAL_RELEASE
        else:
            asset_tier = AmrAssetTier.RELEASE_CANDIDATE

        translation = np.array(args.initial_pos + [0.0])
        orientation = rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(0, 0, 1), args.initial_yaw))
        # Add robot
        robot = GxfRobot(
            prim_path=prim_path,
            name=args.robot,
            robot_type=robot_type,
            asset_tier=asset_tier,
            translation=translation,
            orientation=orientation,
        )
        robot.set_tcp_server_params(address=args.tcp_server_addr, port=args.tcp_server_port)

    simulation_app.update()
    simulation_app.update()
    # Need to initialize physics getting any articulation..etc
    simulation_context.initialize_physics()
    simulation_context.play()

    if args.run_indefinitely:
        while simulation_app.is_running():
            simulation_app.update()
            time.sleep(0.01)
    else:
        frame = 0
        while frame < args.num_frames and simulation_app.is_running():
            simulation_app.update()
            time.sleep(0.01)
            frame = frame + 1

    simulation_context.stop()
    simulation_app.close()


if __name__ == "__main__":
    main()
