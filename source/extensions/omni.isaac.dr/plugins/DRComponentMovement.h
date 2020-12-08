// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "DRComponentBase.h"

#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <drSchema/baseComponent.h>
#include <drSchema/movementComponent.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>

#include <functional>
#include <random>


namespace omni
{
namespace isaac
{
namespace dr
{

class DRComponentMovement : public DRComponentBase<pxr::DrSchemaBaseComponent>
{
public:
    DRComponentMovement(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);
    ~DRComponentMovement();
    virtual void initialize(const pxr::DrSchemaMovementComponent& prim, pxr::UsdStageWeakPtr stage);
    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();

private:
    void update();
    void stop();
    pxr::GfVec3f randomPointTriangle(std::vector<pxr::GfVec3f>& samplePoints);
    pxr::GfVec3f randomPointPolygon(std::vector<pxr::GfVec3f>& samplePoints);

    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr;
    std::vector<std::string> mPaths, mLookAtTargetPaths;
    pxr::GfVec2f mXRange, mYRange, mZRange;
    std::vector<pxr::UsdPrim> mAllPrims;
    bool mEnableLookAtTarget;
    pxr::GfVec3d mLookAtTargetOffset = pxr::GfVec3d(0.0, 0.0, 0.0);
    pxr::GfVec3d mUpUsd;
    std::vector<pxr::GfVec3f> mPolygonPoints;
};

}
}
}
