// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

#include <string>
#include <vector>
class Ros2Factory;

namespace omni
{

namespace isaac
{

namespace ros2_bridge
{

struct Ros2Bridge
{
    CARB_PLUGIN_INTERFACE("omni::isaac::ros2_bridge::Ros2Bridge", 0, 2);
    uint64_t const(CARB_ABI* getDefaultContextHandle)();
    Ros2Factory* const(CARB_ABI* getFactory)();
    bool const(CARB_ABI* getStartupStatus)();
};
}
}
}
