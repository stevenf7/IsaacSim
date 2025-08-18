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
import os
import sys
from collections import defaultdict
from pathlib import Path

import carb
import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.utils.stage as stage_utils
import omni.usd
from isaacsim.core.experimental.prims import Articulation
from isaacsim.core.utils.prims import get_prim_at_path
from isaacsim.storage.native import find_files_recursive, get_assets_root_path
from jinja2 import Environment, FileSystemLoader
from pxr import PhysxSchema, Usd, UsdPhysics
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
    parser.add_argument(
        "--version",
        "-v",
        type=str,
        required=True,
        help="Version of Isaac Sim to use for the RST documentation",
    )

    args, _ = parser.parse_known_args()
    return args


def main():
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

    # includes both capital and lowercase in case of files that are only different in capitalization
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
        "_sensors_merged",
        "/nova_carter_dev_kit",
        "/nova_dev_kit",
        "/payloads",
        "/HighResProps",
    ]
    useful_data = {}
    additional_info = {}
    physics_apis = {}
    has_ros = {}
    accessory_list = {}

    no_data_bots = []

    for asset_path in paths:
        # check all intended assets
        if asset_path.endswith(".usd") and not any(exclude_path in asset_path for exclude_path in exclude_paths):
            stage_utils.open_stage(asset_path)

            # find the root of the prim on the stage
            for prim in stage_utils.traverse_stage():
                stage_path = prim.GetPath()
                break
            object_prim = get_prim_at_path(stage_path)

            # make sure prim is valid
            if object_prim and object_prim.IsValid():
                robot_official_name = asset_path.split("/")[6]
                truncated_path = asset_path.split("/", 5)[-1]

                if truncated_path not in additional_info:
                    additional_info[truncated_path] = defaultdict(int)

                physics_apis[truncated_path] = get_all_physics_apis(object_prim)

                # find sensors
                articulation_roots = []
                joint_count = 0
                for children in stage_utils.traverse_stage():
                    if children.HasAPI(UsdPhysics.ArticulationRootAPI):
                        articulation_roots.append(children.GetPath())
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
                    elif "Joint" in prim_type:
                        joint_count += 1

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

                joints_links_dofs = []
                if len(articulation_roots) > 0:
                    for articulation_root in articulation_roots:

                        temp_joints_links_dofs = []
                        articulation = Articulation(str(articulation_root))

                        try:

                            temp_joints_links_dofs.append(articulation.num_joints)

                        except:
                            temp_joints_links_dofs.append("N/A")
                        try:
                            temp_joints_links_dofs.append(articulation.num_links)

                        except:
                            temp_joints_links_dofs.append("N/A")
                        try:
                            temp_joints_links_dofs.append(articulation.num_dofs)

                        except:
                            temp_joints_links_dofs.append("N/A")
                        joints_links_dofs.append(temp_joints_links_dofs)

                    joints = 0
                    links = 0
                    dofs = 0

                    for root in joints_links_dofs:
                        if root[0] != "N/A":
                            joints += root[0]
                        if root[1] != "N/A":
                            links += root[1]

                        if root[2] != "N/A":
                            dofs += root[2]

                    if any(root[0] == joint_count for root in joints_links_dofs):
                        # Find the root that matches
                        for root in joints_links_dofs:
                            if root[0] == joint_count:
                                data["num_joints"] = root[0]
                                data["num_links"] = root[1]
                                data["num_dofs"] = root[2]
                                break
                    else:
                        data["num_joints"] = joints
                        data["num_links"] = links
                        data["num_dofs"] = dofs
                else:
                    data["num_joints"] = "N/A"
                    data["num_links"] = "N/A"
                    data["num_dofs"] = "N/A"
                    no_data_bots.append(truncated_path)

                # Basic info
                robot_company = asset_path.split("/")[5]  # may be different if not my local path
                robot_type = data["isaac:robotType"]
                # Store attributes in useful_data
                useful_data[truncated_path] = {**data}
                robot_new_path = asset_path.split(".usd")[0] + ".usd"

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

            else:
                print(f"Invalid prim at {asset_path}")

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    isaac_lab_bots_path = os.path.join(script_dir, "isaac_lab_bots.txt")

    with open(isaac_lab_bots_path, "r") as f:
        isaac_lab_robot_names = f.read().split("\n")

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(script_dir), autoescape=True)
    template = env.get_template("robot_rst_template.jinja")

    # Prepare template context
    context = {
        "robot_categorization": robot_categorization,
        "useful_data": useful_data,
        "additional_info": additional_info,
        "accessory_list": accessory_list,
        "physics_apis": physics_apis,
        "isaac_lab_robot_names": isaac_lab_robot_names,
        "ros_bots": ros_bots,
        "version": args.version,
    }

    # Render template and write to file
    with open(args.rst, "w") as f:
        f.write(template.render(**context))

    print(f"RST documentation generated successfully at {args.rst}\n\n")

    print("\n\n")
    print("The following robots have no data on the number of joints, links, or DOFs:\n\n")
    print(no_data_bots)
    print(f"Total number of robots with no data: {len(no_data_bots)}\n\n")


if __name__ == "__main__":
    main()

    simulation_app.close()
