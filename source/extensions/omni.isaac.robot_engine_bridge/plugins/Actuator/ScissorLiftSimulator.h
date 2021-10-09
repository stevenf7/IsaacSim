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
#include <robotEngineBridgeSchema/robotEngineScissorLift.h>

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
class ScissorLiftSimulator : public IsaacComponent
{
public:
    /**
     * @brief Construct a new ScissorLiftSimulator object
     *
     * @param appHandle
     * @param prim
     * @param stage
     */
    ScissorLiftSimulator(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);

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
    /// The name of the channel on which commands are received
    std::string mInputComponent = "input";
    std::string mOutputComponent = "output";
    std::string mCommandChannelName = "lift_command";
    std::string mStateChannelName = "lift_state";
    std::string mLiftJointName = "lift_joint";
    pxr::SdfPath mArticulationPath;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    /// Trigger raising and lowering of the lift
    bool mRaiseRequest, mLowerRequest;

    /// Speed in m/s that the lift lowers and raises
    float mLiftSpeed = 0.02f;

    /// current state of the lift
    enum LiftState
    {
        Lowered,
        Raising,
        Raised,
        Lowering
    };
    LiftState mState;

    /// current height of the lift.
    float mCurrentHeight;

    // Scale of stage
    double mUnitScale;
};
}
}
}
