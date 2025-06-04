# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import csv
import json
import os

# list of pertinent categories to include in csv files
key_list = [
    "name",
    "type",
    "scanRateBaseHz",
    "reportRateBaseHz",
    "numberOfEmitters",
    "numberOfChannels",
    "nearRangeM",
    "farRangeM",
    "rotationDirection",
    "effectiveApertureSize",
    "focusDistM",
    "rangeResolutionM",
    "rangeAccuracyM",
    "minDistBetweenEchos",
    "minReflectance",
    "minReflectanceRange",
    "wavelengthNm",
    "pulseTimeNs",
    "azimuthErrorMean",
    "azimuthErrorStd",
    "elevationErrorMean",
    "elevationErrorStd",
    "maxReturns",
]


# allow input for dir path and ensure path is valid
def readable_dir(prospective_dir):
    if not os.path.isdir(prospective_dir):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
    if os.access(prospective_dir, os.R_OK):
        return prospective_dir
    else:
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))


# search for all nested dictionaries within the dictionary json data
def recursive_items(json_data):
    for key, val in json_data.items():
        if isinstance(val, dict):
            yield from recursive_items(val)
        else:
            yield (key, val)


parser = argparse.ArgumentParser(description="test", fromfile_prefix_chars="@")
parser.add_argument("-l", "--launch_directory", type=readable_dir, default="")
args, unknown = parser.parse_known_args()

json_files = []

# find all json files in the directory and add file directory to list of directories
for dir_path, dir_names, file_names in os.walk(args.launch_directory):
    for filename in file_names:
        if filename.endswith(".json"):
            json_files.append(dir_path + "/" + filename)

file_names = []
csv_paths = []

# create csv files for associatated json files
for n in range(len(json_files)):
    name = os.path.splitext(os.path.basename(json_files[n]))
    file_names.append(name[0])
    csv_paths.append(file_names[n] + ".csv")

for c in range(len(json_files)):
    with open(json_files[c]) as json_file:
        json_data = json.load(json_file)

    nested_data = {}
    for key, val in recursive_items(json_data):
        nested_data[key] = val
    json_data.update(nested_data)

    # write items from json data into csv file
    for key in range(len(list(json_data.keys()))):
        data_file = open(csv_paths[c], "w", newline="")
        csv_writer = csv.writer(data_file)

        for key in key_list:
            if key in list(json_data.keys()):
                csv_writer.writerow([key, json_data[key]])
            else:
                continue

        data_file.close()
