#pragma once

#include "../Core/IsaacComponent.h"

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
class Teleport : public IsaacComponent
{
public:
    /**
     * @brief Construct a new Teleport object
     *
     * @param appHandle
     * @param prim
     * @param stage
     */
    Teleport(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);


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
     * @brief Add a prim to this component
     *
     * @param actorName
     * @param prim
     */
    void addObject(std::string& actorName, pxr::UsdPrim& prim);

    /**
     * @brief Remove a prim from this component
     *
     * @param actorName
     */
    void eraseObject(std::string& actorName);


private:
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    /// The name of the channel on which commands are received
    std::string mInputComponent = "input";
    std::string mTeleportChannelName = "teleport";

    // List of actors that can be teleported
    std::unordered_map<std::string, pxr::UsdPrim> mObjects;

    // Scale of stage
    double mUnitScale;
};
}
}
}
