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
    "omni.isaac.core.scenes.scene_registry has been deprecated in favor of isaacsim.core.api.scenes.scene_registry. Please update your code accordingly."
)


from isaacsim.core.api.scenes.scene_registry import SceneRegistry
