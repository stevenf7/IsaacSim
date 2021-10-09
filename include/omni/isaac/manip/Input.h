// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
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

namespace omni
{
namespace isaac
{
namespace manip
{

typedef void (*GamepadEventFn)(int axis, float value, void* userData);

struct Input
{
    CARB_PLUGIN_INTERFACE("carb::isaac::manip::Input", 0, 1);

    void(CARB_ABI* bind_gamepad)(GamepadEventFn eventFn, void* userData);
    void(CARB_ABI* unbind_gamepad)();
};

}
}
}
