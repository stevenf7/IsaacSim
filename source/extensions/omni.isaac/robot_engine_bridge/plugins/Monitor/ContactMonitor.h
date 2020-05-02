#pragma once

#include "../Core/IsaacComponent.h"

#include <carb/physx/physx.h>

#include <RobotEngineBridgeSchema/robotEngineContactMonitor.h>
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
class ContactMonitor : public IsaacComponent
{
public:
    /**
     * @brief Construct a new Contact Monitor object
     *
     */
    ContactMonitor(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);
    /**
     * @brief Destroy the Contact Monitor object
     *
     */
    ~ContactMonitor();
    /**
     * @brief Tick the component
     */
    virtual void tick();
    /**
     * @brief The rigid bodies might not be valid, so force update on start
     *
     */
    virtual void onStart();
    /**
     * @brief
     *
     */
    virtual void onComponentChange();

private:
    void processContact(carb::events::IEvent* e);
    carb::physics::PhysX* mPhysxPtr = nullptr;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    /// The name of the channel on which contact data is output
    std::string mOutputComponent = "output";
    std::string mOutputChannel = "bodies";
    float mForceThreshold = 100000;
    carb::events::ISubscriptionPtr mContactCallback;
    pxr::UsdPrim mTargetPrim;
    pxr::SdfPathVector mIgnoredTargets;
    // Scale of stage
    double mUnitScale;
};
}
}
}
