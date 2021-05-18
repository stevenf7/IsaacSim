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
class RosPublisher : public RosMessenger
{
public:
    explicit RosPublisher()
    {
        event_type = eRosEventPublish;
    }
    ~RosPublisher()
    {
        // if (pub_)
        // {
        //     pub_-shutdown();
        // }
        pub_.reset();
        pubCallback_ = nullptr;
    }
    RosPublisher(const RosPublisher&) = delete;
    RosPublisher& operator=(const RosPublisher&) = delete;

    template <typename MessageType, class Callback>
    void init(rclcpp::Node* node,
              const std::string& topic,
              const int queueSize,
              void (Callback::*callbackFn)(rclcpp::PublisherBase* pub),
              Callback* object)
    {
        topic_ = topic;
        queue_size_ = queueSize;
        pubCallback_ = std::bind(callbackFn, object, std::placeholders::_1);
        pub_ = node->create_publisher<MessageType>(topic, queueSize);
    }
    void publish()
    {
        if (pub_)
        {
            pubCallback_(pub_.get());
        }
    }

private:
    std::shared_ptr<rclcpp::PublisherBase> pub_;
    std::function<void(rclcpp::PublisherBase* pub)> pubCallback_ = nullptr;
};
}
}
}
