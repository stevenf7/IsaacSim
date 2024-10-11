// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
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

namespace isaacsim
{

namespace ros1
{

namespace bridge
{

struct RosBridge
{
    CARB_PLUGIN_INTERFACE("isaacsim::ros1::bridge::RosBridge", 0, 2);
};
}
}
}
