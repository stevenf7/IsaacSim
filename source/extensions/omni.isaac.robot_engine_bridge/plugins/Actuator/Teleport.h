// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../Core/IsaacComponent.h"

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <robotEngineBridgeSchema/robotEngineTeleport.h>

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
    void addObject(const std::string& actorName, pxr::UsdPrim& prim);

    /**
     * @brief Remove a prim from this component
     *
     * @param actorName
     */
    void eraseObject(const std::string& actorName);

    /**
     * @brief Manual update call, only used by scenario from message
     *
     * @param inputComponent
     * @param inputChannel
     */
    void updateComponent(const std::string& inputComponent, const std::string& inputChannel);

private:
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    /// The name of the channel on which commands are received
    std::string mInputComponent = "input";
    std::string mTeleportChannelName = "teleport";

    // List of actors that can be teleported
    std::unordered_map<std::string, pxr::UsdPrim> mObjects;

    // Inv scale of stage
    double mInvUnitScale;
};
}
}
}
