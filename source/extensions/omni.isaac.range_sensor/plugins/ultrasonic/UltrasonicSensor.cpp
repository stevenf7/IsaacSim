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

#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

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


void UltrasonicSensor::dumpData(double dt)
{
    mLastAzimuth.resize(mCols);
    mLastZenith.resize(mRows);

    std::copy(mAzimuth.begin(), mAzimuth.end(), mLastAzimuth.begin());
    std::copy(mZenith.begin(), mZenith.end(), mLastZenith.begin());

    for (auto& emitter : mEmitters)
    {
        std::copy(emitter.mDepth.begin(), emitter.mDepth.end(), emitter.mLastDepth.begin());
        std::copy(emitter.mHitPos.begin(), emitter.mHitPos.end(), emitter.mLastHitPos.begin());
        std::copy(emitter.mLinearDepth.begin(), emitter.mLinearDepth.end(), emitter.mLastLinearDepth.begin());
        std::copy(emitter.mIntensity.begin(), emitter.mIntensity.end(), emitter.mLastIntensity.begin());
    }
}


UltrasonicSensor::UltrasonicSensor(omni::physx::IPhysx* physxPtr, carb::fastcache::FastCache* fastCachePtr)
    : RangeSensorComponent(physxPtr, fastCachePtr),
      mMinDepth(mMinRange / mMetersPerUnit),
      mMaxDepth(mMaxRange / mMetersPerUnit),
      mRows(int(mVerticalFov / mVerticalResolution)),
      mCols(int(mHorizontalFov / mHorizontalResolution))
{

    mZenith.assign(mRows, 0.0f);
    mLastZenith.assign(mRows, 0.0f);
    mAzimuth.assign(mCols, 0.0f);
    mLastAzimuth.assign(mCols, 0.0f);

    // TODO: Move the emission timer into the emitter?
    mEmissionTimer.setEmitterDelay(0, 0.0);
    mEmissionTimer.setEmitterDelay(1, 0.3);
    mEmissionTimer.setEmitterDelay(2, 0.6);
    mEmissionTimer.setEmitterDelay(3, 0.0);
    mEmissionTimer.setEmitterDelay(4, 0.3);
    mEmissionTimer.setEmitterDelay(5, 0.6);
    mEmissionTimer.setEmitterDelay(6, 0.0);
    mEmissionTimer.setEmitterDelay(7, 0.3);
    mEmissionTimer.setEmitterDelay(8, 0.6);
    mEmissionTimer.setEmitterDelay(9, 0.0);
    mEmissionTimer.setEmitterDelay(10, 0.3);
    mEmissionTimer.setEmitterDelay(11, 0.6);

    // This is temporary, once we switch to the new schema, this will be from the list of relationships:
    for (size_t i = 0; i < NUM_EMITTERS; i++)
    {
        mEmitters.push_back(UltrasonicEmitter());
    }
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

void UltrasonicSensor::onComponentChange()
{

    RangeSensorComponent::onComponentChange();
    const pxr::RangeSensorSchemaUltrasonic& typedPrim = (pxr::RangeSensorSchemaUltrasonic)mPrim;


    if (typedPrim.GetHorizontalFovAttr().HasValue())
    {
        typedPrim.GetHorizontalFovAttr().Get(&mHorizontalFov);
    }

    if (typedPrim.GetVerticalFovAttr().HasValue())
    {
        typedPrim.GetVerticalFovAttr().Get(&mVerticalFov);
    }

    if (typedPrim.GetHorizontalResolutionAttr().HasValue())
    {
        typedPrim.GetHorizontalResolutionAttr().Get(&mHorizontalResolution);
    }

    if (typedPrim.GetVerticalResolutionAttr().HasValue())
    {
        typedPrim.GetVerticalResolutionAttr().Get(&mVerticalResolution);
    }

    if (typedPrim.GetMaxRangeAttr().HasValue())
    {
        typedPrim.GetMaxRangeAttr().Get(&mMaxDepth);
    }


    // we have to have atleast one beam so the FOV can never be smaller than resolution
    mHorizontalResolution = pxr::GfClamp(mHorizontalResolution, 0.005f, 1024);
    mHorizontalFov = pxr::GfClamp(mHorizontalFov, mHorizontalResolution, 360);

    mVerticalResolution = pxr::GfClamp(mVerticalResolution, 0.005f, 1024);
    mVerticalFov = pxr::GfClamp(mVerticalFov, mVerticalResolution, 360);

    mMaxStepSize = float(1.0 / 30.0);

    mCols = int(mHorizontalFov / mHorizontalResolution);
    mRows = int(mVerticalFov / mVerticalResolution);

    mZenith.assign(mRows, 0.0f);
    mLastZenith.assign(mRows, 0.0f);
    mAzimuth.assign(mCols, 0.0f);
    mLastAzimuth.assign(mCols, 0.0f);

    float startAzimuth = -0.5f * mHorizontalFov + mYawOffset;
    float startZenith = -0.5f * mVerticalFov;

    for (int col = 0; col < mCols; col++)
    {
        mAzimuth[col] = float((startAzimuth + col * mHorizontalResolution) * M_PI / 180.0f);
    }
    for (int row = 0; row < mRows; row++)
    {
        mZenith[row] = float((startZenith + row * mVerticalResolution) * M_PI / 180.0f);
    }
    mLastAzimuth.assign(mCols, 0.0f);
    // mLastCol = 0;
    mRemainingTime = 0.0f;

    // TODO: Temporary initialization step, will be moved to the emitter onComponentChange
    clampRangeBounds();
    updateDepthBounds();
    // calculate num
    for (auto& emitter : mEmitters)
    {
        emitter.initialize(NUM_BINS, mMaxDepth * mMetersPerUnit, mRows, mCols);
    }
}


void UltrasonicSensor::tick()
{
    if (!mPxScene)
    {
        CARB_LOG_ERROR("Physics Scene does not exist");
        return;
    }
    mEmissionTimer.update(mTimeDelta);

    carb::fastcache::Transform parentTrans;
    parentTrans.orientation = { 0, 0, 0, 1 };
    auto lidarLocalTrans = omni::usd::UsdUtils::getLocalTransformMatrix(mStage->GetPrimAtPath(mPrim.GetPath()));
    ::physx::PxVec3 origin = utils::conversions::asPxVec3(lidarLocalTrans.ExtractTranslation());
    ::physx::PxQuat theta0 = utils::conversions::asPxQuat(lidarLocalTrans.ExtractRotation().GetQuat());
    // Make sure the parent prim has a transform, otherwise use local transform from the lidar prim itself
    if (mParentPrim.IsA<pxr::UsdGeomXformable>())
    {
        mFastCachePtr->getTransform(mParentPrim.GetPath(), parentTrans);
        ::physx::PxQuat parentRot = utils::conversions::asPxQuat(parentTrans.orientation);
        origin = utils::conversions::asPxVec3(parentTrans.position) + parentRot.rotate(origin);
        theta0 = parentRot * theta0;
    }

    // TODO @markb: get separate debugLinesEmitter[i] for each sensor and combine into mDebugLines
    mDebugLines.clear();
    bool zUp = pxr::UsdGeomGetStageUpAxis(mStage) == pxr::UsdGeomTokens->z;

    std::vector<::physx::PxTransform> leftWedges;

    const ::physx::PxVec3& sensorXOffset = ::physx::PxVec3(25.f, 0.f, 0.f);
    const ::physx::PxVec3& sensorYOffset = ::physx::PxVec3(0.0f, 50.0f, 0.0f);

    if (mEmissionTimer.shouldEmit(0))
    {
        ::physx::PxQuat theta5 = theta0 * ::physx::PxQuat(::physx::PxPi * -0.2f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[0].scan_<false, true>(0, mCols, mRows, mCols, origin + sensorXOffset, theta5, mPhysx, mPxScene,
                                        mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(1))
    {
        ::physx::PxQuat theta6 = theta0 * ::physx::PxQuat(::physx::PxPi * -0.1f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[1].scan_<false, true>(0, mCols, mRows, mCols, origin + sensorXOffset + sensorYOffset, theta6, mPhysx,
                                        mPxScene, mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(2))
    {
        ::physx::PxQuat theta7 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.1f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[2].scan_<false, true>(0, mCols, mRows, mCols, origin + sensorXOffset + 2.f * sensorYOffset, theta7,
                                        mPhysx, mPxScene, mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(3))
    {
        ::physx::PxQuat theta8 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.2f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[3].scan_<false, true>(0, mCols, mRows, mCols, origin + sensorXOffset + 3.f * sensorYOffset, theta8,
                                        mPhysx, mPxScene, mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(4))
    {
        ::physx::PxQuat theta1 = theta0 * ::physx::PxQuat(::physx::PxPi * 1.2f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[4].scan_<false, true>(0, mCols, mRows, mCols, origin - sensorXOffset, theta1, mPhysx, mPxScene,
                                        mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(5))
    {
        ::physx::PxQuat theta2 = theta0 * ::physx::PxQuat(::physx::PxPi * 1.1f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[5].scan_<false, true>(0, mCols, mRows, mCols, origin - sensorXOffset + sensorYOffset, theta2, mPhysx,
                                        mPxScene, mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(6))
    {
        ::physx::PxQuat theta3 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.9f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[6].scan_<false, true>(0, mCols, mRows, mCols, origin - sensorXOffset + 2.f * sensorYOffset, theta3,
                                        mPhysx, mPxScene, mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(7))
    {
        ::physx::PxQuat theta4 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.8f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[7].scan_<false, true>(0, mCols, mRows, mCols, origin - sensorXOffset + 3.f * sensorYOffset, theta4,
                                        mPhysx, mPxScene, mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(8))
    {
        ::physx::PxQuat theta9 = theta0 * ::physx::PxQuat(::physx::PxPi * -0.45f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[8].scan_<false, true>(0, mCols, mRows, mCols, origin + 0.5 * sensorXOffset, theta9, mPhysx, mPxScene,
                                        mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(9))
    {
        ::physx::PxQuat theta10 = theta0 * ::physx::PxQuat(::physx::PxPi * -0.55f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[9].scan_<false, true>(0, mCols, mRows, mCols, origin + 0.5f * sensorXOffset, theta10, mPhysx,
                                        mPxScene, mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }
    if (mEmissionTimer.shouldEmit(10))
    {
        ::physx::PxQuat theta11 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.45f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[10].scan_<false, true>(0, mCols, mRows, mCols, origin + 0.5f * sensorXOffset + 3.f * sensorYOffset,
                                         theta11, mPhysx, mPxScene, mZenith, mAzimuth, mMaxDepth, mMinDepth,
                                         mMetersPerUnit, zUp);
    }
    if (mEmissionTimer.shouldEmit(11))
    {
        ::physx::PxQuat theta12 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.55f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[11].scan_<false, true>(0, mCols, mRows, mCols, origin + 0.5f * sensorXOffset + 3.f * sensorYOffset,
                                         theta12, mPhysx, mPxScene, mZenith, mAzimuth, mMaxDepth, mMinDepth,
                                         mMetersPerUnit, zUp);
    }

    for (auto& emitter : mEmitters)
    {
        mDebugLines.insert(mDebugLines.end(), emitter.mEmitterDebugLines.begin(), emitter.mEmitterDebugLines.end());
        // TODO move this to the emitter code?:
        emitter.mEmitterDebugLines.clear();
    }
    // mTimeDelta is from omni::isaac::utils::plugins::core::Component.h
    // it represents the delta_t since the last tick
    dumpData(mTimeDelta);
}


}
}
}
