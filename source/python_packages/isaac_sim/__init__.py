# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os

if not os.getenv("CARB_APP_PATH"):
    import ctypes
    import os
    import sys

    root_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.normpath(os.path.join(root_path, "..", ".."))

    # preload libcarb.so
    ctypes.PyDLL(os.path.join(root_path, "kit", "libcarb.so"), mode=ctypes.RTLD_GLOBAL)

    # set environment variables
    if not os.environ.get("CARB_APP_PATH", None):
        os.environ["CARB_APP_PATH"] = os.path.join(root_path, "kit")
    if not os.environ.get("EXP_PATH", None):
        os.environ["EXP_PATH"] = os.path.join(root_path, "apps")
    if not os.environ.get("ISAAC_PATH", None):
        os.environ["ISAAC_PATH"] = os.path.join(root_path)

    # set PYTHONPATH
    paths = [
        # kit
        os.path.join(root_path, "kit", "kernel", "py"),
        # isaac-sim
        os.path.join(root_path, "exts", "omni.isaac.kit"),
    ]
    for path in paths:
        if not path in sys.path:
            if not os.path.exists(path):
                print(f"PYTHONPATH: path doesn't exist ({path})")
                continue
            sys.path.insert(0, path)


# expose Isaac Sim API
from omni.isaac.kit import AppFramework, SimulationApp
