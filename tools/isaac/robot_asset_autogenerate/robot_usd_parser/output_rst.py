# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import carb
import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.utils.stage as stage_utils
import numpy as np
import omni
import omni.usd
from isaacsim.core.api import World
from isaacsim.core.api.robots import Robot
from isaacsim.core.experimental.prims import Articulation, XformPrim
from isaacsim.core.utils.prims import get_prim_at_path
from isaacsim.core.utils.stage import add_reference_to_stage, get_stage_units
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.storage.native import (
    find_files_recursive,
    get_assets_root_path,
    get_stage_references,
    is_absolute_path,
    is_path_external,
    is_valid_usd_file,
)
from pxr import Gf, PhysxSchema, Sdf, Usd, UsdGeom, UsdPhysics
from usd.schema.isaac import robot_schema


# update as more physics backends are added
def get_all_physics_apis(prim):
    """Get a list of all physics APIs applied to a prim."""
    physics_apis = [
        # (UsdPhysics.ArticulationRootAPI, "USD ArticulationRootAPI"),
        # (UsdPhysics.RigidBodyAPI, "USD RigidBodyAPI"),
        # (UsdPhysics.CollisionAPI, "USD CollisionAPI"),
        # (UsdPhysics.MeshCollisionAPI, "USD MeshCollisionAPI"),
        # (UsdPhysics.DriveAPI, "USD DriveAPI"),
        # (UsdPhysics.MassAPI, "USD MassAPI"),
        # (UsdPhysics.LimitAPI, "USD LimitAPI"),
        (PhysxSchema.PhysxArticulationAPI, "PhysX ArticulationAPI"),
        (PhysxSchema.PhysxRigidBodyAPI, "PhysX RigidBodyAPI"),
        (PhysxSchema.PhysxCollisionAPI, "PhysX CollisionAPI"),
        (PhysxSchema.PhysxSceneAPI, "PhysX SceneAPI"),
        (PhysxSchema.PhysxMimicJointAPI, "PhysX MimicJointAPI"),
        (PhysxSchema.PhysxJointAPI, "PhysX JointAPI"),
        (PhysxSchema.PhysxResidualReportingAPI, "PhysX ResidualReportingAPI"),
        (PhysxSchema.PhysxAutoParticleClothAPI, "PhysX AutoParticleClothAPI"),
        (PhysxSchema.PhysxParticleClothAPI, "PhysX ParticleClothAPI"),
    ]

    applied_apis = []
    for api, name in physics_apis:
        if prim.HasAPI(api):
            applied_apis.append(name)

    return applied_apis


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Process robot types and generate RST documentation.")

    parser.add_argument(
        "--rst",
        "-r",
        type=str,
        required=False,
        default="./tools/isaac/robot_asset_autogenerate/outputs/usd_assets_robots.rst",
        help="Path where the RST output file should be saved",
    )

    parser.add_argument(
        "--list",
        "-l",
        type=str,
        required=False,
        default="./tools/isaac/robot_asset_autogenerate/outputs/robot_list.csv",
        help="Path of the list of robot names (as a csv file) to parse",
    )

    args, _ = parser.parse_known_args()
    return args


# Parse command line arguments
args = parse_args()


# get list of robots that use ROS2
root = get_assets_root_path()
ros_paths = find_files_recursive(
    [carb.settings.get_settings().get("/persistent/isaac/asset_root/default") + "/Isaac/Samples/ROS2/Robots/"]
)

ros_bots = []
for file in ros_paths:
    if file.endswith(".usd") and "/.thumbs" not in file:
        ros_bots.append(file.split(".")[0].split("_ROS")[0])


robot_categorization = {}


paths = []


try:
    with open(args.list, "r", newline="") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row and row[0].endswith(".usd"):  # Only process USD files
                paths.append(row[0])
    print(f"Successfully loaded {len(paths)} paths")
except FileNotFoundError:
    print(f"Error: CSV file not found")
    sys.exit(1)
except Exception as e:
    print(f"Error reading CSV file: {e}")
    sys.exit(1)


