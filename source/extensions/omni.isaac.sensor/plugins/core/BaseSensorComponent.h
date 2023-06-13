// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
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
#include <omni/isaac/debug_draw/PrimitiveDrawingHelper.h>
#include <omni/renderer/IDebugDraw.h>

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
    IsaacSensorComponentBase(omni::renderer::IDebugDraw* debugDrawPtr)
    {
        mPointDrawing = std::make_shared<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper>(
            omni::usd::UsdContext::getContext(), debugDrawPtr,
            omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::ePoints, true);

        mLineDrawing = std::make_shared<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper>(
            omni::usd::UsdContext::getContext(), debugDrawPtr,
            omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::eLines);
    }

    ~IsaacSensorComponentBase()
    {
        mLineDrawing.reset();
        mPointDrawing.reset();
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
        isaac::utils::safeGetAttribute(this->mPrim.GetVisualizeAttr(), mVisualize);
        pxr::UsdPrim tempPrim = this->mStage->GetPrimAtPath(this->mPrim.GetPath()).GetParent();

        // clearDraw function will clear the drawing, it will be redrawn in the sensor's onComponentChange based on the
        // mVisualize flag

        clearDraw();

        // Find valid parent (if exist)
        while (tempPrim.IsValid() && tempPrim.GetName().GetString() != "/")
        {
            // check if it's a rigid body
            bool rigidBodyEnabled = false;
            tempPrim.GetAttribute(pxr::TfToken("physics:rigidBodyEnabled")).Get(&rigidBodyEnabled);
            if (rigidBodyEnabled)
            {
                mParentPrim = tempPrim;
                return;
            }
            // go to parent
            tempPrim = tempPrim.GetParent();
        }

        // TODO: What to do if the parent prim is invalid aside from this error message?
        CARB_LOG_ERROR("Failed to updated contact sensor, parent prim is not found or invalid");
    }

    virtual void preTick()
    {
        return;
    }

    virtual void tick() = 0;

    // check
    virtual void onPhysicsStep(){};

    virtual void draw()
    {
        mLineDrawing->draw();
        mPointDrawing->draw();
    }

    virtual void onStop()
    {
    }

    virtual void clearDraw()
    {
        mLineDrawing->clear();
        mPointDrawing->clear();
        mLineDrawing->draw();
        mPointDrawing->draw();
    }

    bool getVisualize()
    {
        return mVisualize;
    }

protected:
    pxr::UsdPrim mParentPrim;
    bool mVisualize = true;
    std::shared_ptr<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper> mPointDrawing;
    std::shared_ptr<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper> mLineDrawing;
};
typedef IsaacSensorComponentBase<pxr::IsaacSensorIsaacBaseSensor> IsaacBaseSensorComponent;

}
}
}
