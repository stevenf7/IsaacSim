// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
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

#include <isaacSensorSchema/isaacBaseSensor.h>

#include <string>
#include <vector>

namespace omni
{
namespace isaac
{
namespace sensor
{
inline float lerp(const float& start, const float& end, const float t)
{
    return start + ((end - start) * t);
}

/**
 * @brief Base class which simulates a non RTX isaac sensor
 */
template <class PrimType>
class IsaacSensorComponentBase : public utils::ComponentBase<PrimType>
{
public:
    IsaacSensorComponentBase()
    {
    }

    ~IsaacSensorComponentBase()
    {
    }

    virtual void initialize(const PrimType& prim, const pxr::UsdStageWeakPtr stage)
    {
        utils::ComponentBase<PrimType>::initialize(prim, stage);
    }

    virtual void onStart()
    {
        onComponentChange();
    }

    virtual void onComponentChange()
    {
        // base sensor on component change
        isaac::utils::safeGetAttribute(this->mPrim.GetEnabledAttr(), this->mEnabled);
    }

    virtual void preTick()
    {
        return;
    }

    virtual void tick() = 0;

    // check
    virtual void onPhysicsStep(){};

    virtual void onStop()
    {
    }

    pxr::UsdPrim getParentPrim()
    {
        return mParentPrim;
    }

protected:
    pxr::UsdPrim mParentPrim;
};
typedef IsaacSensorComponentBase<pxr::IsaacSensorIsaacBaseSensor> IsaacBaseSensorComponent;

}
}
}
