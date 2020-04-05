#pragma once

#include "../Actuator/Teleport.h"
#include "../Core/IsaacComponent.h"
#include "../Monitor/RigidBodiesSink.h"

#include <omni/isaac/dynamic_control/DynamicControl.h>

#include <memory>
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
class ScenarioFromMessage : public IsaacComponent
{
public:
    /**
     * @brief Construct a new Scenario From Message object
     *
     * @param appHandle
     * @param prim
     * @param stage
     * @param dynamicControlPtr
     */
    ScenarioFromMessage(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);
    /**
     * @brief
     *
     * @param isaacCApiPtr
     * @param appHandle
     * @param prim
     * @param stage
     */
    virtual void initialize(IsaacCApi* isaacCApiPtr,
                            const isaac_handle_t& appHandle,
                            const pxr::UsdPrim& prim,
                            pxr::UsdStageRefPtr stage);

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

    /**
     * @brief Set the App Handle
     *
     * @param appHandle
     */
    virtual void setAppHandle(isaac_handle_t appHandle);

private:
    /**
     * @brief
     *
     */
    virtual void initSubComponents();

    /**
     * @brief Load scenario from robot engine message
     *
     * @param request
     */
    void LoadScenarioFromMessage(isaac_message::ActorGroup::Builder& request);

    /**
     * @brief Adds rigid body and teleport objects
     *
     * @param actorName
     * @param prim
     */
    void AddObject(std::string& actorName, pxr::UsdPrim& prim);

    /**
     * @brief Removes rigid body and teleport objects
     *
     * @param prim
     */
    void RemoveObject(std::string& actorName);

    std::unique_ptr<Teleport> mTeleport;
    std::unique_ptr<RigidBodiesSink> mRigidBodiesSink;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    /// The name of the channel on which commands are received
    std::string mInputComponent = "input";
    std::string mRequestChannelName = "scenario_actors";

    // Scale of stage
    double mUnitScale;
};
}
}
}
