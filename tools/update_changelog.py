# Use this if you have to update a lot of changelogs with the same text.
# make sure to update the date, changelog_text, and extensions you want to update.
import fileinput
import re
import sys

date = "2023-01-06"
changelog_text = [f"### Fixed", f"- onclick_fn warning when creating UI"]

extensions = [
    "omni.isaac.utils",
    "omni.isaac.urdf",
    "omni.isaac.unit_converter",
    "omni.isaac.ui_template",
    "omni.isaac.synthetic_recorder",
    "omni.isaac.shapenet",
    "omni.isaac.sensor",
    "omni.isaac.ros_bridge",
    "omni.isaac.ros2_bridge",
    "omni.isaac.robot_description_editor",
    "omni.isaac.robot_benchmark",
    "omni.isaac.range_sensor",
    "omni.isaac.physics_utilities",
    "omni.isaac.physics_inspector",
    "omni.isaac.partition",
    "omni.isaac.occupancy_map",
    "omni.isaac.merge_mesh",
    "omni.isaac.internal_tools",
    "omni.isaac.gxf_bridge",
    "omni.isaac.gain_tuner",
    "omni.isaac.extension_templates",
    "omni.isaac.examples",
    "omni.isaac.diff_usd",
    "omni.isaac.conveyor",
    "omni.isaac.assets_check",
    "omni.isaac.articulation_inspector",
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
