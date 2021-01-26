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

#include "LidarSensor.h"
#include "../RangeSensorUtils.h"

#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>

#include <carb/InterfaceUtils.h>

#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

#include <iostream>

using namespace ::physx;
using namespace pxr;

namespace omni
{
namespace isaac
{
namespace range_sensor
{


LidarSensor::LidarSensor(omni::physx::IPhysx* physxPtr, carb::fastcache::FastCache* fastCachePtr)
    : RangeSensorComponent(physxPtr, fastCachePtr)
{
}

LidarSensor::~LidarSensor()
{
}

void LidarSensor::onStart()
{
    RangeSensorComponent::onStart();
}

void LidarSensor::onComponentChange()
{

    RangeSensorComponent::onComponentChange();

    const pxr::RangeSensorSchemaLidar& typedPrim = (pxr::RangeSensorSchemaLidar)mPrim;


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

    if (typedPrim.GetRotationRateAttr().HasValue())
    {
        typedPrim.GetRotationRateAttr().Get(&mRotationRate);
    }

    if (typedPrim.GetHighLodAttr().HasValue())
    {
        typedPrim.GetHighLodAttr().Get(&mHighLod);
    }
    if (typedPrim.GetYawOffsetAttr().HasValue())
    {
        typedPrim.GetYawOffsetAttr().Get(&mYawOffset);
    }


    // we have to have atleast one beam so the FOV can never be smaller than resolution
    mHorizontalResolution = pxr::GfClamp(mHorizontalResolution, 0.005f, 1024);
    mHorizontalFov = pxr::GfClamp(mHorizontalFov, mHorizontalResolution, 360);

    mVerticalResolution = pxr::GfClamp(mVerticalResolution, 0.005f, 1024);
    mVerticalFov = pxr::GfClamp(mVerticalFov, mVerticalResolution, 360);
    mRotationRate = pxr::GfClamp(mRotationRate, 0, 1024);
    mMinRange = pxr::GfClamp(mMinRange, 0, 1e9f);
    mMaxRange = pxr::GfClamp(mMaxRange, mMinRange, 1e9f);

    mMinDepth = mMinRange / mMetersPerUnit;
    mMaxDepth = mMaxRange / mMetersPerUnit;

    mMaxStepSize = float(1.0 / 30.0);

    mCols = int(mHorizontalFov / mHorizontalResolution);

    // Add one so that we have symmetry
    // Otherwise we are missing one angle for the Velodyne 16 case as 30/2 = 15
    mRows = mHighLod ? int(mVerticalFov / mVerticalResolution) + 1 : 1;

    if (mRotationRate != 0.0f && mRotationRate > 1.0 / mMaxStepSize)
        mRotationRate = float(1.0 / mMaxStepSize);


    mColScanSpeed = mCols * mRotationRate;
    mMaxColsPerTick = int(mColScanSpeed * mMaxStepSize);

    mDepth.assign(mRows * mCols, 0);
    mHitPos.assign(mRows * mCols, { 0, 0, 0 });
    mLinearDepth.assign(mRows * mCols, 0);

    mIntensity.assign(mRows * mCols, 0);
    mZenith.assign(mRows, 0.0f);
    mAzimuth.assign(mCols, 0.0f);

    float startAzimuth = -0.5f * mHorizontalFov + mYawOffset;
    float startZenith = -0.5f * mVerticalFov;

    for (int col = 0; col < mCols; col++)
        mAzimuth[col] = float((startAzimuth + col * mHorizontalResolution) * M_PI / 180.0f);

    for (int row = 0; row < mRows; row++)
        mZenith[row] = float((startZenith + row * mVerticalResolution) * M_PI / 180.0f);

    if (!mHighLod)
        mZenith[0] = 0.0f;

    mLastAzimuth.assign(mMaxColsPerTick, 0.0f);
    mLastDepth.assign(mRows * mMaxColsPerTick, 0);
    mLastLinearDepth.assign(mRows * mMaxColsPerTick, 0);
    mLastHitPos.assign(mRows * mCols, { 0, 0, 0 });
    mLastCol = 0;
    mLastNumColsTicked = 0;
    mRemainingTime = 0.0f;
}


bool raycastClosest(const ::physx::PxVec3& pos,
                    const ::physx::PxVec3& dir,
                    float distance,
                    ::physx::PxRaycastHit& hit,
                    ::physx::PxScene* physxScene)
{

    if (!physxScene)
    {
        return false;
    }
    // ::physx::PxRaycastHit hit;
    ::physx::PxHitFlags hitFlags = PxHitFlag::eDEFAULT | PxHitFlag::eMESH_BOTH_SIDES;

    const bool ret = ::physx::PxSceneQueryExt::raycastSingle(*physxScene, pos, dir, distance, hitFlags, hit);
    // if (ret)
    // {
    //     outHit.distance = hit.distance;
    //     outHit.normal = (const Float3&)hit.normal;
    //     outHit.position = (const Float3&)hit.position;
    //     outHit.faceIndex = hit.faceIndex;
    //     const InternalHandle shapeIndex = (InternalHandle)hit.shape->userData;
    //     const InternalHandle bodyIndex = (InternalHandle)hit.actor->userData;
    //     outHit.collision = shapeIndex < gInternalScene->getRecords().size() ?
    //                            gInternalScene->getRecords()[shapeIndex].mPrim.GetPath().GetText() :
    //                            nullptr;
    //     outHit.rigidBody = bodyIndex < gInternalScene->getRecords().size() ?
    //                            gInternalScene->getRecords()[bodyIndex].mPrim.GetPath().GetText() :
    //                            nullptr;
    // }
    return ret;
}
template <bool drawPoints, bool drawLines>
void scan(int start,
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
            bool hit = raycastClosest(origin + unitDir * minDepth, unitDir, maxDepth, raycastHit, physxScenePtr);

            if (hit)
            {
                // the distance of the ray should be from center of lidar
                depth[i] = static_cast<uint16_t>((raycastHit.distance + minDepth) * invMaxDepth * 65535.0f);
                linearDepth[i] = (raycastHit.distance + minDepth) * metersPerUnit; // in meters
                intensity[i] = 255;

                // if (linearDepth[i] < minDepth * metersPerUnit)
                // {
                //     depth[i] = 0;
                //     linearDepth[i] = minDepth * metersPerUnit; // in meters
                //     intensity[i] = 0;
                //     continue;
                // }
                carb::Float3 hitPos = { raycastHit.position.x, raycastHit.position.y, raycastHit.position.z };
                ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(raycastHit.position - origin);
                hitPosition[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z }; // relative to the sensor location
                if (drawPoints)
                {
                    omni::isaac::range_sensor::DebugData data;

                    ::physx::PxVec3 diff = raycastHit.position - origin;
                    // TODO: replace lines with dots.

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

void LidarSensor::dumpData(int start, int stop, double dt)
{

    // Size of mLastDepth and mLastIntensity == mRows * mLastNumColsTicked
    // Size of mDepth, and mIntensity == mRows * mCols
    // Size of mAzimuth == mCols
    // Size of mLastAzimuth == mLastNumColsTicked

    int colsToTick = stop - start;
    int unwrappedSize = std::min(stop, mCols) - start;
    int wrappedSize = std::max(0, stop - mCols);

    mLastDepth.resize(mRows * colsToTick);
    mLastHitPos.resize(mRows * colsToTick);
    mLastLinearDepth.resize(mRows * colsToTick);
    mLastIntensity.resize(mRows * colsToTick);
    mLastAzimuth.resize(colsToTick);

    std::copy(mAzimuth.begin() + start, mAzimuth.begin() + (start + unwrappedSize), mLastAzimuth.begin());
    std::copy(mDepth.begin() + start * mRows, mDepth.begin() + (start + unwrappedSize) * mRows, mLastDepth.begin());
    std::copy(mHitPos.begin() + start * mRows, mHitPos.begin() + (start + unwrappedSize) * mRows, mLastHitPos.begin());

    std::copy(mLinearDepth.begin() + start * mRows, mLinearDepth.begin() + (start + unwrappedSize) * mRows,
              mLastLinearDepth.begin());

    std::copy(mIntensity.begin() + start * mRows, mIntensity.begin() + (start + unwrappedSize) * mRows,
              mLastIntensity.begin());

    // We wrapped around
    if (wrappedSize > 0)
    {
        std::copy(mAzimuth.begin(), mAzimuth.begin() + wrappedSize, mLastAzimuth.begin() + unwrappedSize);
        std::copy(mDepth.begin(), mDepth.begin() + wrappedSize * mRows, mLastDepth.begin() + unwrappedSize * mRows);
        std::copy(mHitPos.begin(), mHitPos.begin() + wrappedSize * mRows, mLastHitPos.begin() + unwrappedSize * mRows);
        std::copy(mLinearDepth.begin(), mLinearDepth.begin() + wrappedSize * mRows,
                  mLastLinearDepth.begin() + unwrappedSize * mRows);
        std::copy(mIntensity.begin(), mIntensity.begin() + wrappedSize * mRows,
                  mLastIntensity.begin() + unwrappedSize * mRows);
    }
}


void LidarSensor::tick()
{
    if (!mPxScene)
    {
        CARB_LOG_ERROR("Physics Scene does not exist");
        return;
    }

    carb::fastcache::Transform parentTrans;
    parentTrans.orientation = { 0, 0, 0, 1 };
    auto lidarLocalTrans = omni::usd::UsdUtils::getLocalTransformMatrix(mStage->GetPrimAtPath(mPrim.GetPath()));
    ::physx::PxVec3 finalTranslation = utils::conversions::asPxVec3(lidarLocalTrans.ExtractTranslation());
    ::physx::PxQuat finalRotation = utils::conversions::asPxQuat(lidarLocalTrans.ExtractRotation().GetQuat());
    // Make sure the parent prim has a transform, otherwise use local transform from the lidar prim itself
    if (mParentPrim.IsA<pxr::UsdGeomXformable>())
    {
        mFastCachePtr->getTransform(mParentPrim.GetPath(), parentTrans);
        ::physx::PxQuat parentRot = utils::conversions::asPxQuat(parentTrans.orientation);
        finalTranslation = utils::conversions::asPxVec3(parentTrans.position) + parentRot.rotate(finalTranslation);
        finalRotation = parentRot * finalRotation;
    }

    double elapsedTime = mTimeDelta;
    mDebugLines.clear();
    bool zUp = pxr::UsdGeomGetStageUpAxis(mStage) == pxr::UsdGeomTokens->z;

    // Every tick does a full scan
    if (mRotationRate == 0.0f)
    {
        mLastNumColsTicked = mCols;
        if (mDrawLines)
        {
            scan<false, true>(0, mCols, mRows, mCols, finalTranslation, finalRotation, mPhysx, mPxScene, mDebugLines,
                              mDepth, mHitPos, mLinearDepth, mIntensity, mZenith, mAzimuth, mMaxDepth, mMinDepth,
                              mMetersPerUnit, zUp);
        }
        else if (mDrawPoints)
        {
            scan<true, false>(0, mCols, mRows, mCols, finalTranslation, finalRotation, mPhysx, mPxScene, mDebugLines,
                              mDepth, mHitPos, mLinearDepth, mIntensity, mZenith, mAzimuth, mMaxDepth, mMinDepth,
                              mMetersPerUnit, zUp);
        }
        else
        {
            scan<false, false>(0, mCols, mRows, mCols, finalTranslation, finalRotation, mPhysx, mPxScene, mDebugLines,
                               mDepth, mHitPos, mLinearDepth, mIntensity, mZenith, mAzimuth, mMaxDepth, mMinDepth,
                               mMetersPerUnit, zUp);
        }
        dumpData(0, mCols, elapsedTime);


        mLastCol = 0;
    }
    else
    {
        mRemainingTime += elapsedTime;
        mLastNumColsTicked = int(mColScanSpeed * mRemainingTime);

        // If too much time is remaining, cap the number of columns
        if (mLastNumColsTicked > mMaxColsPerTick)
        {
            mLastNumColsTicked = mMaxColsPerTick;
        }

        float simulateTime = mLastNumColsTicked / mColScanSpeed;
        mRemainingTime -= simulateTime;


        // In the case where we capped the number of columns, we drop from mRemainingTime
        // a multiple of mMaxStepSize
        mRemainingTime = std::fmod(mRemainingTime, mMaxStepSize);

        // Now scan the columns and dump the data
        if (mDrawLines)
        {
            scan<false, true>(mLastCol, mLastCol + mLastNumColsTicked, mRows, mCols, finalTranslation, finalRotation,
                              mPhysx, mPxScene, mDebugLines, mDepth, mHitPos, mLinearDepth, mIntensity, mZenith,
                              mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
        }
        else if (mDrawPoints)
        {
            scan<true, false>(mLastCol, mLastCol + mLastNumColsTicked, mRows, mCols, finalTranslation, finalRotation,
                              mPhysx, mPxScene, mDebugLines, mDepth, mHitPos, mLinearDepth, mIntensity, mZenith,
                              mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
        }
        else
        {
            scan<false, false>(mLastCol, mLastCol + mLastNumColsTicked, mRows, mCols, finalTranslation, finalRotation,
                               mPhysx, mPxScene, mDebugLines, mDepth, mHitPos, mLinearDepth, mIntensity, mZenith,
                               mAzimuth, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
        }
        dumpData(mLastCol, mLastCol + mLastNumColsTicked, simulateTime);

        mLastCol = (mLastCol + mLastNumColsTicked) % mCols;
    }
}


}
}
}