exclude_paths = [
    "/.thumbs",
    "/parts",
    "/Parts",
    "/Materials",
    "/materials",
    "/Legacy",
    "/legacy",
    "/Props",
    "/props",
    "/DetailedProps",
    "/detailedprops",
    "/Config",
    "/config",
    "/Configuration",
    "/configuration",
    "/Grippers",
    "/grippers",
    "/Variants",
    "/variants",
    "/Physics",
    "/physics",
    "/Sensors_merged",
    "/sensors_merged",
    "/Sensors_merged_stage",
    "_sensors_merged" "/nova_carter_dev_kit",
    "/nova_dev_kit",
    "/HighResProps",
]
useful_data = {}
additional_info = {}
physics_apis = {}
has_ros = {}
accessory_list = {}
for asset_path in paths:
    # check all intended assets

    # Extract robot name from path for comparison

    if asset_path.endswith(".usd") and not any(exclude_path in asset_path for exclude_path in exclude_paths):

        stage_utils.open_stage(asset_path)

        # find the root of the prim on the stage
        for prim in stage_utils.traverse_stage():
            stage_path = prim.GetPath()
            break
        object_prim = get_prim_at_path(stage_path)

        # make sure prim is valid
        if object_prim and object_prim.IsValid():  # and not any(map(bot.__contains__, exclude_paths)):

            robot_official_name = asset_path.split("/")[6]
            truncated_path = asset_path.split("/", 5)[-1]

            if truncated_path not in additional_info:
                additional_info[truncated_path] = defaultdict(int)

            physics_apis[truncated_path] = get_all_physics_apis(object_prim)

            # find sensors
            for children in stage_utils.traverse_stage():

                prim_type = children.GetTypeName()
                if prim_type == "OmniLidar":
                    additional_info[truncated_path]["OmniSensor Lidar"] += 1
                elif prim_type == "OmniDepthSensor":
                    additional_info[truncated_path]["OmniSensor Depth"] += 1
                elif prim_type == "OmniCamera":
                    additional_info[truncated_path]["OmniSensor Camera"] += 1
                elif prim_type == "OmniIMU":
                    additional_info[truncated_path]["OmniSensor IMU"] += 1
                elif prim_type == "IsaacImuSensor":
                    additional_info[truncated_path]["IMU"] += 1
                elif prim_type == "IsaacForceSensor":
                    additional_info[truncated_path]["Force Sensor"] += 1
                elif prim_type == "IsaacTorqueSensor":
                    additional_info[truncated_path]["Torque Sensor"] += 1
                elif prim_type == "IsaacContactSensor":
                    additional_info[truncated_path]["Contact Sensor"] += 1
                elif prim_type == "Camera":
                    additional_info[truncated_path]["Camera"] += 1

            variants = prim_utils.get_prim_variant_collection(str(stage_path))

            accessories_list = ["Variant_Set", "Gripper", "gripper", "Hands"]
            for accessories in accessories_list:
                if accessories in variants:
                    temp_list = []
                    for accessory in variants[accessories]:
                        if accessory != "None":
                            temp_list.append(accessory)
                    accessory_list[truncated_path] = temp_list

            articulation = Articulation(str(object_prim.GetPath()))

            data = {}
            for attr_name in ["num_joints", "num_links"]:
                try:
                    attr = object_prim.GetAttribute(attr_name)
                    if attr:
                        data[attr_name] = attr.Get()
                # Empty if it doesn't exist
                except:
                    data[attr_name] = ""

            # Get robot description using IsaacRobotAPI
            description = ""
            try:
                # Check if the prim has the IsaacRobotAPI applied
                if object_prim.HasAPI(robot_schema.Classes.ROBOT_API.value):
                    # Get the description attribute from the API
                    for attr_name in [
                        "isaac:description",
                        "isaac:robotType",
                        "isaac:license",
                        "isaac:version",
                        "isaac:source",
                    ]:
                        attr = object_prim.GetAttribute(attr_name)
                        if attr:
                            if attr.Get() == "":
                                data[attr_name] = "N/A"
                            else:
                                data[attr_name] = attr.Get()
                        else:
                            data[attr_name] = "N/A"

                else:
                    print("IsaacRobotAPI not applied to this prim: ", asset_path)
                    data["isaac:description"] = "N/A"
                    data["isaac:robotType"] = "No Robot Schema Applied"
                    data["isaac:license"] = "N/A"
                    data["isaac:version"] = "N/A"
                    data["isaac:source"] = "N/A"
            except Exception as e:
                print(f"Error getting description: {e}")

            has_articulation = object_prim.HasAPI(UsdPhysics.ArticulationRootAPI)
            if has_articulation:
                articulation = Articulation(str(object_prim.GetPath()))

                try:
                    data["num_joints"] = articulation.num_joints
                except:
                    data["num_joints"] = "N/A"
                try:
                    data["num_links"] = articulation.num_links
                except:
                    data["num_links"] = "N/A"
                try:
                    data["num_dofs"] = articulation.num_dofs
                except:
                    data["num_dofs"] = "N/A"
            else:
                data["num_joints"] = "N/A"
                data["num_links"] = "N/A"
                data["num_dofs"] = "N/A"

            # Basic info
            robot_company = asset_path.split("/")[5]  # may be different if not my local path
            # robot_official_name = asset_path.split("/")[-2]
            robot_type = data["isaac:robotType"]
            # Store attributes in useful_data
            useful_data[truncated_path] = {**data}  # , **attributes
            robot_new_path = asset_path.split(".usd")[0] + ".usd"  # + "_stage.usd"

            robot_new_name = robot_new_path

            if truncated_path not in additional_info:
                additional_info[truncated_path] = defaultdict(int)

            # No need to save the stage since we're only reading
            stage_utils.clear_stage()

            robot_new_name = robot_new_path.split("/")[-1].split(".")[0]

            # once again, may be different if not my local path. Should be like this: /Robots/UniversalRobots/ur10e/ur10e.usd

            truncated_path = asset_path.split("/", 5)[-1]

            # categorize the robot: outermost layer is robot type, then further categorized by company, which stores a list of robots of that company and type
            if robot_type not in robot_categorization:
                robot_categorization[robot_type] = {
                    robot_company: [(robot_new_name, truncated_path, robot_official_name)]
                }
            else:
                if robot_company not in robot_categorization[robot_type]:
                    robot_categorization[robot_type][robot_company] = [
                        (robot_new_name, truncated_path, robot_official_name)
                    ]
                else:
                    robot_categorization[robot_type][robot_company].append(
                        (robot_new_name, truncated_path, robot_official_name)
                    )

                # Remove any existing robots whose names contain the current robot name (they are variants)

        else:
            print(f"Invalid prim at {asset_path}")


