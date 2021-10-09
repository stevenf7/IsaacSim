// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
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
namespace ros2_bridge
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
    virtual void onStart();
    virtual void onStop();
    virtual void onComponentChange();
    virtual void onPhysicsStep(float dt);

    void pubCallback(rclcpp::PublisherBase* pub);
    void subCallback(const sensor_msgs::msg::JointState::SharedPtr msg);

private:
    std::string mJointStatePubTopic = "/joint_states";
    std::string mJointStateSubTopic = "/joint_command";
    int mQueueSize = 0;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    double mUnitScale = 1;
    pxr::SdfPath mArticulationPath;

    std::vector<float> mPrevJointPosition;
    std::vector<float> mCalculatedJointVelocity;
    omni::isaac::dynamic_control::DcDofState* mStates = nullptr;
    std::vector<dynamic_control::DcDofProperties> mDofProps;
};
}
}
}
