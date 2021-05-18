// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

// #include "RosCallback.h"
#include "../Core/IsaacComponent.h"
#include "../Core/RosNode.h"
#include "isaac_ros2_messages/srv/isaac_pose.hpp"

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <rosBridgeSchema/rosTeleport.h>

namespace omni
{
namespace isaac
{
namespace ros2_bridge
{


class RosTeleport : public IsaacComponent
{

public:
    RosTeleport(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);

    // Virtual so that it can be called when object is destroyed
    virtual ~RosTeleport();
    virtual void initialize(RosNode* rosNode,
                            const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                            pxr::UsdStageWeakPtr stage);
    virtual void onStart();
    virtual void onStop();
    virtual void onComponentChange();
    bool srvCallback(const isaac_ros2_messages::srv::IsaacPose::Request::SharedPtr req,
                     isaac_ros2_messages::srv::IsaacPose::Response::SharedPtr res);

private:
    void addObject(const std::string& actorName, pxr::UsdPrim& prim);
    void eraseObject(const std::string& actorName);

    std::string mPoseSrvTopic = "/pose_srv";
    double mUnitScale = 1;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    std::unordered_map<std::string, std::pair<size_t, pxr::UsdPrim>> mObjects;
};
}
}
}
