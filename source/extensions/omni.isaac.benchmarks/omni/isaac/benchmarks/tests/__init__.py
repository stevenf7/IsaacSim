# Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# scan_for_test_modules = True

import sys

from .test_benchmark_camera import *
from .test_benchmark_physx_lidar import *
from .test_benchmark_real_time_factor import *
from .test_benchmark_robots import *
from .test_benchmark_scene_generation import *
from .test_benchmark_sdg_generation import *

if sys.platform != "win32":
    from .test_benchmark_ros_camera import *

    # from .test_benchmark_rtx_lidar import *
