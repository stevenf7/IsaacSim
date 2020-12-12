// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once


// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <carb/logging/Log.h>
#include <functional>

#include "ros/callback_queue.h"
#include "ros/ros.h"
#include <omni/isaac/ros_bridge/RosBridge.h>
#include "RosCallback.h"

namespace omni
{
namespace isaac
{
namespace ros_bridge
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
    RosEventType getEventType()
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

    // std::unique_ptr<RosCallback> callback_;

protected:
    RosEventType event_type = eRosEventNone;
    std::string topic_ = "";
    size_t queue_size_ = 0;
};
}
}
}
