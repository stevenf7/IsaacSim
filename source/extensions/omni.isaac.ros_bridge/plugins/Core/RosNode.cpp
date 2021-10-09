// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
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
namespace ros_bridge
{
RosNode::RosNode(std::string name)
{
    // std::string fullName = ros::this_node::getName();
    // if (name.size() > 0)
    // {
    //     fullName = ros::names::clean(ros::this_node::getName() + "/" + name);
    // }
    CARB_LOG_INFO("Ros Node Was Created");
    rosnode_ = std::make_unique<ros::NodeHandle>(name);
    rosnode_->setCallbackQueue(&(callbackQueue_));
    // CARB_LOG_INFO("Ros Node Resolved Namespace: %s Unresolved: %s", rosnode_->getNamespace().c_str(),
    //               rosnode_->getUnresolvedNamespace().c_str());
}
void RosNode::start()
{

    // Call once after creating
    // if (ros::ok())
    // {
    //     callbackQueue_.callAvailable();
    // }
}
void RosNode::stop()
{
    for (auto& msg : mMessages)
    {
        msg.second = nullptr;
    }
    mMessages.clear();

    if (rosnode_)
    {
        CARB_LOG_INFO("Ros Node Was Shutdown");
        rosnode_->shutdown();
    }
    rosnode_ = nullptr;
}
void RosNode::tick()
{

    if (ros::ok())
    {
        callbackQueue_.callAvailable();
        for (auto& msg : mMessages)
        {
            RosPublisher* pub = dynamic_cast<RosPublisher*>(msg.second.get());
            if (msg.second && msg.second->getEventType() == eRosEventPublish && pub)
            {
                pub->publish();
            }
            RosPeriodic* per = dynamic_cast<RosPeriodic*>(msg.second.get());
            if (msg.second && msg.second->getEventType() == eRosEventPeriodic && per)
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
