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

#include <carb/logging/Log.h>

#include <geometry_msgs/PoseStamped.h>
#include <omni/isaac/ros_bridge/RosBridge.h>
#include <ros/ros.h>
#include <rosgraph_msgs/Clock.h>
#include <sensor_msgs/JointState.h>
#include <tf2_msgs/TFMessage.h>

#include <vector>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{
class RosNode;

class RosCallback
{
public:
    explicit RosCallback(RosNode* node);
    explicit RosCallback(RosNode* node, const std::vector<std::string>& paths);
    RosCallback(const RosCallback&) = default;
    virtual ~RosCallback() = default;
    virtual void pubCallback(ros::Publisher* pub);
    virtual void tickCallback();
    std::vector<std::string> getPaths();
    void set_enable_pub(const bool enabled);
    void set_enable_sub(const bool enabled);
    void set_enable_srv(const bool enabled);
    bool get_enable_pub();
    bool get_enable_sub();
    bool get_enable_srv();
    // RosMessageType getMessageType();

protected:
    RosNode* node_;
    // The paths that this callback will inspect and modify
    std::vector<std::string> paths_;
    // convert paths to pointers
    bool enable_pub = true;
    bool enable_sub = true;
    bool enable_srv = true;
};

}
}
}
