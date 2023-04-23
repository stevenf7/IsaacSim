# Copyright (c) 2020-2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import argparse
import carb
from omni.isaac.kit import SimulationApp
import os
import sys
import yaml
import numpy as np
from typing import List

GXF_BRIDGE_EXTENSION_NAME = "omni.isaac.gxf_bridge"

DEFAULT_ATLAS_YAML = "default_atlas.yaml"
DEFAULT_CLOCK_YAML = "default_clock.yaml"
DEFAULT_ALLOCATOR_YAML = "isaac_sim_allocator.yaml"

ROBOT_ASSET_PATHS = {"carter_v2_3": "/Projects/isaac_amr_envoy/GXF/Robots/carter_v2_3_gxf.usd"}
ROBOT_PRIM_PATHS = {"carter_v2_3": "/carter_v2_3"}


def set_yaml_addr_port(yaml: List[dict], address: str, port: int) -> bool:
    """Sets TCP server port & address in provided YAML documents.

    Args:
        yaml(List[dict]): List of dictionaries representing YAML documents.
        address (str): address to set server to.
        port (str): port to set server to.

    Returns:
        bool: True if successful; False otherwise.
    """
    for entity in yaml:
        if entity is None:
            continue
        for component in entity["components"]:
            if component["type"] == "nvidia::gxf::TcpServer":
                component["parameters"]["address"] = address
                component["parameters"]["port"] = port
                return True
    return False


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        "Play scene with GXF application.", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--headless", action="store_false", help="Run sim in headless mode.")
    parser.add_argument("-r", "--rate", type=int, default=60, help="Frame rate (Hz)")
    parser.add_argument("-n", "--num_frames", type=int, default=60, help="Number of frames to run simulation for.")
    parser.add_argument("--use_default_atlas", action="store_true", help="Use default atlas entity/component.")
    parser.add_argument(
        "--use_default_clock", action="store_true", help="Use default scheduler entity/clock component."
    )
    parser.add_argument(
        "--tcp_server_addr",
        default="127.0.0.1",
        help="TCP server address - for scenes creating GXF app from OmniGraph.",
    )
    parser.add_argument(
        "--tcp_server_port",
        type=int,
        default=7000,
        help="TCP server port - for scenes creating GXF app from OmniGraph.",
    )
    parser.add_argument(
        "--robot", choices=ROBOT_ASSET_PATHS.keys(), default=None, help="Type of robot to place or move in scene"
    )
    parser.add_argument(
        "--initial_pos",
        type=float,
        nargs=2,
        default=[0.0, 0.0],
        help="Initial (x, y) position of robot in world coordinates.",
    )
    parser.add_argument(
        "--initial_yaw", type=float, default=0.0, help="Initial yaw position of robot in world coordinates (degrees)."
    )

    parser.add_argument("scene", type=str, help="Path to scene in Nucleus server")
    parser.add_argument("yaml_path", type=str, nargs="*", help="Path to GXF app YAML file.")

    args, unknown_args = parser.parse_known_args()

    # Create simulation application
    simulation_app = SimulationApp({"renderer": "RayTracedLighting", "headless": args.headless})

    import omni
    import omni.kit.commands
    from omni.isaac.core import SimulationContext
    from omni.isaac.core.prims import XFormPrim
    from omni.isaac.core.utils import extensions, prims, rotations, nucleus
    from omni.isaac.core.utils.stage import add_reference_to_stage, traverse_stage
    from pxr import Gf

    # Enable GXF bridge extension
    extensions.enable_extension(GXF_BRIDGE_EXTENSION_NAME)

    # Open the specified USD scene
    assets_root_path = nucleus.get_assets_root_path()
    if assets_root_path is None:
        carb.log_error("Could not find Isaac Sim assets folder")
        simulation_app.close()
        sys.exit(1)

    omni.usd.get_context().open_stage(assets_root_path + args.scene, None)

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
    script_path = os.path.join(package_path, "standalone_examples", "testing", GXF_BRIDGE_EXTENSION_NAME)

    if not args.yaml_path:
        # Iterate over prims in the stage to see if a GXF YAML node is present
        gxf_yaml_node_present = False
        for stage_prim in traverse_stage():
            if stage_prim.HasAttribute("node:type"):
                type_attr = stage_prim.GetAttribute("node:type")
                value = type_attr.Get()
                if "omni.isaac.gxf_bridge.GXFYAML" in value:
                    gxf_yaml_node_present = True
                    graph = yaml.safe_load_all(stage_prim.GetAttribute("inputs:yaml").Get())
                    if set_yaml_addr_port(graph, args.tcp_server_addr, args.tcp_server_port):
                        stage_prim.GetAttribute("inputs:yaml").Get()
                        carb.log_info(
                            f"Set TcpServer component address to {args.tcp_server_addr}, port to {args.tcp_server_port}."
                        )
                    stage_prim.GetAttribute("inputs:yaml").Set(yaml.dump_all(graph))
                    break
        if not gxf_yaml_node_present:
            carb.log_error("No GXF graph YAMLs provided as arguments, and no GXF YAML node found in loaded scene.")
            carb.log_error("Failed to create GXF application, exiting.")
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
            simulation_app.close()
            sys.exit(1)

    # Place or move robot in scene:
    if args.robot:
        robot_asset_path = ROBOT_ASSET_PATHS[args.robot]
        robot_prim_path = ROBOT_PRIM_PATHS[args.robot]
        if not prims.get_prim_at_path(robot_prim_path):
            # Create the robot in the scene
            add_reference_to_stage(usd_path=f"{assets_root_path}{robot_asset_path}", prim_path=robot_prim_path)
        # move the robot
        _ = XFormPrim(
            prim_path=robot_prim_path,
            translation=np.array(args.initial_pos + [0.0]),
            orientation=rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(0, 0, 1), args.initial_yaw)),
        )

    # Need to initialize physics getting any articulation..etc
    simulation_context.initialize_physics()

    # Run for specified number of frames
    frame = 0
    while frame < args.num_frames and simulation_app.is_running():
        simulation_context.step(render=True)
        frame = frame + 1

    # Bring down the GXF application and close the simulation
    if args.yaml_path:
        result, status = omni.kit.commands.execute("RobotEngineBridgeGxfDestroyApplication")

    simulation_app.close()


if __name__ == "__main__":
    main()
