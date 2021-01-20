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
    for (size_t i = 0; i < NUM_EMITTERS; i++)
    {
        mLastDepth[i].resize(mRows * mCols);
        mLastHitPos[i].resize(mRows * mCols);
        mLastLinearDepth[i].resize(mRows * mCols);
        mLastIntensity[i].resize(mRows * mCols);
    }
    mLastAzimuth.resize(mCols);
    mLastZenith.resize(mRows);

    std::copy(mAzimuth.begin(), mAzimuth.end(), mLastAzimuth.begin());
    std::copy(mZenith.begin(), mZenith.end(), mLastZenith.begin());
    std::copy(mDepth.begin(), mDepth.end(), mLastDepth.begin());
    for (size_t i = 0; i < mHitPos.size(); i++)
    {
        std::copy(mHitPos[i].begin(), mHitPos[i].end(), mLastHitPos[i].begin());
    }
    for (size_t i = 0; i < mLinearDepth.size(); i++)
    {
        std::copy(mLinearDepth[i].begin(), mLinearDepth[i].end(), mLastLinearDepth[i].begin());
    }
    for (size_t i = 0; i < mIntensity.size(); i++)
    {
        std::copy(mIntensity[i].begin(), mIntensity[i].end(), mLastIntensity[i].begin());
    }
}


