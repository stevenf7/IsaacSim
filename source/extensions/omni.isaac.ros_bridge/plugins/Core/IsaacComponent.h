// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "RosNode.h"
#include "plugins/core/Component.h"
#include "plugins/core/UsdUtilities.h"

#include <rosBridgeSchema/rosBridgeComponent.h>

#include <string>
#include <vector>
namespace omni
{
namespace isaac
{
namespace ros_bridge
{

/**
 * @brief Base class which exchanges data with an Isaac SDK application.
 * This class provides helper functions to facilitate the data exchange.
 */
template <typename PrimType>
class IsaacComponentBase : public utils::ComponentBase<PrimType>
{
public:
    virtual ~IsaacComponentBase()
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

    virtual void initialize(RosNode* rosNode, const PrimType& prim, pxr::UsdStageWeakPtr stage)
    {
        utils::ComponentBase<PrimType>::initialize(prim, stage);
        mRosNode = rosNode;
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
     * @brief Called every frame
     *
     */
    virtual void tick(){};

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
    virtual void updateTimestamp(double timeSeconds, double dt, int64_t timeNano)
    {
        this->mTimeNanoSeconds = timeNano;
        this->mTimeSeconds = timeSeconds;
        this->mTimeDelta = dt;
    }


protected:
    std::string mRosNodePrefix = "";
    RosNode* mRosNode;
};


typedef IsaacComponentBase<pxr::RosBridgeSchemaRosBridgeComponent> IsaacComponent;


}
}
}