# Write RST documentation

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
isaac_lab_bots_path = os.path.join(script_dir, "isaac_lab_bots.txt")

with open(isaac_lab_bots_path, "r") as f:
    isaac_lab_robot_names = f.read().split("\n")


with open(args.rst, "w") as f:
    f.write("..\n")
    f.write("   Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.\n")
    f.write("   NVIDIA CORPORATION and its licensors retain all intellectual property\n")
    f.write("   and proprietary rights in and to this software, related documentation\n")
    f.write("   and any modifications thereto. Any use, reproduction, disclosure or\n")
    f.write("   distribution of this software and related documentation without an express\n")
    f.write("   license agreement from NVIDIA CORPORATION is strictly prohibited.\n")
    f.write("\n\n\n")
    f.write(".. _isaac_assets_robots:\n\n")
    f.write("================================\n")
    f.write("Robot Assets\n")
    f.write("================================\n")
    f.write("\n")
    f.write("|isaac-sim| supports a wide range of robots with differential bases, form factors, and functions.\n")
    f.write("\n")
    f.write(
        "These robots can be categorized as wheeled robots, holonomic robots, quadruped robots, robotic manipulator and aerial robots (drones). They can be found in the Content Browser in the ``Isaac Sim/Robots`` folder.\n\n\n"
    )

    f.write(".. tab-set::\n")
    # categorize by robot type
    for robot_type, value in robot_categorization.items():

        written_robot_names = []

        f.write(f"    .. tab-item:: {robot_type}\n\n")

        # categorize by company
        for robot_company, robot_names in value.items():
            f.write(f"        **{robot_company}**\n\n")
            # write info for each robot
            for robot_name, truncated_path, robot_official_name in robot_names:

                image_path = truncated_path.replace("/", "_").replace(" ", "_").replace("-", "_").replace(".", "_")

                if robot_official_name not in written_robot_names:
                    written_robot_names.append(robot_official_name)
                    f.write(f"          - Robot: {robot_official_name}\n\n")
                    f.write(f"              .. tab-set::\n")

                tab = "          "

                f.write(f"                  .. tab-item:: {truncated_path}\n\n")

                # Create the filename safely
                thumbnail_filename = truncated_path.replace("/", "_").replace(" ", "_").replace("-", "_").split(".")[0]
                f.write(
                    f"{tab}            .. figure:: /images/usd_assets_robots/isim_5.1_full_ref_viewport_Isaac_Robots_{thumbnail_filename}.usd.png\n"
                )

                f.write(f"{tab}              :align: center\n")
                f.write(f"{tab}              :alt: {robot_official_name} Robot\n")
                f.write(f"{tab}              :width: 100%\n\n")

                f.write(f"{tab}            .. list-table::\n")
                f.write(f"{tab}                :align: center\n")
                f.write(f"{tab}                :widths: 40 40\n\n")

                f.write(f"{tab}                * - Description\n")
                f.write(f'{tab}                  - {useful_data[truncated_path]["isaac:description"]}\n')

                f.write(f"{tab}                * - License\n")
                f.write(f'{tab}                  - {useful_data[truncated_path]["isaac:license"]}\n')
                f.write(f"{tab}                * - Version\n")
                f.write(f'{tab}                  - {useful_data[truncated_path]["isaac:version"]}\n')
                f.write(f"{tab}                * - Source\n")
                f.write(f'{tab}                  - {useful_data[truncated_path]["isaac:source"]}\n')
                f.write(f"{tab}                * - Number of Joints\n")
                f.write(f'{tab}                  - {useful_data[truncated_path]["num_joints"]}\n')
                f.write(f"{tab}                * - Number of Links\n")
                f.write(f'{tab}                  - {useful_data[truncated_path]["num_links"]}\n')
                f.write(f"{tab}                * - Number of DOFs\n")
                f.write(f'{tab}                  - {useful_data[truncated_path]["num_dofs"]}\n\n')

                if truncated_path in additional_info:
                    if len(additional_info[truncated_path]) > 1:
                        f.write(f"{tab}            .. list-table::\n")
                        f.write(f"{tab}                :align: center\n")
                        f.write(f"{tab}                :widths: 40 40\n")
                        f.write(f"{tab}                :header-rows: 1\n\n")
                        f.write(f"{tab}                * - Sensor/Accessory\n")
                        f.write(f"{tab}                  - Count\n")
                        for item in additional_info[truncated_path]:
                            if item != "Camera":
                                f.write(f"{tab}                * - {item}\n")
                                f.write(f"{tab}                  - {additional_info[truncated_path][item]}\n\n")
                            elif additional_info[truncated_path][item] > 4:
                                f.write(f"{tab}                * - {item}\n")
                                f.write(f"{tab}                  - {additional_info[truncated_path][item]-4}\n\n")
                    elif len(additional_info[truncated_path]) == 1 and additional_info[truncated_path]["Camera"] > 4:
                        f.write(f"{tab}            .. list-table::\n")
                        f.write(f"{tab}                :align: center\n")
                        f.write(f"{tab}                :widths: 40 40\n")
                        f.write(f"{tab}                :header-rows: 1\n\n")
                        f.write(f"{tab}                * - Sensors\n")
                        f.write(f"{tab}                  - Count\n")
                        f.write(f"{tab}                * - Camera\n")
                        f.write(f'{tab}                  - {additional_info[truncated_path]["Camera"]-4}\n\n\n')
                if truncated_path in accessory_list:
                    if len(accessory_list[truncated_path]) > 1:

                        f.write(f"{tab}            * Accessories\n")
                        for accessory in accessory_list[truncated_path]:
                            f.write(f"{tab}                - {accessory}\n\n")

                if len(physics_apis[truncated_path]) > 0:
                    f.write(f"{tab}            * Physics APIs:\n")
                    for api in physics_apis[truncated_path]:
                        f.write(f"{tab}                - {api}\n\n")

                if truncated_path.split("/")[-1] in isaac_lab_robot_names:
                    f.write(f"{tab}            * This robot is in Isaac Lab\n\n ")

                if truncated_path.split("/")[-1].split(".")[0] in ros_bots:
                    f.write(f"{tab}            * This robot uses ROS2\n\n")

                f.write("\n\n\n")

    f.close()


simulation_app.close()
