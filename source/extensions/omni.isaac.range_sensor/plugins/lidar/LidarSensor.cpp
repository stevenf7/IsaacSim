// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
// clang-format on

#include "LidarSensor.h"

#include <carb/InterfaceUtils.h>
#include <carb/flatcache/FlatCache.h>
#include <carb/flatcache/FlatCacheUSD.h>
#include <carb/flatcache/IToken.h>
#include <carb/flatcache/StageWithHistory.h>

#include <omni/isaac/utils/Conversions.h>
#include <omni/isaac/utils/Pose.h>
#include <omni/kit/syntheticdata/SyntheticData.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>

#include <iostream>
#include <numeric>

using namespace ::physx;
using namespace pxr;

namespace omni
{
namespace isaac
{
namespace range_sensor
{


LidarSensor::LidarSensor(omni::renderer::IDebugDraw* debugDrawPtr,
                         omni::physx::IPhysx* physxPtr,
                         omni::syntheticdata::SyntheticData* syntheticDataPtr)
    : RangeSensorComponent(debugDrawPtr, physxPtr)
{
    mSyntheticDataPtr = syntheticDataPtr;
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

    isaac::utils::safeGetAttribute(typedPrim.GetHorizontalFovAttr(), mHorizontalFov);
    isaac::utils::safeGetAttribute(typedPrim.GetVerticalFovAttr(), mVerticalFov);
    isaac::utils::safeGetAttribute(typedPrim.GetHorizontalResolutionAttr(), mHorizontalResolution);
    isaac::utils::safeGetAttribute(typedPrim.GetVerticalResolutionAttr(), mVerticalResolution);
    isaac::utils::safeGetAttribute(typedPrim.GetRotationRateAttr(), mRotationRate);
    isaac::utils::safeGetAttribute(typedPrim.GetHighLodAttr(), mHighLod);
    isaac::utils::safeGetAttribute(typedPrim.GetYawOffsetAttr(), mYawOffset);
    isaac::utils::safeGetAttribute(typedPrim.GetEnableSemanticsAttr(), mEnableSemantics);

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

    mAzimuthRange = { mAzimuth[0], mAzimuth[mCols - 1] };
    mZenithRange = { mZenith[0], mZenith[mRows - 1] };

    // High LOD false means 2D lidar
    if (!mHighLod)
    {
        mZenith[0] = 0.0f;
        mZenithRange = { 0.0f, 0.0f };
    }

    mLastAzimuth.assign(mMaxColsPerTick, 0.0f);
    mLastDepth.assign(mRows * mMaxColsPerTick, 0);
    mLastLinearDepth.assign(mRows * mMaxColsPerTick, 0);
    mLastHitPos.assign(mRows * mCols, { 0, 0, 0 });
    mLastSemanticID.assign(mRows * mCols, 0);
    mLastCol = 0;
    mLastNumColsTicked = 0;
    mRemainingTime = 0.0f;

    mSemanticID.assign(mRows * mCols, 0);
    if (mSemanticToRandomID.size() == 0)
    {
        std::srand(0); // This forces all lidars to have the same color scheme
        mSemanticToRandomID.resize(mNumSemanticIDs);
        std::iota(mSemanticToRandomID.begin(), mSemanticToRandomID.end(), 1);
        std::random_shuffle(mSemanticToRandomID.begin(), mSemanticToRandomID.end());
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
    mLastSemanticID.resize(mRows * colsToTick);

    std::copy(mAzimuth.begin() + start, mAzimuth.begin() + (start + unwrappedSize), mLastAzimuth.begin());
    std::copy(mDepth.begin() + start * mRows, mDepth.begin() + (start + unwrappedSize) * mRows, mLastDepth.begin());
    std::copy(mHitPos.begin() + start * mRows, mHitPos.begin() + (start + unwrappedSize) * mRows, mLastHitPos.begin());

    std::copy(mLinearDepth.begin() + start * mRows, mLinearDepth.begin() + (start + unwrappedSize) * mRows,
              mLastLinearDepth.begin());

    std::copy(mIntensity.begin() + start * mRows, mIntensity.begin() + (start + unwrappedSize) * mRows,
              mLastIntensity.begin());

    std::copy(mSemanticID.begin() + start * mRows, mSemanticID.begin() + (start + unwrappedSize) * mRows,
              mLastSemanticID.begin());

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
        std::copy(mSemanticID.begin(), mSemanticID.begin() + wrappedSize * mRows,
                  mLastSemanticID.begin() + unwrappedSize * mRows);
    }
}

void LidarSensor::preTick()
{
    auto worldMat = omni::isaac::utils::pose::computeWorldXformNoCache(mStage, mUsdrtStage, mPrim.GetPath());

    mFinalTranslation = utils::conversions::asPxVec3(worldMat.ExtractTranslation());
    mFinalRotation = utils::conversions::asPxQuat(worldMat.ExtractRotation());
}

void LidarSensor::tick()
{
    // Clear active semantic IDs each frame
    mSemanticID.assign(mRows * mCols, 0);

    mLineDrawing->clear();
    mPointDrawing->clear();

    if (!mPxScene)
    {
        CARB_LOG_ERROR("Physics Scene does not exist");
        return;
    }


    double elapsedTime = mTimeDelta;
    bool zUp = pxr::UsdGeomGetStageUpAxis(mStage) == pxr::UsdGeomTokens->z;

    // Every tick does a full scan
    if (mRotationRate == 0.0f)
    {
        mLastNumColsTicked = mCols;


        if (mEnableSemantics)
        {
            if (mDrawPoints && mDrawLines)
            {
                scan<true, true, true>(0, mCols, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
            else if (mDrawPoints)
            {
                scan<true, false, true>(0, mCols, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
            else if (mDrawLines)
            {
                scan<false, true, true>(0, mCols, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
            else
            {
                scan<false, false, true>(0, mCols, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
        }
        else
        {
            if (mDrawPoints && mDrawLines)
            {
                scan<true, true, false>(0, mCols, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
            else if (mDrawPoints)
            {
                scan<true, false, false>(0, mCols, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
            else if (mDrawLines)
            {
                scan<false, true, false>(0, mCols, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
            else
            {
                scan<false, false, false>(0, mCols, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
        }

        if (mFirstFrame)
        {
            mFirstFrame = false;
        }
        else
        {
            dumpData(0, mCols, elapsedTime);

            mLastCol = 0;
        }
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
        if (mEnableSemantics)
        {
            if (mDrawPoints && mDrawLines)
            {
                scan<true, true, true>(
                    mLastCol, mLastCol + mLastNumColsTicked, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
            else if (mDrawPoints)
            {
                scan<true, false, true>(
                    mLastCol, mLastCol + mLastNumColsTicked, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
            else if (mDrawLines)
            {
                scan<false, true, true>(
                    mLastCol, mLastCol + mLastNumColsTicked, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
            else
            {
                scan<false, false, true>(
                    mLastCol, mLastCol + mLastNumColsTicked, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
        }
        else
        {
            if (mDrawPoints && mDrawLines)
            {
                scan<true, true, false>(
                    mLastCol, mLastCol + mLastNumColsTicked, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
            else if (mDrawPoints)
            {
                scan<true, false, false>(
                    mLastCol, mLastCol + mLastNumColsTicked, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
            else if (mDrawLines)
            {
                scan<false, true, false>(
                    mLastCol, mLastCol + mLastNumColsTicked, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
            else
            {
                scan<false, false, false>(
                    mLastCol, mLastCol + mLastNumColsTicked, mRows, mCols, mFinalTranslation, mFinalRotation, zUp);
            }
        }

        if (mFirstFrame)
        {
            mFirstFrame = false;
        }
        else
        {
            dumpData(mLastCol, mLastCol + mLastNumColsTicked, simulateTime);

            mLastCol = (mLastCol + mLastNumColsTicked) % mCols;
        }
    }
    mSequenceNumber++;
}


}
}
}
