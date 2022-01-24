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

#include <carb/logging/Log.h>

#include <omni/isaac/ros/RosMessenger.h>

#include <functional>

namespace omni
{
namespace isaac
{
namespace ros2_bridge
{
class RosService : public ros_base::RosMessenger
{
public:
    explicit RosService()
    {
        event_type = ros_base::eRosEventService;
    }

    ~RosService()
    {
        CARB_LOG_INFO("Destroying Service");
        srv_.reset();
        srv_ = nullptr;
    }

    RosService(const RosService&) = delete;
    RosService& operator=(const RosService&) = delete;

    template <typename MessageType, class Callback>
    void init(rclcpp::Node* node,
              const std::string& topic,
              bool (Callback::*callbackFn)(typename MessageType::Request::SharedPtr,
                                           typename MessageType::Response::SharedPtr),
              Callback* object)
    {
        topic_ = topic;
        queue_size_ = 0;
        srv_ = node->create_service<MessageType>(
            topic, std::bind(callbackFn, object, std::placeholders::_1, std::placeholders::_2));
    }
    std::shared_ptr<rclcpp::ServiceBase> srv_;

private:
};
}
}
}
