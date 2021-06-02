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

#include <carb/logging/Log.h>
#include <functional>

#include "rclcpp/rclcpp.hpp"
#include "../Core/RosMessenger.h"

namespace omni
{
namespace isaac
{
namespace ros2_bridge
{
class RosSubscriber : public RosMessenger
{
public:
    explicit RosSubscriber()
    {
        event_type = eRosEventSubscribe;
    }

    ~RosSubscriber()
    {
        CARB_LOG_INFO("Destroying Subscriber");
        sub_.reset();
        sub_ = nullptr;
    }

    RosSubscriber(const RosSubscriber&) = delete;
    RosSubscriber& operator=(const RosSubscriber&) = delete;

    template <typename MessageType, class Callback>
    void init(rclcpp::Node* node,
              const std::string& topic,
              const int queueSize,
              void (Callback::*callbackFn)(const typename MessageType::SharedPtr),
              Callback* object)
    {
        topic_ = topic;
        queue_size_ = queueSize;
        sub_ = node->create_subscription<MessageType>(
            topic, queueSize, std::bind(callbackFn, object, std::placeholders::_1));
    }
    std::shared_ptr<rclcpp::SubscriptionBase> sub_;

private:
};
}
}
}
