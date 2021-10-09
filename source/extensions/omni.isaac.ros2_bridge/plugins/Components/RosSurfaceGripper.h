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
#include <omni/isaac/surface_gripper/SurfaceGripper.h>
#include <rosBridgeSchema/rosSurfaceGripper.h>

namespace omni
{
namespace isaac
{
namespace ros2_bridge
{


class RosSurfaceGripper : public IsaacComponent
{

public:
    RosSurfaceGripper(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);
    // Virtual so that it can be called when object is destroyed
    virtual ~RosSurfaceGripper();
    virtual void initialize(RosNode* rosNode,
                            const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                            pxr::UsdStageWeakPtr stage);
    virtual void onStart();
    virtual void onStop();
    virtual void onComponentChange();
    void pubCallback(rclcpp::PublisherBase* pub);
    void subCallback(const sensor_msgs::msg::JointState::SharedPtr msg);

private:
    std::string mSurfaceGripperPubTopic = "/gripper_state";
    std::string mSurfaceGripperSubTopic = "/gripper_command";
    int mQueueSize = 0;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    std::string mGripperEntityName = "gripper";
    std::unique_ptr<omni::isaac::surface_gripper::SurfaceGripper> mGripperJoint;
    omni::isaac::surface_gripper::SurfaceGripperProperties mProps;
};
}
}
}
