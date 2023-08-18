# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import argparse
import os
import sys
import time

import carb
import numpy as np
import yaml
from isaac_amr import *
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
        "--robot", choices=ROBOT_ASSET_PATHS.keys(), default=None, help="Type of robot to place or move in scene"
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

    import omni
    import omni.kit.commands
    from omni.isaac.core import SimulationContext
    from omni.isaac.core.prims import XFormPrim
    from omni.isaac.core.utils import extensions, nucleus, prims, rotations
    from omni.isaac.core.utils.stage import add_reference_to_stage, traverse_stage
    from pxr import Gf

    # Enable GXF bridge extension
    extensions.enable_extension(GXF_BRIDGE_EXTENSION_NAME)

    # Open the specified USD scene
    assets_root_path = nucleus.get_assets_root_path()
    if assets_root_path is None:
        carb.log_error("Could not find Isaac Sim assets folder")
        with open(args.status_file, "w") as status_file:
            status_file.write("Could not find Isaac Sim assets folder.\n")
        simulation_app.close()
        sys.exit(1)

    result = omni.usd.get_context().open_stage(assets_root_path + args.scene, None)
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

    # Get path to GXF bridge extension
    ext_manager = omni.kit.app.get_app().get_extension_manager()
    ext_id = ext_manager.get_enabled_extension_id(GXF_BRIDGE_EXTENSION_NAME)
    gxf_extension_path = ext_manager.get_extension_path(ext_id)
    gxf_extension_lib = os.path.join(gxf_extension_path, "lib")
    gxf_app_config_path = os.path.join(gxf_extension_path, "data", "config")

    # Get path to directory containing this script
    app_folder = carb.tokens.get_tokens_interface().resolve("${app}/../")
    package_path = os.path.abspath(app_folder)
    script_path = os.path.join(package_path, "tools", "isaac_amr")

    # Place or move robot in scene:
    if args.robot:
        robot_prim_path = ROBOT_PRIM_PATHS[args.robot]
        if args.use_release_assets:
            robot_asset_path = ROBOT_ASSET_PATHS[args.robot]
        else:
            robot_asset_path = ROBOT_ASSET_PATHS_RELEASE_CANDIDATE[args.robot]
        if not prims.get_prim_at_path(robot_prim_path):
            # Create the robot in the scene
            add_reference_to_stage(usd_path=f"{assets_root_path}{robot_asset_path}", prim_path=robot_prim_path)
        # move the robot
        _ = XFormPrim(
            prim_path=robot_prim_path,
            translation=np.array(args.initial_pos + [0.0]),
            orientation=rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(0, 0, 1), args.initial_yaw)),
        )

    if not args.yaml_path:
        # Iterate over prims in the stage to see if a GXF YAML node is present
        gxf_yaml_node_present = False
        for stage_prim in traverse_stage():
            if stage_prim.HasAttribute("node:type"):
                type_attr = stage_prim.GetAttribute("node:type")
                value = type_attr.Get()
                if "omni.isaac.gxf_bridge.GXFYAML" in value:
                    gxf_yaml_node_present = True
                    graph = list(yaml.safe_load_all(stage_prim.GetAttribute("inputs:yaml").Get()))
                    if set_yaml_addr_port(graph, args.tcp_server_addr, args.tcp_server_port):
                        stage_prim.GetAttribute("inputs:yaml").Get()
                        carb.log_info(
                            f"Set TcpServer component address to {args.tcp_server_addr}, port to {args.tcp_server_port}."
                        )
                    stage_prim.GetAttribute("inputs:yaml").Set(yaml.dump_all(graph))
                    if not os.path.exists("tmp"):
                        os.mkdir("tmp")
                    combined_yaml_path = os.path.join("tmp", "combined_graph.yaml")
                    with open(combined_yaml_path, "w") as cgy:
                        cgy.write(yaml.dump_all(graph))
                    break
        if not gxf_yaml_node_present:
            carb.log_error("No GXF graph YAMLs provided as arguments, and no GXF YAML node found in loaded scene.")
            with open(args.status_file, "w") as status_file:
                status_file.write(
                    "No GXF graph YAMLs provided as arguments, and no GXF YAML node found in loaded scene.\n"
                )
            simulation_app.close()
            sys.exit(1)
    else:
        # Assemble list of GXF app YAMLs
        gxf_app_yaml_paths = []
        if args.use_default_atlas:
            gxf_app_yaml_paths.append(os.path.join(script_path, DEFAULT_ATLAS_YAML))
        if args.use_default_clock:
            gxf_app_yaml_paths.append(os.path.join(script_path, DEFAULT_CLOCK_YAML))
        gxf_app_yaml_paths.extend(args.yaml_path)
        gxf_app_yaml_paths.append(os.path.join(gxf_app_config_path, DEFAULT_ALLOCATOR_YAML))

        # Combine YAMLs into a single graph
        combined_yaml = []
        for yaml_path in gxf_app_yaml_paths:
            with open(yaml_path, "r") as yp:
                combined_yaml.extend(yaml.safe_load_all(yp))

        # Update TCP server port and address
        if set_yaml_addr_port(combined_yaml, args.tcp_server_addr, args.tcp_server_port):
            carb.log_info(f"Set TcpServer component address to {args.tcp_server_addr}, port to {args.tcp_server_port}.")

        # Write combined & updated YAML into a single file
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        combined_yaml_path = os.path.join("tmp", "combined_graph.yaml")
        with open(combined_yaml_path, "w") as cgy:
            cgy.write(yaml.safe_dump_all(combined_yaml))

        # Create GXF application
        result, status = omni.kit.commands.execute(
            "RobotEngineBridgeGxfCreateApplication",
            base_path=gxf_extension_lib,
            manifest_file="manifest.yaml",
            graph_files=[combined_yaml_path],
        )

        if not status:
            carb.log_error("Failed to create GXF application, exiting.")
            with open(args.status_file, "w") as status_file:
                status_file.write("Failed to create GXF application, exiting.\n")
            simulation_app.close()
            sys.exit(1)

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

    # Bring down the GXF application and close the simulation
    if args.yaml_path:
        result, status = omni.kit.commands.execute("RobotEngineBridgeGxfDestroyApplication")

    simulation_app.close()


if __name__ == "__main__":
    main()