UltrasonicSensor::UltrasonicSensor(omni::physx::IPhysx* physxPtr, carb::fastcache::FastCache* fastCachePtr)
    : RangeSensorComponent(physxPtr, fastCachePtr),
      mMinDepth(mMinRange / mMetersPerUnit),
      mMaxDepth(mMaxRange / mMetersPerUnit),
      mRows(int(mVerticalFov / mVerticalResolution)),
      mCols(int(mHorizontalFov / mHorizontalResolution)),
      mLinearDepth(NUM_EMITTERS, std::vector<float>(mRows * mCols, 0)),
      mLastLinearDepth(NUM_EMITTERS, std::vector<float>(mRows * mCols, 0)),
      mIntensity(NUM_EMITTERS, std::vector<uint8_t>(mRows * mCols, 0)),
      mLastIntensity(NUM_EMITTERS, std::vector<uint8_t>(mRows * mCols, 0)),
      mDepth(NUM_EMITTERS, std::vector<uint16_t>(mRows * mCols, 0)),
      mLastDepth(NUM_EMITTERS, std::vector<uint16_t>(mRows * mCols, 0)),
      mHitPos(NUM_EMITTERS, std::vector<carb::Float3>(mRows * mCols, { 0, 0, 0 })),
      mLastHitPos(NUM_EMITTERS, std::vector<carb::Float3>(mRows * mCols, { 0, 0, 0 })),
      mEnvelope(std::vector<USSEnvelope>(NUM_EMITTERS, USSEnvelope(NUM_BINS, mMaxDepth))),
      mEmitterDebugLines(NUM_EMITTERS, std::vector<DebugData>())
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

    // we have to have atleast one beam so the FOV can never be smaller than resolution
    mHorizontalResolution = pxr::GfClamp(mHorizontalResolution, 0.005f, 1024);
    mHorizontalFov = pxr::GfClamp(mHorizontalFov, mHorizontalResolution, 360);

    mVerticalResolution = pxr::GfClamp(mVerticalResolution, 0.005f, 1024);
    mVerticalFov = pxr::GfClamp(mVerticalFov, mVerticalResolution, 360);

    clampRangeBounds();
    updateDepthBounds();

    mMaxStepSize = float(1.0 / 30.0);

    mCols = int(mHorizontalFov / mHorizontalResolution);
    mRows = int(mVerticalFov / mVerticalResolution);

    for (size_t i = 0; i < mLinearDepth.size(); i++)
    {
        mLinearDepth[i].assign(mRows * mCols, 0);
        mLastLinearDepth[i].assign(mRows * mCols, 0);
        mIntensity[i].assign(mRows * mCols, 0);
        mLastIntensity[i].assign(mRows * mCols, 0);
        mDepth[i].assign(mRows * mCols, 0);
        mLastDepth[i].assign(mRows * mCols, 0);
        mHitPos[i].assign(mRows * mCols, { 0, 0, 0 });
        mLastHitPos[i].assign(mRows * mCols, { 0, 0, 0 });
    }

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
                                        mEmitterDebugLines[0], mDepth[0], mHitPos[0], mLinearDepth[0], mIntensity[0],
                                        mEnvelope[0], mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(1))
    {
        ::physx::PxQuat theta6 = theta0 * ::physx::PxQuat(::physx::PxPi * -0.1f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[1].scan_<false, true>(0, mCols, mRows, mCols, origin + sensorXOffset + sensorYOffset, theta6, mPhysx,
                                        mPxScene, mEmitterDebugLines[1], mDepth[1], mHitPos[1], mLinearDepth[1],
                                        mIntensity[1], mEnvelope[1], mZenith, mAzimuth, mMaxDepth, mMinDepth,
                                        mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(2))
    {
        ::physx::PxQuat theta7 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.1f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[2].scan_<false, true>(0, mCols, mRows, mCols, origin + sensorXOffset + 2.f * sensorYOffset, theta7,
                                        mPhysx, mPxScene, mEmitterDebugLines[2], mDepth[2], mHitPos[2], mLinearDepth[2],
                                        mIntensity[2], mEnvelope[2], mZenith, mAzimuth, mMaxDepth, mMinDepth,
                                        mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(3))
    {
        ::physx::PxQuat theta8 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.2f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[3].scan_<false, true>(0, mCols, mRows, mCols, origin + sensorXOffset + 3.f * sensorYOffset, theta8,
                                        mPhysx, mPxScene, mEmitterDebugLines[3], mDepth[3], mHitPos[3], mLinearDepth[3],
                                        mIntensity[3], mEnvelope[3], mZenith, mAzimuth, mMaxDepth, mMinDepth,
                                        mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(4))
    {
        ::physx::PxQuat theta1 = theta0 * ::physx::PxQuat(::physx::PxPi * 1.2f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[4].scan_<false, true>(0, mCols, mRows, mCols, origin - sensorXOffset, theta1, mPhysx, mPxScene,
                                        mEmitterDebugLines[4], mDepth[4], mHitPos[4], mLinearDepth[4], mIntensity[4],
                                        mEnvelope[4], mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(5))
    {
        ::physx::PxQuat theta2 = theta0 * ::physx::PxQuat(::physx::PxPi * 1.1f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[5].scan_<false, true>(0, mCols, mRows, mCols, origin - sensorXOffset + sensorYOffset, theta2, mPhysx,
                                        mPxScene, mEmitterDebugLines[5], mDepth[5], mHitPos[5], mLinearDepth[5],
                                        mIntensity[5], mEnvelope[5], mZenith, mAzimuth, mMaxDepth, mMinDepth,
                                        mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(6))
    {
        ::physx::PxQuat theta3 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.9f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[6].scan_<false, true>(0, mCols, mRows, mCols, origin - sensorXOffset + 2.f * sensorYOffset, theta3,
                                        mPhysx, mPxScene, mEmitterDebugLines[6], mDepth[6], mHitPos[6], mLinearDepth[6],
                                        mIntensity[6], mEnvelope[6], mZenith, mAzimuth, mMaxDepth, mMinDepth,
                                        mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(7))
    {
        ::physx::PxQuat theta4 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.8f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[7].scan_<false, true>(0, mCols, mRows, mCols, origin - sensorXOffset + 3.f * sensorYOffset, theta4,
                                        mPhysx, mPxScene, mEmitterDebugLines[7], mDepth[7], mHitPos[7], mLinearDepth[7],
                                        mIntensity[7], mEnvelope[7], mZenith, mAzimuth, mMaxDepth, mMinDepth,
                                        mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(8))
    {
        ::physx::PxQuat theta9 = theta0 * ::physx::PxQuat(::physx::PxPi * -0.45f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[8].scan_<false, true>(0, mCols, mRows, mCols, origin + 0.5 * sensorXOffset, theta9, mPhysx, mPxScene,
                                        mEmitterDebugLines[8], mDepth[8], mHitPos[8], mLinearDepth[8], mIntensity[8],
                                        mEnvelope[8], mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (mEmissionTimer.shouldEmit(9))
    {
        ::physx::PxQuat theta10 = theta0 * ::physx::PxQuat(::physx::PxPi * -0.55f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[9].scan_<false, true>(0, mCols, mRows, mCols, origin + 0.5f * sensorXOffset, theta10, mPhysx, mPxScene,
                                        mEmitterDebugLines[9], mDepth[9], mHitPos[9], mLinearDepth[9], mIntensity[9],
                                        mEnvelope[9], mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }
    if (mEmissionTimer.shouldEmit(10))
    {
        ::physx::PxQuat theta11 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.45f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[10].scan_<false, true>(0, mCols, mRows, mCols, origin + 0.5f * sensorXOffset + 3.f * sensorYOffset,
                                         theta11, mPhysx, mPxScene, mEmitterDebugLines[10], mDepth[10], mHitPos[10],
                                         mLinearDepth[10], mIntensity[10], mEnvelope[10], mZenith, mAzimuth, mMaxDepth,
                                         mMinDepth, mMetersPerUnit, zUp);
    }
    if (mEmissionTimer.shouldEmit(11))
    {
        ::physx::PxQuat theta12 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.55f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mEmitters[11].scan_<false, true>(0, mCols, mRows, mCols, origin + 0.5f * sensorXOffset + 3.f * sensorYOffset,
                                         theta12, mPhysx, mPxScene, mEmitterDebugLines[11], mDepth[11], mHitPos[11],
                                         mLinearDepth[11], mIntensity[11], mEnvelope[11], mZenith, mAzimuth, mMaxDepth,
                                         mMinDepth, mMetersPerUnit, zUp);
    }

    for (size_t i = 0; i < mEmitterDebugLines.size(); i++)
    {
        mDebugLines.insert(mDebugLines.end(), mEmitterDebugLines[i].begin(), mEmitterDebugLines[i].end());
        mEmitterDebugLines[i].clear();
    }
    // mTimeDelta is from omni::isaac::utils::plugins::core::Component.h
    // it represents the delta_t since the last tick
    dumpData(mTimeDelta);
}


}
}
}
