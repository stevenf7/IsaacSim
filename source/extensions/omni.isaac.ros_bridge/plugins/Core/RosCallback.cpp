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

#include "RosCallback.h"

#include "RosNode.h"

#include <omni/isaac/dynamic_control/DynamicControl.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{

using namespace omni::isaac::dynamic_control;

RosCallback::RosCallback(RosNode* node)
{
    node_ = node;
}
RosCallback::RosCallback(RosNode* node, const std::vector<std::string>& paths)
{
}
void RosCallback::pubCallback(ros::Publisher* pub)
{
    CARB_LOG_ERROR("Publisher Called but not implemented!");
}
void RosCallback::tickCallback()
{
}
std::vector<std::string> RosCallback::getPaths()
{
    return paths_;
}
void RosCallback::set_enable_pub(const bool enabled)
{
    enable_pub = enabled;
}
void RosCallback::set_enable_sub(const bool enabled)
{
    enable_sub = enabled;
}
void RosCallback::set_enable_srv(const bool enabled)
{
    enable_srv = enabled;
}
bool RosCallback::get_enable_pub()
{
    return enable_pub;
}
bool RosCallback::get_enable_sub()
{
    return enable_sub;
}
bool RosCallback::get_enable_srv()
{
    return enable_srv;
}

}
}
}
