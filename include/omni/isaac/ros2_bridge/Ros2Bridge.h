// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
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

namespace omni
{

namespace isaac
{

namespace ros2_bridge
{

enum Ros2EventType
{
    eRosEventNone,
    eRosEventPublish,
    eRosEventSubscribe,
    eRosEventService,
    eRosEventPeriodic,
};


struct Ros2Bridge
{
    CARB_PLUGIN_INTERFACE("omni::isaac::ros2_bridge::Ros2Bridge", 0, 1);
    void(CARB_ABI* setUseSimTime)(const bool useSimTime);
    bool(CARB_ABI* tickComponent)(const std::string& primPath);
};
}
}
}
