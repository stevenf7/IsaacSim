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

GXF_BRIDGE_EXTENSION_NAME = "omni.isaac.gxf_bridge"

DEFAULT_ATLAS_YAML = "default_atlas.yaml"
DEFAULT_CLOCK_YAML = "default_clock.yaml"
DEFAULT_ALLOCATOR_YAML = "isaac_sim_allocator.yaml"

# Parse command-line arguments
parser = argparse.ArgumentParser(
    "Play scene with GXF application.", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("--headless", action="store_false", help="Run sim in headless mode.")
parser.add_argument("-r", "--rate", type=int, default=60, help="Frame rate (Hz)")
parser.add_argument("-n", "--num_frames", type=int, default=60, help="Number of frames to run simulation for.")
parser.add_argument("--use_default_atlas", action="store_true", help="Use default atlas entity/component.")
parser.add_argument("--use_default_clock", action="store_true", help="Use default scheduler entity/clock component.")

parser.add_argument("scene", type=str, help="Path to scene in Nucleus server")
parser.add_argument("yaml_path", type=str, nargs="*", help="Path to GXF app YAML file.")

args, unknown_args = parser.parse_known_args()

# Create simulation application
simulation_app = SimulationApp({"renderer": "RayTracedLighting", "headless": args.headless})

import omni
import omni.kit.commands
from omni.isaac.core import SimulationContext
from omni.isaac.core.utils import extensions, nucleus

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
    print("No GXF graph YAMLs provided. Assuming any graphs are provided directly in USD via YAML node(s).")
else:
    # Assemble list of GXF app YAMLs
    gxf_app_yaml_paths = []
    if args.use_default_atlas:
        gxf_app_yaml_paths.append(os.path.join(script_path, DEFAULT_ATLAS_YAML))
    if args.use_default_clock:
        gxf_app_yaml_paths.append(os.path.join(script_path, DEFAULT_CLOCK_YAML))
    for path in args.yaml_path:
        gxf_app_yaml_paths.append(path)
    gxf_app_yaml_paths.append(os.path.join(gxf_app_config_path, DEFAULT_ALLOCATOR_YAML))

    # Create GXF application
    result, status = omni.kit.commands.execute(
        "RobotEngineBridgeGxfCreateApplication",
        base_path=gxf_extension_lib,
        manifest_file="manifest.yaml",
        graph_files=gxf_app_yaml_paths,
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
