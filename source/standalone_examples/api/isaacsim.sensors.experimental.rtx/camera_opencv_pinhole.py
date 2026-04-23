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

"""Configure a camera with OpenCV pinhole (rational polynomial) distortion model.

This example demonstrates how to:
- Apply the ``OmniLensDistortionOpenCvPinholeAPI`` schema to a camera prim
- Set pinhole intrinsic parameters (cx, cy, fx, fy) and distortion coefficients (k1-k6, p1-p2, s1-s4)
- Render a distorted image using ``CameraSensor``
"""

import argparse

from isaacsim import SimulationApp

parser = argparse.ArgumentParser(description="Camera with OpenCV pinhole distortion.")
parser.add_argument("--test", default=False, action="store_true", help="Run in test mode.")
args, _ = parser.parse_known_args()

simulation_app = SimulationApp({"headless": True})

import numpy as np
import omni
from isaacsim.core.experimental.objects import Cube
from isaacsim.sensors.experimental.rtx import CameraSensor, RtxCamera
from pxr import Gf

# =============================================================================
# CREATE SCENE
# =============================================================================

for i, (x, y, color) in enumerate([(3, 0, [1, 0, 0]), (5, 2, [0, 1, 0]), (4, -2, [0, 0, 1])]):
    Cube(f"/World/cube_{i}", sizes=1.0, positions=np.array([float(x), float(y), 0.5]), colors=color)

# =============================================================================
# CREATE CAMERA WITH PINHOLE DISTORTION
# =============================================================================
# The OmniLensDistortionOpenCvPinholeAPI schema adds rational polynomial
# distortion attributes to the camera prim. Supports up to 12 distortion
# coefficients: k1-k6 (radial), p1-p2 (tangential), s1-s4 (thin prism).

WIDTH, HEIGHT = 1280, 720

cam = RtxCamera(
    "/World/camera",
    schemas=["OmniLensDistortionOpenCvPinholeAPI"],
    attributes={
        # Intrinsic parameters (pixels)
        "omni:lensdistortion:opencvPinhole:cx": WIDTH / 2.0,
        "omni:lensdistortion:opencvPinhole:cy": HEIGHT / 2.0,
        "omni:lensdistortion:opencvPinhole:fx": 600.0,
        "omni:lensdistortion:opencvPinhole:fy": 600.0,
        # Radial distortion coefficients
        "omni:lensdistortion:opencvPinhole:k1": 0.1,
        "omni:lensdistortion:opencvPinhole:k2": -0.05,
        "omni:lensdistortion:opencvPinhole:k3": 0.0,
        # Tangential distortion coefficients
        "omni:lensdistortion:opencvPinhole:p1": 0.001,
        "omni:lensdistortion:opencvPinhole:p2": -0.001,
        # Image size (must be Gf.Vec2i for the int2 attribute)
        "omni:lensdistortion:opencvPinhole:imageSize": Gf.Vec2i(WIDTH, HEIGHT),
    },
    translations=np.array([0.0, 0.0, 0.5]),
)

# Set the distortion model selector
cam.prims[0].GetAttribute("omni:lensdistortion:model").Set("opencvPinhole")

print(f"Created camera with OpenCV pinhole distortion at {cam.paths[0]}")

# =============================================================================
# CREATE SENSOR AND RENDER
# =============================================================================

sensor = CameraSensor(cam, resolution=(HEIGHT, WIDTH), annotators=["rgb"])

timeline = omni.timeline.get_timeline_interface()
timeline.play()

frame_count = 0
while simulation_app.is_running():
    simulation_app.update()
    frame_count += 1

    data, info = sensor.get_data("rgb")
    if data is not None and frame_count == 10:
        print(f"  RGB shape: {data.shape}, dtype: {data.dtype}")
        print(f"  Pinhole distortion is applied in the rendered image")

    if args.test and frame_count >= 20:
        break

timeline.stop()
simulation_app.close()
