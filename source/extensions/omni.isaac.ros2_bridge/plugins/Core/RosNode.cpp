// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "RosNode.h"

#include <carb/Framework.h>
#include <carb/Types.h>

namespace omni
{
namespace isaac
{
namespace ros2_bridge
{
RosNode::RosNode(std::string name)
{
    // std::string fullName = ros::this_node::getName();
    // if (name.size() > 0)
    // {
    //     fullName = ros::names::clean(ros::this_node::getName() + "/" + name);
    // }

    if (name.size() == 0)
    {
        carb::Framework* framework = carb::getFramework();
        carb::settings::ISettings* settings = framework->acquireInterface<carb::settings::ISettings>();
        name = settings->get<const char*>("/exts/omni.isaac.ros2_bridge/nodeName");
        if (name.size() == 0)
        {
            name = "OmniIsaacRos2Bridge";
        }
    }
    else
    {
        std::replace_if(name.begin(), name.end(), [](auto ch) { return !(::isalnum(ch) || ch == '_'); }, '_');
    }
    CARB_LOG_INFO("Ros2 Node Was Created with name %s", name.c_str());
    rosnode_ = std::make_shared<rclcpp::Node>(name);
    executor = std::make_shared<rclcpp::executors::SingleThreadedExecutor>();
    executor->add_node(rosnode_);
    // auto group = rosnode_->create_callback_group(rclcpp::callback_group::CallbackGroupType::MutuallyExclusive);

    // rosnode_->setCallbackQueue(&(callbackQueue_)); TODO
    // CARB_LOG_INFO("Ros Node Resolved Namespace: %s Unresolved: %s", rosnode_->getNamespace().c_str(),
    //               rosnode_->getUnresolvedNamespace().c_str());
}

RosNode::~RosNode()
{
    for (auto& msg : mMessages)
    {
        msg.second = nullptr;
    }
    mMessages.clear();
    if (executor)
    {
        executor->cancel();
        executor->remove_node(rosnode_);
    }
    executor.reset();
    if (rosnode_)
    {
        CARB_LOG_INFO("Ros2 Node Was Shutdown");
        // rosnode_->shutdown();
    }
    rosnode_.reset();
    rosnode_ = nullptr;
    CARB_LOG_INFO("Ros2 Node Shutdown Complete");
}
void RosNode::tick()
{

    if (rclcpp::ok())
    {
        // callbackQueue_.callAvailable();
        executor->spin_once(std::chrono::nanoseconds(0));

        for (auto& msg : mMessages)
        {
            RosPublisher* pub = dynamic_cast<RosPublisher*>(msg.second.get());
            if (msg.second && msg.second->getEventType() == ros_base::eRosEventPublish && pub)
            {
                pub->publish();
            }
            RosPeriodic* per = dynamic_cast<RosPeriodic*>(msg.second.get());
            if (msg.second && msg.second->getEventType() == ros_base::eRosEventPeriodic && per)
            {
                per->tick();
            }
        }
    }
    else
    {
        CARB_LOG_ERROR("!ros::ok() An error has occurred within ROS.");
    }
}

void RosNode::destroyMessage(std::string topic)
{
    if (mMessages.find(topic) != mMessages.end())
    {
        mMessages[topic].reset();
        mMessages.erase(topic);
    }
}

// bool RosNode::deleteEvent(IsaacHandle event_handle)
// {
//     if (event_handle >= 0 && size_t(event_handle) < mMessages.size())
//     {
//         mMessages[event_handle].reset();
//         return true;
//     }
//     return false;
// }

}
}
}
