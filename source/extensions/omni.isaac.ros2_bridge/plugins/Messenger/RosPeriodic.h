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
class RosPeriodic : public ros_base::RosMessenger
{
public:
    explicit RosPeriodic()
    {
        event_type = ros_base::eRosEventPeriodic;
    }
    ~RosPeriodic()
    {
        CARB_LOG_INFO("Destroying Periodic");
        tickCallback_ = nullptr;
    }
    RosPeriodic(const RosPeriodic&) = delete;
    RosPeriodic& operator=(const RosPeriodic&) = delete;

    template <typename MessageType, class Callback>
    void init(rclcpp::Node* node, void (Callback::*callbackFn)(), Callback* object)
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
