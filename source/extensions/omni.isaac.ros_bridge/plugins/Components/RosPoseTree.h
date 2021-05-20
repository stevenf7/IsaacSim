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

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <rosBridgeSchema/rosPoseTree.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{


class RosPoseTree : public IsaacComponent
{

public:
    RosPoseTree(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);
    // Virtual so that it can be called when object is destroyed
    virtual ~RosPoseTree();
    virtual void initialize(RosNode* rosNode,
                            const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                            pxr::UsdStageWeakPtr stage);
    virtual void onStart();
    virtual void onStop();
    virtual void onComponentChange();
    void pubCallback(ros::Publisher* pub);

private:
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    double mStageUnits = 1;
    std::unordered_map<std::string, std::pair<size_t, pxr::UsdPrim>> mObjects;
    int mQueueSize = 0;
    std::string mPoseTreePubTopic = "/tf";
    pxr::SdfPath mParentPath;
    pxr::UsdPrim mParentPrim;
    pxr::SdfPathVector mTargets;
};
}
}
}
