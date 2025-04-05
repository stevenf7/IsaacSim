# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import time

from isaacsim import SimulationApp

# Example ROS bridge sample showing rospy and rosclock interaction
kit = SimulationApp()
import omni
from isaacsim.core.utils.extensions import enable_extension

# enable ROS bridge extension
enable_extension("isaacsim.ros2.bridge")
kit.update()
kit.close()
