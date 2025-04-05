# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import carb
import omni

old_extension_name = "omni.isaac.sensor"

# Provide deprecation warning to user
carb.log_warn(
    f"{old_extension_name}.commands has been deprecated in favor of isaacsim.sensors.physics.commands, isaacsim.sensors.physx.commands, and isaacsim.sensors.rtx.commands. Please update your code accordingly."
)

from isaacsim.sensors.physics import IsaacSensorCreateContactSensor, IsaacSensorCreateImuSensor, IsaacSensorCreatePrim
from isaacsim.sensors.physx import IsaacSensorCreateLightBeamSensor
from isaacsim.sensors.rtx import IsaacSensorCreateRtxIDS, IsaacSensorCreateRtxLidar, IsaacSensorCreateRtxRadar
