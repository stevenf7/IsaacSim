// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
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
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>

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


bool raycast(const ::physx::PxVec3& pos,
             const ::physx::PxVec3& dir,
             float distance,
             ::physx::PxRaycastHit& hit,
             ::physx::PxScene* physxScene)
{

    if (!physxScene)
    {
        return false;
    }

    ::physx::PxHitFlags hitFlags = PxHitFlag::eDEFAULT | PxHitFlag::eMESH_BOTH_SIDES;
    const bool ret = ::physx::PxSceneQueryExt::raycastSingle(*physxScene, pos, dir, distance, hitFlags, hit);
    return ret;
}


template <bool drawPoints, bool drawLines>
void scan_(int start,
           int stop,
           int rows,
           int cols,
           const ::physx::PxVec3& origin,
           const ::physx::PxQuat& worldRotation,
           omni::physx::IPhysx* physxPtr,
           ::physx::PxScene* physxScenePtr,
           std::vector<omni::isaac::range_sensor::DebugData>& debugLines,
           std::vector<uint16_t>& depth,
           std::vector<carb::Float3>& hitPosition,
           std::vector<float>& linearDepth,
           std::vector<uint8_t>& intensity,
           std::vector<float>& zenith,
           std::vector<float>& azimuth,
           float maxDepth,
           float minDepth,
           float metersPerUnit,
           bool zUp)
{

    int i = start * rows;
    int j = start;
    float invMaxDepth = 1.0f / maxDepth;
    // This isn't correct because the same prim (like carter) would have a different lidar axis if it was in a Y up vs Z
    // up stage. So commented this out and using the pure Z up rotation version
    // ::physx::PxVec3 azimuthDir = zUp ? ::physx::PxVec3(0.0f, 0.0f, 1.0f) : ::physx::PxVec3(0.0f, 1.0f, 0.0f);
    // ::physx::PxVec3 zenithDir = zUp ? ::physx::PxVec3(0.0f, 1.0f, 0.0f) : ::physx::PxVec3(0.0f, 0.0f, 1.0f);

    ::physx::PxVec3 azimuthDir = ::physx::PxVec3(0.0f, 0.0f, 1.0f);
    ::physx::PxVec3 zenithDir = ::physx::PxVec3(0.0f, 1.0f, 0.0f);

    for (int colPreMod = start; colPreMod < stop; colPreMod++)
    {
        int col = colPreMod % cols;
        ::physx::PxQuat mainrot = worldRotation * ::physx::PxQuat(azimuth[col], azimuthDir);

        for (int row = 0; row < rows; row++)
        {
            // Pitch then yaw
            ::physx::PxQuat rot = mainrot * ::physx::PxQuat(zenith[row], zenithDir);
            ::physx::PxVec3 unitDir = rot.rotate(::physx::PxVec3(1.0f, 0.0f, 0.0f)).getNormalized();
            ::physx::PxRaycastHit raycastHit;
            // Project the start point out to prevent collisions from origin
            bool hit = raycast(origin + unitDir * minDepth, unitDir, maxDepth, raycastHit, physxScenePtr);

            if (hit)
            {
                // the distance of the ray should be from center of lidar
                depth[i] = static_cast<uint16_t>((raycastHit.distance + minDepth) * invMaxDepth * 65535.0f);
                linearDepth[i] = (raycastHit.distance + minDepth) * metersPerUnit; // in meters
                intensity[i] = 255;
                carb::Float3 hitPos = { raycastHit.position.x, raycastHit.position.y, raycastHit.position.z };
                ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(raycastHit.position - origin);
                hitPosition[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z }; // relative to the sensor location
                if (drawPoints)
                {
                    omni::isaac::range_sensor::DebugData data;

                    ::physx::PxVec3 diff = raycastHit.position - origin;

                    data.startPos = hitPos;
                    auto temp = raycastHit.position - diff.getNormalized();
                    data.endPos = { temp.x, temp.y, temp.z };
                    // set ratio for color.  should be zero at minDepth and unity at maxDepth
                    auto ratio = (linearDepth[i] - minDepth * metersPerUnit) / ((maxDepth - minDepth) * metersPerUnit);
                    data.color = dist_to_color(ratio, true);
                    debugLines.push_back(data);
                }

                if (drawLines)
                {
                    omni::isaac::range_sensor::DebugData data;

                    ::physx::PxVec3 diff = raycastHit.position - origin;
                    auto temp = origin + diff.getNormalized() * minDepth;
                    data.startPos = { temp.x, temp.y, temp.z };
                    data.endPos = hitPos;
                    // set ratio for color.  should be zero at minDepth and unity at maxDepth
                    auto ratio = (linearDepth[i] - minDepth * metersPerUnit) / ((maxDepth - minDepth) * metersPerUnit);
                    data.color = dist_to_color(ratio, true);
                    debugLines.push_back(data);
                }
            }
            else
            {
                depth[i] = 65535;
                linearDepth[i] = maxDepth * metersPerUnit; // in meters
                intensity[i] = 0;
                ::physx::PxVec3 hitPos = origin + unitDir * (maxDepth + minDepth);
                ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(hitPos - origin);
                hitPosition[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z };
                if (drawPoints)
                {

                    omni::isaac::range_sensor::DebugData data;

                    ::physx::PxVec3 diff = hitPos - origin;
                    // TODO: replace lines with dots.

                    data.startPos = { hitPos.x, hitPos.y, hitPos.z };
                    auto temp = hitPos - diff.getNormalized();
                    data.endPos = { temp.x, temp.y, temp.z };
                    data.color = 255 + (255 << 8) + (255 << 16) + (255 << 24);
                    debugLines.push_back(data);
                }

                if (drawLines)
                {
                    omni::isaac::range_sensor::DebugData data;

                    auto temp = origin + unitDir * minDepth;
                    data.startPos = { temp.x, temp.y, temp.z };
                    data.endPos = { hitPos.x, hitPos.y, hitPos.z };
                    data.color = 255 + (255 << 8) + (255 << 16) + (50 << 24);
                    debugLines.push_back(data);
                }
            }

            if (zenith[row] == 0.0f)
                ++j %= cols;
            ++i %= (cols * rows);
        }
    }
}


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
      mEmitterDebugLines(NUM_EMITTERS, std::vector<DebugData>())
{

    mZenith.assign(mRows, 0.0f);
    mLastZenith.assign(mRows, 0.0f);
    mAzimuth.assign(mCols, 0.0f);
    mLastAzimuth.assign(mCols, 0.0f);

    emitter.setEmitterDelay(0, 0.0);
    emitter.setEmitterDelay(1, 0.3);
    emitter.setEmitterDelay(2, 0.6);
    emitter.setEmitterDelay(3, 0.0);
    emitter.setEmitterDelay(4, 0.3);
    emitter.setEmitterDelay(5, 0.6);
    emitter.setEmitterDelay(6, 0.0);
    emitter.setEmitterDelay(7, 0.3);
}

