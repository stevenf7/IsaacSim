// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
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

#include "rclcpp/rclcpp.hpp"
// #include "rmw/qos_profiles.h"

#include <carb/logging/Log.h>

#include <omni/isaac/ros/RosMessenger.h>

#include <functional>


namespace omni
{
namespace isaac
{
namespace ros2_bridge
{
class RosPublisher : public ros_base::RosMessenger
{
public:
    explicit RosPublisher()
    {
        event_type = ros_base::eRosEventPublish;
    }
    ~RosPublisher()
    {
        CARB_LOG_INFO("Destroying Publisher");
        pub_.reset();
        pub_ = nullptr;
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
        // auto qos =
        //     rclcpp::QoS(rclcpp::QoSInitialization::from_rmw(rmw_qos_profile_sensor_data),
        //     rmw_qos_profile_sensor_data);
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
