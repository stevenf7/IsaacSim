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

#include "RosCallback.h"
#include "rclcpp/rclcpp.hpp"

#include <carb/logging/Log.h>

#include <omni/isaac/ros2_bridge/Ros2Bridge.h>

#include <functional>

namespace omni
{
namespace isaac
{
namespace ros2_bridge
{
class RosMessenger
{
public:
    explicit RosMessenger()
    {
    }

    virtual ~RosMessenger()
    {
        CARB_LOG_INFO("Destroying Messenger");
    }

    RosMessenger(const RosMessenger&) = delete;
    RosMessenger& operator=(const RosMessenger&) = delete;
    Ros2EventType getEventType()
    {
        return event_type;
    }
    std::string getTopic()
    {
        return topic_;
    }
    size_t getQueueSize()
    {
        return queue_size_;
    }

protected:
    Ros2EventType event_type = eRosEventNone;
    std::string topic_ = "";
    size_t queue_size_ = 0;
};
}
}
}
