from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import argparse
import csv
import os
import sys
from pathlib import Path

import carb
import omni
import omni.usd
from isaacsim.core.api import World
from isaacsim.core.utils.prims import get_prim_at_path
from omni.isaac.nucleus import get_assets_root_path
from pxr import UsdGeom

# list of 29 pertinent categories to include in csv files
attr_list = [
    "name",
    "focalLength",
    "focusDistance",
    "fStop",
    "projection",
    "stereoRole",
    "horizontalAperture",
    "verticalAperture",
    "clippingRange",
    "cameraProjectionType",
    "nominalWidth",
    "nominalHeight",
    "opticalCenterX",
    "opticalCenterY",
    "maxFOV",
    "polyK0",
    "polyK1",
    "polyK2",
    "polyK3",
    "polyK4",
    "polyK5",
    "p0",
    "p1",
    "s0",
    "s1",
    "s2",
    "s3",
    "physicalDistortionCoefficients",
    "physicalDistortionModel",
]

# default values if parse returns None for value
default_values = {
    "cameraProjectionType": "pinhole",
    "nominalWidth": 1936.0,
    "nominalHeight": 1216.0,
    "opticalCenterX": 970.94244,
    "opticalCenterY": 600.37482,
    "maxFOV": 200.0,
    "polyK0": 0.0,
    "polyK1": 0.00245,
    "polyK2": 0.0,
    "polyK3": 0.0,
    "polyK4": 0.0,
    "polyK5": 0.0,
    "p0": -0.00037,
    "p1": -0.00074,
    "s0": -0.00058,
    "s1": -0.00022,
    "s2": 0.00019,
    "s3": -0.0002,
}

parser = argparse.ArgumentParser()
parser.add_argument("--usd", default=None, help="Path to USD")
args, unknown = parser.parse_known_args()

# check that path argument starts with omniverse dir
if args.usd is not None:
    env_path = args.usd
    print(f"Loading environment: {env_path}")
    omni.usd.get_context().open_stage(env_path)

file_name = os.path.splitext(os.path.basename(args.usd))
camera_prim_paths = []

# find all camera prim paths
stage = omni.usd.get_context().get_stage()
for prim in stage.Traverse():
    if prim.IsA(UsdGeom.Camera) and "OmniverseKit" not in str(prim.GetPath()):
        camera_prim_paths.append(str(prim.GetPath()))

# create dictionary to store camera data
usd_data = {}
for i in range(len(attr_list)):
    usd_data.update({attr_list[i]: []})

# append usd parameter data to dictionary
for m in range(len(camera_prim_paths)):
    camera_prim = UsdGeom.Camera(stage.DefinePrim(camera_prim_paths[m], "Camera"))
    object_prim = get_prim_at_path(camera_prim_paths[m])
    usd_data["name"].append(os.path.basename(camera_prim_paths[m]))
    usd_data[attr_list[1]].append(str(camera_prim.GetFocalLengthAttr().Get()))
    usd_data[attr_list[2]].append(str(camera_prim.GetFocusDistanceAttr().Get()))
    usd_data[attr_list[3]].append(str(camera_prim.GetFStopAttr().Get()))
    usd_data[attr_list[4]].append(str(camera_prim.GetProjectionAttr().Get()))
    usd_data[attr_list[5]].append(str(object_prim.GetAttribute("stereoRole").Get()))
    usd_data[attr_list[6]].append(str(camera_prim.GetHorizontalApertureAttr().Get()))
    usd_data[attr_list[7]].append(str(camera_prim.GetVerticalApertureAttr().Get()))
    usd_data[attr_list[8]].append(str(camera_prim.GetClippingRangeAttr().Get()))
    usd_data[attr_list[9]].append(str(object_prim.GetAttribute("cameraProjectionType").Get()))
    usd_data[attr_list[10]].append(str(object_prim.GetAttribute("fthetaWidth").Get()))
    usd_data[attr_list[11]].append(str(object_prim.GetAttribute("fthetaHeight").Get()))
    usd_data[attr_list[12]].append(str(object_prim.GetAttribute("fthetaCx").Get()))
    usd_data[attr_list[13]].append(str(object_prim.GetAttribute("fthetaCy").Get()))
    usd_data[attr_list[14]].append(str(object_prim.GetAttribute("fthetaMaxFov").Get()))
    usd_data[attr_list[15]].append(str(object_prim.GetAttribute("fthetaPolyA").Get()))
    usd_data[attr_list[16]].append(str(object_prim.GetAttribute("fthetaPolyB").Get()))
    usd_data[attr_list[17]].append(str(object_prim.GetAttribute("fthetaPolyC").Get()))
    usd_data[attr_list[18]].append(str(object_prim.GetAttribute("fthetaPolyD").Get()))
    usd_data[attr_list[19]].append(str(object_prim.GetAttribute("fthetaPolyE").Get()))
    usd_data[attr_list[20]].append(str(object_prim.GetAttribute("fthetaPolyF").Get()))
    usd_data[attr_list[21]].append(str(object_prim.GetAttribute("p0").Get()))
    usd_data[attr_list[22]].append(str(object_prim.GetAttribute("p1").Get()))
    usd_data[attr_list[23]].append(str(object_prim.GetAttribute("s0").Get()))
    usd_data[attr_list[24]].append(str(object_prim.GetAttribute("s1").Get()))
    usd_data[attr_list[25]].append(str(object_prim.GetAttribute("s2").Get()))
    usd_data[attr_list[26]].append(str(object_prim.GetAttribute("s3").Get()))
    usd_data[attr_list[27]].append(str(object_prim.GetAttribute("physicalDistortionCoefficients").Get()))
    usd_data[attr_list[28]].append(str(object_prim.GetAttribute("physicalDistortionModel").Get()))
    for attr in attr_list:
        # replace instances of None with default value; replace with N/A if default value doesn't exist
        if "None" in usd_data[attr] and attr in default_values.keys():
            usd_data[attr].append(default_values[attr])
            usd_data[attr].remove("None")
        if "None" in usd_data[attr] and attr not in default_values.keys():
            usd_data[attr].append("Not Applicable")
            usd_data[attr].remove("None")


for m in range(len(camera_prim_paths)):
    csv_path = file_name[0] + ".csv"
    # create csv file with all of usd camera data
    for i in range(len(list(usd_data.keys()))):
        data_file = open(Path(__file__).parent / csv_path, "w+", newline="")
        csv_writer = csv.writer(data_file)
        # write items into one string, seperate string to write items into correct columns
        for attr in attr_list:
            header = [attr]
            # ignore items that aren't in the dictionary and write items to csv
            if attr in list(usd_data.keys()):
                for word in usd_data[attr]:
                    word = str(word).replace(",", " ")
                    header.append(word)
                csv_writer.writerow(header)
            else:
                continue
        data_file.close()

simulation_app.close()
