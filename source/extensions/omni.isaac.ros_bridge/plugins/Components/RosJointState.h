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
#include <rosBridgeSchema/rosJointState.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{


class RosJointState : public IsaacComponent
{

public:
    RosJointState(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);
    // Virtual so that it can be called when object is destroyed
    virtual ~RosJointState();
    virtual void initialize(RosNode* rosNode,
                            const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                            pxr::UsdStageWeakPtr stage);

    virtual void onComponentChange();
    void pubCallback(ros::Publisher* pub);
    void subCallback(const sensor_msgs::JointState::ConstPtr& msg);

private:
    std::string mJointStatePubTopic = "/joint_state";
    std::string mJointStateSubTopic = "/joint_command";
    int mQueueSize = 0;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    double mUnitScale = 1;
    pxr::SdfPath mArticulationPath;
};
}
}
}
