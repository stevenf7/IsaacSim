#pragma once

#include "../Core/IsaacComponent.h"

#include <RobotEngineBridgeSchema/robotEngineJointControl.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>

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
class JointControl : public IsaacComponent
{
public:
    /**
     * @brief Construct a new JointControl object
     *
     * @param appHandle
     * @param prim
     * @param stage
     */
    JointControl(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);

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
    std::string mJointControlChannelName = "joint_position";
    std::string mJointStateChannelName = "joint_state";
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    float mLimitOffset = 0.01f;
};
}
}
}
