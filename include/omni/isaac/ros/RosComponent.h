// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "omni/isaac/bridge/Component.h"
#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/profiler/Profile.h>

#include <rosBridgeSchema/rosBridgeComponent.h>

#include <chrono>
#include <string>
#include <vector>

namespace omni
{
namespace isaac
{
namespace ros_base
{

/**
 * @brief Base class which exchanges data with an Isaac SDK application.
 * This class provides helper functions to facilitate the data exchange.
 */
template <typename PrimType, typename NodeType>
class RosComponentBase : public utils::ComponentBase<PrimType>
{
public:
    virtual ~RosComponentBase()
    {
    }
    /**
     * @brief Initialize various pointers and handles in the component
     * Must be called after creation, can be overridden to initialize subcomponents
     *
     * @param isaacCApiPtr
     * @param appHandle
     * @param prim
     * @param stage
     */

    virtual void initialize(NodeType* rosNode, const PrimType& prim, pxr::UsdStageWeakPtr stage)
    {
        utils::ComponentBase<PrimType>::initialize(prim, stage);
        mRosNode = std::make_unique<NodeType>(prim.GetPath().GetString());
    }
    /**
     * @brief Function that runs after start is pressed
     *
     */
    virtual void onStart()
    {
    }
    /** @brief Function that runs after stop is pressed
     *
     */
    virtual void onStop()
    {
    }
    /**
     * @brief Called every frame, ticks the internal rosnode for each component
     *
     */
    virtual void tick()
    {
        mRosNode->tick();
    };

    /**
     * @brief Function that is called each physics step
     *
     */
    virtual void onPhysicsStep(float dt)
    {
    }
    /**
     * @brief Publish any Messages
     *
     */
    virtual void publishAllMessages(){};

    /**
     * @brief Called every time the Prim is changed
     *
     */
    virtual void onComponentChange()
    {
        isaac::utils::safeGetAttribute(this->mPrim.GetRosNodePrefixAttr(), mRosNodePrefix);
        isaac::utils::safeGetAttribute(this->mPrim.GetEnabledAttr(), this->mEnabled);
    }

    /**
     * @brief Update timestamps for component
     *
     * @param timeSeconds
     * @param dt
     * @param timeNano
     */
    virtual void updateTimestamp(double timeSeconds,
                                 double dt,
                                 int64_t timeNano,
                                 std::chrono::_V2::system_clock::rep systemTimeNano)
    {
        utils::ComponentBase<PrimType>::updateTimestamp(timeSeconds, dt, timeNano);
        mSystemTimeNanoSeconds = systemTimeNano;
    }

    /**
     * @brief Update physics timestamp for component
     *
     * @param physicsTimeSeconds
     * @param physicsDt
     */
    virtual void updatePhysicsTimestamp(double physicsTimeSeconds, double physicsDt)
    {
        mPhysicsTimeSeconds = physicsTimeSeconds;
        mPhysicsDt = physicsDt;
    }

    /**
     * @brief Sets whether or not this component publishes its header with sim time or system time
     *
     * @param useSimTime
     */
    virtual void setUseSimTime(const bool useSimTime)
    {
        mUseSimTime = useSimTime;
    }

    /**
     * @brief Sets whether or not this component updates its sim time using the physics step
     *
     * @param usePhysicsStepSimTime
     */
    virtual void setUsePhysicsStepSimTime(const bool usePhysicsStepSimTime)
    {
        mUsePhysicsStepSimTime = usePhysicsStepSimTime;
    }

protected:
    std::string mRosNodePrefix = "";
    std::unique_ptr<NodeType> mRosNode;
    std::chrono::_V2::system_clock::rep mSystemTimeNanoSeconds = 0;
    double mPhysicsTimeSeconds = 0;
    double mPhysicsDt = 0;
    bool mUseSimTime = true;
    bool mUsePhysicsStepSimTime = false;
};


}
}
}
