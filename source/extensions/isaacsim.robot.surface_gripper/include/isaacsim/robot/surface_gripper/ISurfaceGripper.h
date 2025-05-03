// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.
#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

#include <usdrt/gf/matrix.h>

namespace isaacsim
{
namespace robot
{
namespace surface_gripper
{


struct SurfaceGripperInterface
{
    CARB_PLUGIN_INTERFACE("isaacsim::robot::surface_gripper::ISurfaceGripper", 0, 1);

    const char*(CARB_ABI* GetGripperStatus)(const char* primPath);
    bool(CARB_ABI* OpenGripper)(const char* primPath);
    bool(CARB_ABI* CloseGripper)(const char* primPath);
    std::vector<std::string>(CARB_ABI* GetGrippedObjects)(const char* primPath);
};

} // namespace surface_gripper
} // namespace robot
} // namespace isaacsim
