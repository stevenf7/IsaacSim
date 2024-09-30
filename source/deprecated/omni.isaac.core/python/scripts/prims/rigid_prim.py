# Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import carb

carb.log_warn(
    "omni.isaac.core.prims.rigid_prim has been deprecated in favor of isaacsim.core.api.prims.rigid_prim. Please update your code accordingly."
)


from isaacsim.core.api.prims.rigid_prim import RigidPrim
