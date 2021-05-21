// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "DRComponentBase.h"

#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <drSchema/baseComponent.h>
#include <drSchema/transformComponent.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>

#include <functional>
#include <random>


namespace omni
{
namespace isaac
{
namespace dr
{

class DRComponentTransform : public DRComponentBase<pxr::DrSchemaBaseComponent>
{
public:
    DRComponentTransform(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr,
                         omni::renderer::IDebugDraw* debugDrawPtr);
    ~DRComponentTransform();
    virtual void initialize(const pxr::DrSchemaTransformComponent& prim, pxr::UsdStageWeakPtr stage);
    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();

private:
    void update();
    void stop();
    pxr::GfVec3f randomPointTriangle(std::vector<pxr::GfVec3f>& samplePoints);
    pxr::GfVec3f randomPointPolygon(std::vector<pxr::GfVec3f>& samplePoints);
    bool checkOverlap(pxr::GfRange3d inputRange);

    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr;
    std::vector<std::string> mPaths, mLookAtTargetPaths, mExcludedTargetPaths;
    pxr::GfVec3f mTranslateMin, mTranslateMax, mRotateMin, mRotateMax, mScaleMin, mScaleMax;
    std::vector<pxr::UsdPrim> mAllPrims;
    bool mEnableLookAtTarget, mDrawPolygon, mEnableSequentialBehavior, mCombineRandomRange;
    pxr::GfVec3d mLookAtTargetOffset = pxr::GfVec3d(0.0, 0.0, 0.0);
    pxr::GfVec3d mExcludedTargetOffset = pxr::GfVec3d(0.0, 0.0, 0.0);
    pxr::GfVec3d mUpUsd;
    std::vector<pxr::GfVec3f> mPolygonPoints, mTargetPoints, mLookAtTargetPoints;
    std::vector<pxr::GfVec3f> mPointInstancersTranslate, mPointInstancersOrient;
    omni::renderer::IDebugDraw* mDebugDrawPtr;
    unsigned int mSequentialIndex = 0;
};

}
}
}
