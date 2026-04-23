# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Configure a camera from ROS camera_info parameters.

This example demonstrates how to:
- Parse a ROS ``camera_info`` YAML-style parameter set
- Map ROS intrinsic matrix (K), distortion coefficients (D), and image size
  to ``RtxCamera`` schemas and attributes
- Create a camera matching a real-world ROS camera calibration
"""

import argparse

from isaacsim import SimulationApp

parser = argparse.ArgumentParser(description="Configure camera from ROS camera_info.")
parser.add_argument("--test", default=False, action="store_true", help="Run in test mode.")
args, _ = parser.parse_known_args()

simulation_app = SimulationApp({"headless": True})

import numpy as np
import omni
from isaacsim.core.experimental.objects import Cube
from isaacsim.sensors.experimental.rtx import CameraSensor, RtxCamera
from pxr import Gf

# =============================================================================
# ROS CAMERA_INFO PARAMETERS
# =============================================================================
# These would typically come from a ROS camera_info topic or YAML file.
# Example: a 1280x720 camera with slight barrel distortion.

IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720

# Intrinsic matrix K (3x3, row-major)
# [fx  0  cx]
# [ 0 fy  cy]
# [ 0  0   1]
K = [615.0, 0.0, 640.0, 0.0, 615.0, 360.0, 0.0, 0.0, 1.0]
fx, fy = K[0], K[4]
cx, cy = K[2], K[5]

# Distortion model and coefficients
DISTORTION_MODEL = "plumb_bob"  # OpenCV pinhole (k1,k2,p1,p2,k3)
D = [-0.1, 0.05, 0.001, -0.001, 0.0]

# =============================================================================
# CREATE SCENE
# =============================================================================

for i, (x, y) in enumerate([(3, 0), (5, 2), (4, -2)]):
    Cube(f"/World/cube_{i}", sizes=1.0, positions=np.array([float(x), float(y), 0.5]))

# =============================================================================
# CREATE CAMERA FROM ROS PARAMETERS
# =============================================================================
# Map ROS distortion_model to the appropriate lens distortion schema.
# - "plumb_bob" / "rational_polynomial" → OmniLensDistortionOpenCvPinholeAPI
# - "equidistant" → OmniLensDistortionOpenCvFisheyeAPI

if DISTORTION_MODEL in ("plumb_bob", "rational_polynomial"):
    schema = "OmniLensDistortionOpenCvPinholeAPI"
    prefix = "omni:lensdistortion:opencvPinhole"
    model_name = "opencvPinhole"
    # Map D coefficients to attribute names
    coeff_names = ["k1", "k2", "p1", "p2", "k3", "k4", "k5", "k6", "s1", "s2", "s3", "s4"]
    distortion_attrs = {f"{prefix}:{coeff_names[i]}": D[i] for i in range(len(D))}
elif DISTORTION_MODEL == "equidistant":
    schema = "OmniLensDistortionOpenCvFisheyeAPI"
    prefix = "omni:lensdistortion:opencvFisheye"
    model_name = "opencvFisheye"
    coeff_names = ["k1", "k2", "k3", "k4"]
    distortion_attrs = {f"{prefix}:{coeff_names[i]}": D[i] for i in range(len(D))}
else:
    raise ValueError(f"Unsupported distortion model: {DISTORTION_MODEL}")

# Build the full attribute dict
attributes = {
    f"{prefix}:cx": cx,
    f"{prefix}:cy": cy,
    f"{prefix}:fx": fx,
    f"{prefix}:fy": fy,
    f"{prefix}:imageSize": Gf.Vec2i(IMAGE_WIDTH, IMAGE_HEIGHT),
    **distortion_attrs,
}

cam = RtxCamera(
    "/World/ros_camera",
    schemas=[schema],
    attributes=attributes,
    translations=np.array([0.0, 0.0, 0.5]),
)

# Set the distortion model selector
cam.prims[0].GetAttribute("omni:lensdistortion:model").Set(model_name)

print(f"Created camera from ROS camera_info:")
print(f"  Resolution: {IMAGE_WIDTH}x{IMAGE_HEIGHT}")
print(f"  Intrinsics: fx={fx}, fy={fy}, cx={cx}, cy={cy}")
print(f"  Distortion model: {DISTORTION_MODEL} → {schema}")
print(f"  D: {D}")

# =============================================================================
# CREATE SENSOR AND RENDER
# =============================================================================

sensor = CameraSensor(cam, resolution=(IMAGE_HEIGHT, IMAGE_WIDTH), annotators=["rgb"])

timeline = omni.timeline.get_timeline_interface()
timeline.play()

frame_count = 0
while simulation_app.is_running():
    simulation_app.update()
    frame_count += 1

    data, _ = sensor.get_data("rgb")
    if data is not None and frame_count == 10:
        print(f"\n  RGB shape: {data.shape}")

    if args.test and frame_count >= 20:
        break

timeline.stop()
simulation_app.close()
