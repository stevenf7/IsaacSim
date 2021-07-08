// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once


// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "../Core/RosMessenger.h"
#include "ros/callback_queue.h"
#include "ros/ros.h"

#include <carb/logging/Log.h>

#include <functional>


namespace omni
{
namespace isaac
{
namespace ros_bridge
{
class RosPeriodic : public RosMessenger
{
public:
    explicit RosPeriodic()
    {
        event_type = eRosEventPeriodic;
    }
    ~RosPeriodic()
    {
        tickCallback_ = nullptr;
    }
    RosPeriodic(const RosPeriodic&) = delete;
    RosPeriodic& operator=(const RosPeriodic&) = delete;

    template <typename MessageType, class Callback>
    void init(ros::NodeHandle* node, void (Callback::*callbackFn)(), Callback* object)
    {
        tickCallback_ = std::bind(callbackFn, object);
    }
    void tick()
    {
        tickCallback_();
    }

private:
    std::function<void()> tickCallback_ = nullptr;
};
}
}
}
