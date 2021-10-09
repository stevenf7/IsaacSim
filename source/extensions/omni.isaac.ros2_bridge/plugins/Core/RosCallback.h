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

#include <carb/logging/Log.h>

#include <geometry_msgs/msg/pose_stamped.hpp>
#include <omni/isaac/ros2_bridge/Ros2Bridge.h>
#include <rclcpp/rclcpp.hpp>
#include <rosgraph_msgs/msg/clock.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <tf2_msgs/msg/tf_message.hpp>

#include <vector>

namespace omni
{
namespace isaac
{
namespace ros2_bridge
{
class RosNode;

class RosCallback
{
public:
    explicit RosCallback(RosNode* node);
    explicit RosCallback(RosNode* node, const std::vector<std::string>& paths);
    RosCallback(const RosCallback&) = default;
    virtual ~RosCallback() = default;
    virtual void pubCallback(rclcpp::PublisherBase* pub);
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
    // RosMessageType message_type = eRosMessageNone;
    // std::vector<RosActor> actor_list;
};


// class RosCallbackJointState : public RosCallback
// {
// public:
//     explicit RosCallbackJointState(RosNode* node, const std::vector<std::string>& paths);
//     RosCallbackJointState(const RosCallbackJointState&) = default;
//     ~RosCallbackJointState() = default;
//     void buildMessage(const sensor_msgs::msg::JointState::SharedPtr msg, const bool teleport = false);
//     void subCallback(const sensor_msgs::msg::JointState::SharedPtr msg);
//     bool srvCallback(isaac_bridge::IsaacJointStates::Request& req, isaac_bridge::IsaacJointStates::Response& res);
//     virtual void pubCallback(rclcpp::PublisherBase* pub);
// };

// class RosCallbackTF : public RosCallback
// {
// public:
//     explicit RosCallbackTF(RosNode* node, const std::vector<std::string>& paths, tf2_ros::Buffer* tf_buffer);
//     RosCallbackTF(const RosCallbackTF&) = default;
//     ~RosCallbackTF() = default;
//     virtual void pubCallback(rclcpp::PublisherBase* pub);
//     virtual void tickCallback();
//     tf2_ros::Buffer* tf_buffer_;
// };

// class RosCallbackPose : public RosCallback
// {
// public:
//     explicit RosCallbackPose(RosNode* node, const std::vector<std::string>& paths);
//     RosCallbackPose(const RosCallbackPose&) = default;
//     ~RosCallbackPose() = default;
//     virtual void pubCallback(rclcpp::PublisherBase* pub);
//     void subCallback(const geometry_msgs::PoseStamped::SharedPtr msg);
//     bool srvCallback(isaac_bridge::IsaacPose::Request& req, isaac_bridge::IsaacPose::Response& res);
// };

// class RosCallbackSimState : public RosCallback
// {
// public:
//     explicit RosCallbackSimState(RosNode* node);
//     RosCallbackSimState(const RosCallbackSimState&) = default;
//     ~RosCallbackSimState() = default;
//     virtual void pubCallback(rclcpp::PublisherBase* pub);
// };
}
}
}
