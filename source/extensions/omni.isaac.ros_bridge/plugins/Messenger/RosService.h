// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
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
class RosService : public RosMessenger
{
public:
    explicit RosService()
    {
        event_type = eRosEventService;
    }

    ~RosService()
    {
        if (srv_)
        {
            srv_->shutdown();
        }
        srv_ = nullptr;
    }

    RosService(const RosService&) = delete;
    RosService& operator=(const RosService&) = delete;

    template <typename MessageType, class Callback>
    void init(ros::NodeHandle* node,
              const std::string& topic,
              bool (Callback::*callbackFn)(typename MessageType::Request&, typename MessageType::Response&),
              Callback* object)
    {
        topic_ = topic;
        queue_size_ = 0;
        srv_ = std::make_unique<ros::ServiceServer>();
        *srv_ = node->advertiseService(topic, callbackFn, object);
    }
    std::unique_ptr<ros::ServiceServer> srv_;

private:
};
}
}
}
