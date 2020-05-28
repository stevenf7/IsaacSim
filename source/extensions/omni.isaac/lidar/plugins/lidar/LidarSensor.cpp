// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
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

#include <carb/physx/physx.h>
#include <carb/InterfaceUtils.h>
// #include <carb/filesystem/IFileSystem.h>

#include <PhysicsSchema/physicsScene.h>

// #include <omni/usd/UsdUtils.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>
using namespace physx;
using namespace pxr;

namespace omni
{
namespace isaac
{
namespace lidar
{


LidarSensor::LidarSensor()
{
}

LidarSensor::~LidarSensor()
{
    mDebugLines.clear();
}

void LidarSensor::initialize(carb::physics::PhysX* physxPtr,
                             carb::fastcache::FastCache* fastCachePtr,
                             const pxr::LidarSchemaLidar& prim,
                             pxr::UsdStageWeakPtr stage)
{
    SensorComponent::initialize(prim, stage);
    mPhysx = physxPtr;
    mFastCachePtr = fastCachePtr;
}


void LidarSensor::onStart()
{
    onComponentChange();

    pxr::UsdPrimRange range = mStage->Traverse();

    mPxScene = nullptr;
    for (pxr::UsdPrimRange::iterator iter = range.begin(); iter != range.end(); ++iter)
    {
        pxr::UsdPrim prim = *iter;

        if (prim.IsA<pxr::PhysicsSchemaPhysicsScene>())
        {

            mPxScene = static_cast<physx::PxScene*>(mPhysx->getPhysXPtr(prim.GetPrimPath(), carb::physics::ePTScene));

            if (mPxScene)
            {
                break;
            }
        }
    }
}

void LidarSensor::onComponentChange()
{
    mParentPrim = mStage->GetPrimAtPath(mPrim.GetPath()).GetParent();

    SensorComponent::onComponentChange();
    mMetersPerUnit = UsdGeomGetStageMetersPerUnit(mStage);

    if (mPrim.GetHorizontalFovAttr().HasValue())
    {
        mPrim.GetHorizontalFovAttr().Get(&mHorizontalFov);
    }

    if (mPrim.GetVerticalFovAttr().HasValue())
    {
        mPrim.GetVerticalFovAttr().Get(&mVerticalFov);
    }

    if (mPrim.GetRotationRateAttr().HasValue())
    {
        mPrim.GetRotationRateAttr().Get(&mRotationRate);
    }

    if (mPrim.GetHorizontalResolutionAttr().HasValue())
    {
        mPrim.GetHorizontalResolutionAttr().Get(&mHorizontalResolution);
    }

    if (mPrim.GetVerticalResolutionAttr().HasValue())
    {
        mPrim.GetVerticalResolutionAttr().Get(&mVerticalResolution);
    }

    if (mPrim.GetMinRangeAttr().HasValue())
    {
        mPrim.GetMinRangeAttr().Get(&mMinRange);
    }

    if (mPrim.GetMaxRangeAttr().HasValue())
    {
        mPrim.GetMaxRangeAttr().Get(&mMaxRange);
    }

    if (mPrim.GetHighLodAttr().HasValue())
    {
        mPrim.GetHighLodAttr().Get(&mHighLod);
    }

    if (mPrim.GetDrawLidarPointsAttr().HasValue())
    {
        mPrim.GetDrawLidarPointsAttr().Get(&mDrawLidarPoints);
    }

    if (mPrim.GetYawOffsetAttr().HasValue())
    {
        mPrim.GetYawOffsetAttr().Get(&mYawOffset);
    }

    // we have to have atleast one beam so the FOV can never be smaller than resolution
    mHorizontalResolution = pxr::GfClamp(mHorizontalResolution, 0.005f, 1024);
    mHorizontalFov = pxr::GfClamp(mHorizontalFov, mHorizontalResolution, 360);

    mVerticalResolution = pxr::GfClamp(mVerticalResolution, 0.005f, 1024);
    mVerticalFov = pxr::GfClamp(mVerticalFov, mVerticalResolution, 360);
    mRotationRate = pxr::GfClamp(mRotationRate, 0, 1024);
    mMinRange = pxr::GfClamp(mMinRange, 0, 1e9f);
    mMaxRange = pxr::GfClamp(mMaxRange, mMinRange, 1e9f);


    // CARB_LOG_INFO("%f %f %f %f %f %f %f %d %d\n",
    //        mHorizontalFov,
    //        mVerticalFov,
    //        mRotationRate,
    //        mHorizontalResolution,
    //        mVerticalResolution,
    //        mMinRange,
    //        mMaxRange,
    //        mHighLod,
    //        mDrawLidarPoints);


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

    mLastCol = 0;
    mLastNumColsTicked = 0;
    mRemainingTime = 0.0f;

    mDebugLines.clear();
}


bool raycastClosest(const physx::PxVec3& pos,
                    const physx::PxVec3& dir,
                    float distance,
                    physx::PxRaycastHit& hit,
                    physx::PxScene* physxScene)
{

    if (!physxScene)
    {
        return false;
    }
    // physx::PxRaycastHit hit;
    physx::PxHitFlags hitFlags = PxHitFlag::eDEFAULT | PxHitFlag::eMESH_BOTH_SIDES;

    const bool ret = physx::PxSceneQueryExt::raycastSingle(*physxScene, pos, dir, distance, hitFlags, hit);
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
template <bool drawLidarPoints>
void scan(int start,
          int stop,
          int rows,
          int cols,
          const physx::PxVec3& origin,
          const physx::PxQuat& worldRotation,
          carb::physics::PhysX* physxPtr,
          physx::PxScene* physxScenePtr,
          pxr::LidarSchemaLidar& prim,
          std::vector<omni::isaac::lidar::DebugData>& debugLines,
          std::vector<uint16_t>& depth,
          std::vector<float>& linearDepth,
          std::vector<uint8_t>& intensity,
          std::vector<float>& zenith,
          std::vector<float>& azimuth,
          float maxDepth,
          float metersPerUnit,
          bool zUp)
{


    int i = start * rows;
    int j = start;
    float invMaxDepth = 1.0f / maxDepth;
    physx::PxVec3 azimuthDir = zUp ? physx::PxVec3(0.0f, 0.0f, 1.0f) : physx::PxVec3(0.0f, 1.0f, 0.0f);
    physx::PxVec3 zenithDir = zUp ? physx::PxVec3(0.0f, 1.0f, 0.0f) : physx::PxVec3(0.0f, 0.0f, 1.0f);
    for (int colPreMod = start; colPreMod < stop; colPreMod++)
    {
        int col = colPreMod % cols;
        physx::PxQuat rot = worldRotation * physx::PxQuat(azimuth[col], azimuthDir);

        for (int row = 0; row < rows; row++)
        {
            // Pitch then yaw
            rot *= physx::PxQuat(zenith[row], zenithDir);
            physx::PxVec3 unitDir = rot.rotate(physx::PxVec3(1.0f, 0.0f, 0.0f)).getNormalized();
            physx::PxRaycastHit raycastHit;

            bool hit = raycastClosest(origin, unitDir, maxDepth, raycastHit, physxScenePtr);

            if (hit)
            {
                depth[i] = static_cast<uint16_t>(raycastHit.distance * invMaxDepth * 65535.0f);
                linearDepth[i] = raycastHit.distance * metersPerUnit; // in meters
                intensity[i] = 255;

                if (drawLidarPoints)
                {
                    carb::Float3 hitPos = (const carb::Float3&)raycastHit.position;
                    omni::isaac::lidar::DebugData data;
                    data.startPos = (const carb::Float3&)origin;
                    data.endPos = (const carb::Float3&)hitPos;
                    data.color = 0xFFc7f464;
                    debugLines.push_back(data);
                }
            }
            else
            {
                depth[i] = 65535;
                linearDepth[i] = maxDepth * metersPerUnit; // in meters
                intensity[i] = 0;
                if (drawLidarPoints)
                {
                    physx::PxVec3 hitPos = origin + unitDir * maxDepth;
                    omni::isaac::lidar::DebugData data;
                    data.startPos = (const carb::Float3&)origin;
                    data.endPos = (const carb::Float3&)hitPos;
                    data.color = 0xFF556270;
                    debugLines.push_back(data);
                }
            }

            if (zenith[row] == 0.0f)
                ++j %= cols;
            ++i %= (cols * rows);
        }
    }
}

void LidarSensor::dumpData(int start, int stop, float dt)
{

    // Size of mLastDepth and mLastIntensity == mRows * mLastNumColsTicked
    // Size of mDepth, and mIntensity == mRows * mCols
    // Size of mAzimuth == mCols
    // Size of mLastAzimuth == mLastNumColsTicked

    int colsToTick = stop - start;
    int unwrappedSize = std::min(stop, mCols) - start;
    int wrappedSize = std::max(0, stop - mCols);

    mLastDepth.resize(mRows * colsToTick);
    mLastLinearDepth.resize(mRows * colsToTick);
    mLastIntensity.resize(mRows * colsToTick);
    mLastAzimuth.resize(colsToTick);

    std::copy(mAzimuth.begin() + start, mAzimuth.begin() + (start + unwrappedSize), mLastAzimuth.begin());
    std::copy(mDepth.begin() + start * mRows, mDepth.begin() + (start + unwrappedSize) * mRows, mLastDepth.begin());
    std::copy(mLinearDepth.begin() + start * mRows, mLinearDepth.begin() + (start + unwrappedSize) * mRows,
              mLastLinearDepth.begin());

    std::copy(mIntensity.begin() + start * mRows, mIntensity.begin() + (start + unwrappedSize) * mRows,
              mLastIntensity.begin());

    // We wrapped around
    if (wrappedSize > 0)
    {
        std::copy(mAzimuth.begin(), mAzimuth.begin() + wrappedSize, mLastAzimuth.begin() + unwrappedSize);
        std::copy(mDepth.begin(), mDepth.begin() + wrappedSize * mRows, mLastDepth.begin() + unwrappedSize * mRows);
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
    mFastCachePtr->getTransform(mParentPrim.GetPath(), parentTrans);

    auto lidarLocalTrans = omni::usd::UsdUtils::getLocalTransformMatrix(mStage->GetPrimAtPath(mPrim.GetPath()));

    physx::PxQuat parentRot = (const physx::PxQuat&)parentTrans.orientation;
    physx::PxVec3 finalTranslation = ((const physx::PxVec3&)parentTrans.position) +
                                     parentRot.rotate(utils::conversions::asPxVec3(lidarLocalTrans.ExtractTranslation()));
    physx::PxQuat finalRotation = parentRot * utils::conversions::asPxQuat(lidarLocalTrans.ExtractRotation().GetQuat());

    float elapsedTime = mTimeDelta;
    mDebugLines.clear();
    bool zUp = pxr::UsdGeomGetStageUpAxis(mStage) == pxr::UsdGeomTokens->z;

    // Every tick does a full scan
    if (mRotationRate == 0.0f)
    {
        mLastNumColsTicked = mCols;
        if (mDrawLidarPoints)
        {
            scan<true>(0, mCols, mRows, mCols, finalTranslation, finalRotation, mPhysx, mPxScene, mPrim, mDebugLines,
                       mDepth, mLinearDepth, mIntensity, mZenith, mAzimuth, mMaxDepth, mMetersPerUnit, zUp);
        }
        else
        {
            scan<false>(0, mCols, mRows, mCols, finalTranslation, finalRotation, mPhysx, mPxScene, mPrim, mDebugLines,
                        mDepth, mLinearDepth, mIntensity, mZenith, mAzimuth, mMaxDepth, mMetersPerUnit, zUp);
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
        if (mDrawLidarPoints)
        {
            scan<true>(mLastCol, mLastCol + mLastNumColsTicked, mRows, mCols, finalTranslation, finalRotation, mPhysx,
                       mPxScene, mPrim, mDebugLines, mDepth, mLinearDepth, mIntensity, mZenith, mAzimuth, mMaxDepth,
                       mMetersPerUnit, zUp);
        }
        else
        {
            scan<false>(mLastCol, mLastCol + mLastNumColsTicked, mRows, mCols, finalTranslation, finalRotation, mPhysx,
                        mPxScene, mPrim, mDebugLines, mDepth, mLinearDepth, mIntensity, mZenith, mAzimuth, mMaxDepth,
                        mMetersPerUnit, zUp);
        }
        dumpData(mLastCol, mLastCol + mLastNumColsTicked, simulateTime);

        mLastCol = (mLastCol + mLastNumColsTicked) % mCols;
    }
}


}
}
}
