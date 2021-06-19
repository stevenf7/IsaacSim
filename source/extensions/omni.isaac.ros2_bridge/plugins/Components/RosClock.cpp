// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
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

#include "RosClock.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include "rosgraph_msgs/msg/clock.hpp"
#include "std_msgs/msg/int64.hpp"
#include "std_msgs/msg/u_int8.hpp"
#include "std_srvs/srv/empty.hpp"
#include <time.h>
namespace omni
{
namespace isaac
{
namespace ros2_bridge
{

RosClock::~RosClock()
{
    CARB_LOG_INFO("RosClock Destroyed");
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mClockPubTopic);
}

void RosClock::initialize(RosNode* rosNode, const pxr::RosBridgeSchemaRosBridgeComponent& prim, pxr::UsdStageWeakPtr stage)
{
    IsaacComponent::initialize(rosNode, prim, stage);
}
void RosClock::onStart()
{
    onComponentChange();
}
void RosClock::onStop()
{
}
void RosClock::onComponentChange()
{

    IsaacComponent::onComponentChange();

    const pxr::RosBridgeSchemaRosClock& typedPrim = (pxr::RosBridgeSchemaRosClock)mPrim;
    // Destroy the old message, in case the topic changes
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mClockPubTopic);

    isaac::utils::safeGetAttribute(typedPrim.GetClockPubTopicAttr(), mClockPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetSimTimeAttr(), mSimTime);


    mRosNode->createPublisher<rosgraph_msgs::msg::Clock>(
        mPrim.GetPath().GetString(), mClockPubTopic, 0, &RosClock::pubCallback, this);
}

void RosClock::pubCallback(rclcpp::PublisherBase* pub)
{

    rosgraph_msgs::msg::Clock time_msg;
    if (mSimTime)
    {
        time_msg.clock = rclcpp::Time(mTimeNanoSeconds);
    }
    else
    {
        time_msg.clock = rclcpp::Time(mSystemTimeNanoSeconds);
    }

    static_cast<rclcpp::Publisher<rosgraph_msgs::msg::Clock, std::allocator<void>>*>(pub)->publish(time_msg);
}
}
}
}
