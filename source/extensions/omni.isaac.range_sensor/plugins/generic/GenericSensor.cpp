// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
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

#include "GenericSensor.h"

#include <carb/InterfaceUtils.h>

#include <omni/isaac/utils/Pose.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>

#include <chrono>
#include <iostream>
#include <string.h>

using namespace ::physx;
using namespace pxr;

namespace omni
{
namespace isaac
{
namespace range_sensor
{


GenericSensor::GenericSensor(omni::renderer::IDebugDraw* debugDrawPtr, omni::physx::IPhysx* physxPtr)
    : RangeSensorComponent(debugDrawPtr, physxPtr)
{
}

GenericSensor::~GenericSensor()
{
}

void GenericSensor::onStart()
{
    RangeSensorComponent::onStart();
}

void GenericSensor::onComponentChange()
{

    RangeSensorComponent::onComponentChange();

    const pxr::RangeSensorSchemaGeneric& typedPrim = (pxr::RangeSensorSchemaGeneric)mPrim;

    isaac::utils::safeGetAttribute(typedPrim.GetSamplingRateAttr(), mSamplingRate);
    isaac::utils::safeGetAttribute(typedPrim.GetStreamingAttr(), mStreaming);

    mMinRange = pxr::GfClamp(mMinRange, 0, 1e9f);
    mMaxRange = pxr::GfClamp(mMaxRange, mMinRange, 1e9f);
    mMinDepth = mMinRange / mMetersPerUnit;
    mMaxDepth = mMaxRange / mMetersPerUnit;


    // all of these will be resized to mSamplesPerTick;
    mAzimuth.assign(mSamplingRate, 0);
    mZenith.assign(mSamplingRate, 0);
    mOffset.assign(mSamplingRate, { 0, 0, 0 });
    mLinearDepth.assign(mSamplingRate, 0);
    mIntensity.assign(mSamplingRate, 0);
    mDepth.assign(mSamplingRate, 0);
    mHitPos.assign(mSamplingRate, { 0, 0, 0 });
}

bool GenericSensor::sendNextBatch()
{
    if (mAzimuth_A.empty() || mAzimuth_B.empty())
    {
        return true;
    }
    else
    {
        return false;
    }
}

void GenericSensor::setNextBatchRays(const float* azimuth_angles, const float* zenith_angles, const int sample_length)
{
    // if not streaming
    // copy the first half of the data to batch_A, second half to batch_B
    // now neither batch are empty, and no more sentNextBatch should be set to True

    // if streaming
    // if both batches are empty, set A first, then B on the next tick.
    // the last batch that's set is always the backup batch, the pActiveBatch should point to the earlier set batch.
    // if one of the batches become empty during data wrapping, the next tick should fill the batch before it checks in
    // line 475 (so it shouldn't skip any ticks for scanning)

    if (!mStreaming)
    {
        A_length = int(sample_length / 2);
        B_length = sample_length - A_length;
        mAzimuth_A.assign(A_length, 0);
        mZenith_A.assign(A_length, 0);
        mAzimuth_B.assign(B_length, 0);
        mZenith_B.assign(B_length, 0);
        memcpy(&mAzimuth_A.front(), azimuth_angles, A_length * sizeof(float));
        memcpy(&mZenith_A.front(), zenith_angles, A_length * sizeof(float));
        memcpy(&mAzimuth_B.front(), azimuth_angles + A_length, B_length * sizeof(float));
        memcpy(&mZenith_B.front(), zenith_angles + A_length, B_length * sizeof(float));

        // set pointer to start with A
        pActiveAzimuth = mAzimuth_A.data();
        pActiveZenith = mZenith_A.data();
        mBatchSize = A_length;
    }
    else
    {
        if (mAzimuth_A.empty())
        {
            mAzimuth_A.assign(sample_length, 0);
            mZenith_A.assign(sample_length, 0);
            memcpy(&mAzimuth_A.front(), azimuth_angles, sample_length * sizeof(float));
            memcpy(&mZenith_A.front(), zenith_angles, sample_length * sizeof(float));

            // the last batch that's set is always the backup batch, the pActiveBatch should point to the earlier set
            // batch.
            if (!mAzimuth_B.empty())
            {
                pActiveAzimuth = mAzimuth_B.data();
                pActiveZenith = mZenith_B.data();
            }
            else
            {
                CARB_LOG_WARN("need more data");
            }
        }
        else if (mAzimuth_B.empty())
        {

            mAzimuth_B.assign(sample_length, 0);
            mZenith_B.assign(sample_length, 0);
            memcpy(&mAzimuth_B.front(), azimuth_angles, sample_length * sizeof(float));
            memcpy(&mZenith_B.front(), zenith_angles, sample_length * sizeof(float));

            // the last batch that's set is always the backup batch, the pActiveBatch should point to the earlier set
            // batch.
            if (!mAzimuth_A.empty())
            {
                pActiveAzimuth = mAzimuth_A.data();
                pActiveZenith = mZenith_A.data();
            }
            else
            {
                CARB_LOG_WARN("need more data ");
            }
        }
        else
        {
            CARB_LOG_WARN("new sensor pattern data not set. Only send new data when send_next_batch() returns true");
        }
        mBatchSize = sample_length;
    }
}


void GenericSensor::setNextBatchOffsets(const float* origin_offsets, const int sample_length)
{
    if (!mStreaming)
    {
        int offset_A_length = int(sample_length / 2);
        int offset_B_length = sample_length - offset_A_length;
        if ((offset_A_length != A_length) || (offset_B_length != B_length))
        {
            CARB_LOG_WARN("offset data size mismatch");
        }
        mOffset_A.assign(A_length, { 0, 0, 0 });
        mOffset_B.assign(B_length, { 0, 0, 0 });
        memcpy(&mOffset_A.front(), origin_offsets, A_length * sizeof(carb::Float3));
        memcpy(&mOffset_B.front(), origin_offsets + A_length, B_length * sizeof(carb::Float3));
        pActiveOffset = mOffset_A.data();
    }
    else
    {
        if (sample_length != mBatchSize)
        {
            CARB_LOG_WARN("offset data size mismatch");
        }

        if (mOffset_A.empty())
        {
            mOffset_A.assign(sample_length, { 0, 0, 0 });
            memcpy(&mOffset_A.front(), origin_offsets, sample_length * sizeof(carb::Float3));
            if (!mOffset_B.empty())
            {
                pActiveOffset = mOffset_B.data();
            }
        }
        else if (mOffset_B.empty())
        {
            mOffset_B.assign(sample_length, { 0, 0, 0 });
            memcpy(&mOffset_B.front(), origin_offsets, sample_length * sizeof(carb::Float3));
            if (!mOffset_A.empty())
            {
                pActiveOffset = mOffset_A.data();
            }
        }
        else
        {
            CARB_LOG_WARN("offset data not set. Only send new data when send_next_batch() returns true");
        }
    }
}


void GenericSensor::wrapData(int start)
{

    double current_fps = 1.0 / mTimeDelta;
    mSamplesPerTick = std::max(1, int(mSamplingRate / current_fps)); // scan at least once per tick
    if (mBatchSize < mSamplesPerTick)
    {
        CARB_LOG_ERROR(
            "Not enough data per sample batch to match sampling rate. Scanning faster than intended and could have missing data. Lower the sample rate or send more data per batch.");
    }
    else if (mSamplesPerTick > maxSamplesPerTick)
    {
        CARB_LOG_WARN("Sampling rate exceed specs. Scanning slower than intended.");
        mSamplesPerTick = maxSamplesPerTick;
    }

    mAzimuth.resize(mSamplesPerTick);
    mZenith.resize(mSamplesPerTick);
    mOffset.resize(mSamplesPerTick);
    mDepth.resize(mSamplesPerTick);
    mIntensity.resize(mSamplesPerTick);
    mHitPos.resize(mSamplesPerTick);
    mLinearDepth.resize(mSamplesPerTick);


    int stop = start + mSamplesPerTick;
    int pt_counter = 0;

    if (stop <= mBatchSize)
    {
        // get all the data from currentBatch
        for (int i = start; i < stop; i++)
        {
            mAzimuth[pt_counter] = pActiveAzimuth[i];
            mZenith[pt_counter] = pActiveZenith[i];
            mOffset[pt_counter] = pActiveOffset[i];
            pt_counter++;
        }
        mLastSample = stop;
    }
    else
    {
        for (int j = start; j < mBatchSize; j++)
        {
            mAzimuth[pt_counter] = pActiveAzimuth[j];
            mZenith[pt_counter] = pActiveZenith[j];
            mOffset[pt_counter] = pActiveOffset[j];

            pt_counter++;
        }
        // switch batches
        if (pActiveAzimuth == mAzimuth_A.data())
        {
            pActiveAzimuth = mAzimuth_B.data();
            pActiveZenith = mZenith_B.data();
            pActiveOffset = mOffset_B.data();

            // if streaming, empty out the batch that has just been read
            if (mStreaming)
            {
                mAzimuth_A = {};
                mZenith_A = {};
                mOffset_A = {};
            }
            else
            {
                mBatchSize = B_length;
            }
        }
        else if (pActiveAzimuth == mAzimuth_B.data())
        {
            pActiveAzimuth = mAzimuth_A.data();
            pActiveZenith = mZenith_A.data();
            pActiveOffset = mOffset_A.data();

            // if streaming, empty out the batch that has just been read
            if (mStreaming)
            {
                mAzimuth_B = {};
                mZenith_B = {};
                mOffset_B = {};
            }
            else
            {
                mBatchSize = A_length;
            }
        }
        else
        {
            CARB_LOG_ERROR("something's wrong with batch switching");
            return;
        }

        for (int k = 0; k <= (stop % mBatchSize); k++)
        {
            mAzimuth[pt_counter] = pActiveAzimuth[k];
            mZenith[pt_counter] = pActiveZenith[k];
            mOffset[pt_counter] = pActiveOffset[k];
            pt_counter++;
        }
        mLastSample = stop % mBatchSize;
    }
}


void GenericSensor::dumpData()
{
    mLastAzimuth = mAzimuth;
    mLastZenith = mZenith;
    mLastOffset = mOffset;
    mLastDepth = mDepth;
    mLastLinearDepth = mLinearDepth;
    mLastIntensity = mIntensity;
    mLastHitPos = mHitPos;
}


void GenericSensor::preTick()
{

    auto worldMat = omni::isaac::utils::pose::computeWorldXformNoCache(mStage, mUsdrtStage, mPrim.GetPath());

    mFinalTranslation = utils::conversions::asPxVec3(worldMat.ExtractTranslation());
    mFinalRotation = utils::conversions::asPxQuat(worldMat.ExtractRotation());
}

void GenericSensor::tick()
{
    mLineDrawing->clear();
    mPointDrawing->clear();

    if (!mPxScene)
    {
        CARB_LOG_ERROR("Physics Scene does not exist");
        return;
    }

    bool zUp = pxr::UsdGeomGetStageUpAxis(mStage) == pxr::UsdGeomTokens->z;

    // scanning
    // make sure both batches have data
    if (mAzimuth_A.empty() || mAzimuth_B.empty())
    {
        return; // and fetch more data one batch at a time until both are full
    }

    if (mOffset_A.empty() && mOffset_B.empty())
    {
        // if offset is not set, default to (0,0,0)
        mOffset_A.assign(mBatchSize, { 0, 0, 0 });
        mOffset_B.assign(mBatchSize, { 0, 0, 0 });
        pActiveOffset = mOffset_A.data();
    }

    if (pActiveAzimuth != NULL)
    {
        wrapData(mLastSample);
        if (mDrawLines && mDrawPoints)
        {
            scan<true, true>(mFinalTranslation, mFinalRotation, mPhysx, mPxScene, mDepth, mHitPos, mLinearDepth,
                             mIntensity, mZenith, mAzimuth, mOffset, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
        }
        else if (mDrawLines)
        {
            scan<false, true>(mFinalTranslation, mFinalRotation, mPhysx, mPxScene, mDepth, mHitPos, mLinearDepth,
                              mIntensity, mZenith, mAzimuth, mOffset, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
        }
        else if (mDrawPoints)
        {
            scan<true, false>(mFinalTranslation, mFinalRotation, mPhysx, mPxScene, mDepth, mHitPos, mLinearDepth,
                              mIntensity, mZenith, mAzimuth, mOffset, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
        }
        else
        {
            scan<false, false>(mFinalTranslation, mFinalRotation, mPhysx, mPxScene, mDepth, mHitPos, mLinearDepth,
                               mIntensity, mZenith, mAzimuth, mOffset, mMaxDepth, mMinDepth, mMetersPerUnit, zUp);
        }
        dumpData();
    }
}


}
}
}
