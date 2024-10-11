# Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
# Use this if you have to update a lot of changelogs with the same text.
# make sure to update the date, changelog_text, and extensions you want to update.
import fileinput
import re
import sys

date = "2023-01-06"
changelog_text = [f"### Fixed", f"- onclick_fn warning when creating UI"]

extensions = [
    "isaacsim.asset.conveyor",
    "isaacsim.robot_setup.gain_tuner",
    "isaacsim.robot_setup.xrdf_editor",
    "isaacsim.ros2.bridge",
    "isaacsim.sensors.camera",
    "isaacsim.sensors.physics",
    "isaacsim.sensors.physx",
    "isaacsim.sensors.rtx",
    "isaacsim.util.internal",
    "isaacsim.util.merge_mesh",
    "isaacsim.examples.ui",
    "isaacsim.examples.extension",
    "omni.isaac.articulation_inspector",
    "omni.isaac.assets_check",
    "isaacsim.examples.interactive",
    "omni.isaac.extension_templates",
    "omni.isaac.gain_tuner",
    "isaacsim.asset.generator.occupancy_map",
    "omni.isaac.physics_inspector",
    "isaacsim.util.physics",
    "omni.isaac.range_sensor",
    "omni.isaac.robot_benchmark",
    "omni.isaac.ros_bridge",
    "omni.isaac.sensor",
    "omni.isaac.synthetic_recorder",
    "isaacsim.core.utils",
]

# compute and replace the version number
add = [0, 0, 1]
ver = []
for ext in extensions:
    print(f"updating {ext}")
    for line in fileinput.input(f"../source/extensions/{ext}/config/extension.toml", inplace=True):
        if line[:7] == "version":
            ver = list(map(int, re.findall("\d+", line)))
            for i in [0, 1, 2]:
                ver[i] = ver[i] + add[i]
            print(f'version = "{ver[0]}.{ver[1]}.{ver[2]}"')
        else:
            print(line, end="")
    print(f"\t to version {ver}")

    found = False
    for line in fileinput.input(f"../source/extensions/{ext}/docs/CHANGELOG.md", inplace=True):
        if line[:11] == "# Changelog":
            print("# Changelog")
            print("")
            print(f"## [{ver[0]}.{ver[1]}.{ver[2]}] - {date}")
            for txt in changelog_text:
                print(txt)
            print("")
        else:
            if found:
                print(line, end="")
            else:
                if line[:3] == "## ":
                    found = True
                    print(line, end="")

    print("CHANGELOG.md updated.")
