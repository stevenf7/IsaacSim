#pragma once

#include "../Core/IsaacComponent.h"

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/utils/SurfaceGripper.h>
#include <robotEngineBridgeSchema/robotEngineSurfaceGripper.h>

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
class SurfaceGripper : public IsaacComponent
{
public:
    /**
     * @brief Construct a new SurfaceGripper object
     *
     * @param appHandle
     * @param prim
     * @param stage
     */
    SurfaceGripper(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);

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
    std::string mGripperControlChannelName = "gripper_command";
    std::string mGripperStateChannelName = "gripper_state";
    std::string mGripperEntityName = "gripper";
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    std::unique_ptr<omni::isaac::utils::SurfaceGripper> mGripperJoint;
    omni::isaac::utils::SurfaceGripperProperties mProps;
};
}
}
}
