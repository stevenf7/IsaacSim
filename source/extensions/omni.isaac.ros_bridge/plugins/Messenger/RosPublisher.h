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
class RosPublisher : public RosMessenger
{
public:
    explicit RosPublisher()
    {
        event_type = eRosEventPublish;
    }
    ~RosPublisher()
    {
        if (pub_)
        {
            pub_->shutdown();
        }
        pub_.reset();
        pubCallback_ = nullptr;
    }
    RosPublisher(const RosPublisher&) = delete;
    RosPublisher& operator=(const RosPublisher&) = delete;

    template <typename MessageType, class Callback>
    void init(ros::NodeHandle* node,
              const std::string& topic,
              const int queueSize,
              void (Callback::*callbackFn)(ros::Publisher* pub),
              Callback* object)
    {
        topic_ = topic;
        queue_size_ = queueSize;
        pubCallback_ = std::bind(callbackFn, object, std::placeholders::_1);
        pub_ = std::make_unique<ros::Publisher>(node->advertise<MessageType>(topic, queueSize));
    }
    void publish()
    {
        if (pub_)
        {
            pubCallback_(pub_.get());
        }
    }

private:
    std::unique_ptr<ros::Publisher> pub_;
    std::function<void(ros::Publisher* pub)> pubCallback_ = nullptr;
};
}
}
}
