// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "plugins/core/Component.h"

#include <string>
#include <vector>
namespace omni
{
namespace isaac
{
namespace lidar
{

/**
 * @brief Base class which exchanges data with an Isaac SDK application.
 * This class provides helper functions to facilitate the data exchange.
 */
template <class PrimType>
class SensorComponent : public utils::ComponentBase<PrimType>
{
    // using utils::ComponentBase<PrimType>::mTimeNanoSeconds;
    // using utils::ComponentBase<PrimType>::mTimeSeconds;
    // using utils::ComponentBase<PrimType>::mTimeDelta;
public:
    /**
     * @brief Construct a new Isaac Component
     */
    SensorComponent()
    {
    }
    /**
     * @brief Initialize various pointers and handles in the component
     * Must be called after creation, can be overridden to initialize subcomponents
     *

     * @param prim
     * @param stage
     */
    virtual void initialize(const PrimType& prim, pxr::UsdStageWeakPtr stage)
    {
        utils::ComponentBase<PrimType>::initialize(prim, stage);
    }
    /**
     * @brief Function that runs after start is pressed
     *
     */
    virtual void onStart() = 0;

    /**
     * @brief Called every frame
     *
     */
    virtual void tick() = 0;

    /**
     * @brief Called every time the Prim is changed
     *
     */
    virtual void onComponentChange()
    {
        // TODO: handle enable disable sensor usd attribute here?
    }

    /**
     * @brief Update timestamps for component
     *
     * @param timeSeconds
     * @param dt
     * @param timeNano
     */
    void updateTimestamp(double timeSeconds, double dt, int64_t timeNano)
    {
        this->mTimeNanoSeconds = timeNano;
        this->mTimeSeconds = timeSeconds;
        this->mTimeDelta = dt;
    }
};
}
}
}
