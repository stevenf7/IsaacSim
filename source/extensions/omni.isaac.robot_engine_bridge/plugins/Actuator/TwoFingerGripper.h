// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../Core/IsaacComponent.h"

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <robotEngineBridgeSchema/robotEngineTwoFingerGripper.h>

#include <string>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

/**
 * @brief
 *
 */
class TwoFingerGripper : public IsaacComponent
{
public:
    /**
     * @brief Construct a new TwoFingerGripper object
     *
     * @param appHandle
     * @param prim
     * @param stage
     */
    TwoFingerGripper(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);

    /**
     * @brief The articulation might not be valid, so force update on start
     *
     */
    virtual void onStart();

    /**
     * @brief
     *
     */
    virtual void tick();

    /**
     * @brief
     *
     */
    virtual void onComponentChange();

private:
    void setDistance(const omni::isaac::dynamic_control::DcHandle& fingerHandle, float distance);
    bool isClosed();
    /// The name of the channel on which commands are received
    std::string mInputComponent = "input";
    std::string mOutputComponent = "output";
    std::string mGripperControlChannelName = "gripper_command";
    std::string mGripperStateChannelName = "gripper_state";
    std::string mGripperEntityName = "gripper";
    std::string mLeftJointName = "left_finger";
    std::string mRightJointName = "right_finger";
    float mOpenDistance = .04f;
    float mClosedDistance = 0;
    float mLimitOffset = 0.01f;
    float mTolerance = 0.01;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    omni::isaac::dynamic_control::DcHandle mLeftFingerHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    omni::isaac::dynamic_control::DcHandle mRightFingerHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    float mUnitScale;
};
}
}
}
