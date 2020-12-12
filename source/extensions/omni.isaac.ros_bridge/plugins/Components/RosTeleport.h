// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

// #include "RosCallback.h"
#include "../../msgs/melodic/IsaacPose.h"
#include "../Core/IsaacComponent.h"
#include "../Core/RosNode.h"

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <rosBridgeSchema/rosTeleport.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
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

    virtual void onComponentChange();
    bool srvCallback(isaac_bridge::IsaacPose::Request& req, isaac_bridge::IsaacPose::Response& res);

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