UltrasonicSensor::~UltrasonicSensor()
{
}

void UltrasonicSensor::onStart()
{
    RangeSensorComponent::onStart();
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

    mMinRange = pxr::GfClamp(mMinRange, 0, 1e9f);
    mMaxRange = pxr::GfClamp(mMaxRange, mMinRange, 1e9f);

    mMinDepth = mMinRange / mMetersPerUnit;
    mMaxDepth = mMaxRange / mMetersPerUnit;

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
    emitter.update(mTimeDelta);

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

    if (emitter.shouldEmit(0))
    {
        ::physx::PxQuat theta5 = theta0 * ::physx::PxQuat(::physx::PxPi * -0.2f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        scan_<false, true>(0, mCols, mRows, mCols, origin + sensorXOffset, theta5, mPhysx, mPxScene,
                           mEmitterDebugLines[0], mDepth[0], mHitPos[0], mLinearDepth[0], mIntensity[0], mZenith,
                           mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (emitter.shouldEmit(1))
    {
        ::physx::PxQuat theta6 = theta0 * ::physx::PxQuat(::physx::PxPi * -0.1f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        scan_<false, true>(0, mCols, mRows, mCols, origin + sensorXOffset + sensorYOffset, theta6, mPhysx, mPxScene,
                           mEmitterDebugLines[1], mDepth[1], mHitPos[1], mLinearDepth[1], mIntensity[1], mZenith,
                           mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (emitter.shouldEmit(2))
    {
        ::physx::PxQuat theta7 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.1f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        scan_<false, true>(0, mCols, mRows, mCols, origin + sensorXOffset + 2.f * sensorYOffset, theta7, mPhysx,
                           mPxScene, mEmitterDebugLines[2], mDepth[2], mHitPos[2], mLinearDepth[2], mIntensity[2],
                           mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (emitter.shouldEmit(3))
    {
        ::physx::PxQuat theta8 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.2f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        scan_<false, true>(0, mCols, mRows, mCols, origin + sensorXOffset + 3.f * sensorYOffset, theta8, mPhysx,
                           mPxScene, mEmitterDebugLines[3], mDepth[3], mHitPos[3], mLinearDepth[3], mIntensity[3],
                           mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (emitter.shouldEmit(4))
    {
        ::physx::PxQuat theta1 = theta0 * ::physx::PxQuat(::physx::PxPi * 1.2f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        scan_<false, true>(0, mCols, mRows, mCols, origin - sensorXOffset, theta1, mPhysx, mPxScene,
                           mEmitterDebugLines[4], mDepth[4], mHitPos[4], mLinearDepth[4], mIntensity[4], mZenith,
                           mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (emitter.shouldEmit(5))
    {
        ::physx::PxQuat theta2 = theta0 * ::physx::PxQuat(::physx::PxPi * 1.1f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        scan_<false, true>(0, mCols, mRows, mCols, origin - sensorXOffset + sensorYOffset, theta2, mPhysx, mPxScene,
                           mEmitterDebugLines[5], mDepth[5], mHitPos[5], mLinearDepth[5], mIntensity[5], mZenith,
                           mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (emitter.shouldEmit(6))
    {
        ::physx::PxQuat theta3 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.9f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        scan_<false, true>(0, mCols, mRows, mCols, origin - sensorXOffset + 2.f * sensorYOffset, theta3, mPhysx,
                           mPxScene, mEmitterDebugLines[6], mDepth[6], mHitPos[6], mLinearDepth[6], mIntensity[6],
                           mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
    }

    if (emitter.shouldEmit(7))
    {
        ::physx::PxQuat theta4 = theta0 * ::physx::PxQuat(::physx::PxPi * 0.8f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        scan_<false, true>(0, mCols, mRows, mCols, origin - sensorXOffset + 3.f * sensorYOffset, theta4, mPhysx,
                           mPxScene, mEmitterDebugLines[7], mDepth[7], mHitPos[7], mLinearDepth[7], mIntensity[7],
                           mZenith, mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
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
