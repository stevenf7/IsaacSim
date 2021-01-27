// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
// clang-format on

#include "UltrasonicSensor.h"
#include "USSEnvelope.h"

#include "../RangeSensorUtils.h"


#include <carb/InterfaceUtils.h>


#include <string>
#include <sstream>
#include <iostream>

using namespace ::physx;
using namespace pxr;

namespace omni
{
namespace isaac
{
namespace range_sensor
{


UltrasonicSensor::UltrasonicSensor(omni::physx::IPhysx* physxPtr, carb::fastcache::FastCache* fastCachePtr)
    : RangeSensorComponent(physxPtr, fastCachePtr)
{
}

UltrasonicSensor::~UltrasonicSensor()
{
}

void UltrasonicSensor::onStart()
{
    RangeSensorComponent::onStart();
}

void UltrasonicSensor::clampRangeBounds()
{
    mMinRange = pxr::GfClamp(mMinRange, 0, 1e9f);
    mMaxRange = pxr::GfClamp(mMaxRange, mMinRange, 1e9f);
}

void UltrasonicSensor::updateDepthBounds()
{
    mMinDepth = mMinRange / mMetersPerUnit;
    mMaxDepth = mMaxRange / mMetersPerUnit;
}

int getNearestInt(float input)
{
    // The number is close to an integer round
    if (abs(input - round(input)) <= 1e-5)
    {
        return static_cast<int>(round(input));
    }
    // The number is not close to an integer, cast normally
    else
    {
        return static_cast<int>(input);
    }
}

void UltrasonicSensor::onComponentChange()
{

    RangeSensorComponent::onComponentChange();
    const pxr::RangeSensorSchemaUltrasonicArray& typedPrim = (pxr::RangeSensorSchemaUltrasonicArray)mPrim;

    isaac::utils::safeGetAttribute(typedPrim.GetHorizontalFovAttr(), mHorizontalFov);
    isaac::utils::safeGetAttribute(typedPrim.GetVerticalFovAttr(), mVerticalFov);
    isaac::utils::safeGetAttribute(typedPrim.GetHorizontalResolutionAttr(), mHorizontalResolution);
    isaac::utils::safeGetAttribute(typedPrim.GetVerticalResolutionAttr(), mVerticalResolution);

    isaac::utils::safeGetAttribute(typedPrim.GetNumBinsAttr(), mNumBins);

    isaac::utils::safeGetAttribute(typedPrim.GetPulseDurationAttr(), mPulseDuration);
    isaac::utils::safeGetAttribute(typedPrim.GetPulseGapDeltaAttr(), mPulseGapDelta);

    // we have to have atleast one beam so the FOV can never be smaller than resolution
    mHorizontalResolution = pxr::GfClamp(mHorizontalResolution, 0.005f, 1024);
    mHorizontalFov = pxr::GfClamp(mHorizontalFov, mHorizontalResolution, 360);

    mVerticalResolution = pxr::GfClamp(mVerticalResolution, 0.005f, 1024);
    mVerticalFov = pxr::GfClamp(mVerticalFov, mVerticalResolution, 360);

    // Use this instead of int casting because for cases like 30/.3 we get 99.9999 which if cast to int becomes 99
    mCols = getNearestInt(mHorizontalFov / mHorizontalResolution);
    mRows = getNearestInt(mVerticalFov / mVerticalResolution);

    mZenith.resize(mRows);
    mAzimuth.resize(mCols);

    float startAzimuth = -0.5f * mHorizontalFov;
    float startZenith = -0.5f * mVerticalFov;

    for (int col = 0; col < mCols; col++)
    {
        mAzimuth[col] = float((startAzimuth + col * mHorizontalResolution) * M_PI / 180.0f);
    }
    for (int row = 0; row < mRows; row++)
    {
        mZenith[row] = float((startZenith + row * mVerticalResolution) * M_PI / 180.0f);
    }

    clampRangeBounds();
    updateDepthBounds();


    pxr::SdfPathVector targets;
    typedPrim.GetEmitterPrimsRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        return;
    }

    mEmissionTimer = std::make_unique<UltrasonicArrayEmissionTimer>(targets.size(), mPulseGapDelta, mPulseDuration);
    mEmitters.resize(targets.size());
    for (size_t i = 0; i < targets.size(); i++)
    {
        pxr::UsdPrim prim = mStage->GetPrimAtPath(targets[i]);
        if (prim.IsA<pxr::RangeSensorSchemaUltrasonicEmitter>())
        {
            const pxr::RangeSensorSchemaUltrasonicEmitter& typedPrim = (pxr::RangeSensorSchemaUltrasonicEmitter)prim;
            mEmitters[i] = UltrasonicEmitter();
            mEmitters[i].initialize(typedPrim, mStage, mNumBins, mMaxDepth * mMetersPerUnit, mRows, mCols);
            mEmissionTimer->setEmitterDelay(i, mEmitters[i].mFiringDelay);
        }
    }
}


void UltrasonicSensor::tick()
{
    if (!mPxScene)
    {
        CARB_LOG_ERROR("Physics Scene does not exist");
        return;
    }
    mEmissionTimer->update(mTimeDelta);


    for (size_t i = 0; i < mEmitters.size(); i++)
    {


        if (mEmissionTimer->shouldEmit(i))
        {

            mEmitters[i].doScan(mFastCachePtr, mPhysx, mPxScene, mZenith, mAzimuth, mMaxDepth, mMinDepth);
        }
    }

    mDebugLines.clear();
    for (auto& emitter : mEmitters)
    {
        mDebugLines.insert(mDebugLines.end(), emitter.mEmitterDebugLines.begin(), emitter.mEmitterDebugLines.end());
        // TODO move this to the emitter code?:
        emitter.mEmitterDebugLines.clear();
    }
}
void UltrasonicSensor::onEmitterChange(const pxr::UsdPrim& prim)
{
    for (auto& emitter : mEmitters)
    {
        if (emitter.getPrim().GetPrim() == prim)
        {
            emitter.onComponentChange();
        }
    }
}

}
}
}
