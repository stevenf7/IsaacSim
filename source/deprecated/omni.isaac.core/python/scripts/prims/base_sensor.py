# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
import carb

carb.log_warn(
    "omni.isaac.core.prims.base_sensor has been deprecated in favor of isaacsim.core.api.sensors.base_sensor. Please update your code accordingly."
)


from isaacsim.core.api.sensors.base_sensor import BaseSensor
