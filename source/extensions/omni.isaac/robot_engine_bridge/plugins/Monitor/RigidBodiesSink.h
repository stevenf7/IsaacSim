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
class RigidBodiesSink : public IsaacComponent
{
public:
    /**
     * @brief Construct a new Scenario From Message object
     *
     * @param appHandle
     * @param prim
     * @param stage
     */
    RigidBodiesSink(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);
    /**
     * @brief
     *
     * @param timeSeconds
     * @param timeNano
     * @param timeDifferenceNano
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
    std::vector<pxr::GfVec3d> mLastLinearVelocity, mLastAngularVelocity;
    /// The name of the channel on which commands are received
    std::string mOutputComponent = "output";
    std::string mRigidBodyChannelName = "bodies";
    /// List of prim paths
    std::string mRigidBodyPrimPaths = "";

    // List of actors to send rigid body data
    std::unordered_map<std::string, pxr::UsdPrim> mObjects;

    // Scale of stage
    double mUnitScale;
};
}
}
}
