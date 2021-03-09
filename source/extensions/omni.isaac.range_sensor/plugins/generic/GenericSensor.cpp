// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
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
#include "../RangeSensorUtils.h"

#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>

#include <carb/InterfaceUtils.h>

#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

#include <iostream>
#include <chrono>
#include <string.h>

using namespace ::physx;
using namespace pxr;

namespace omni
{
namespace isaac
{
namespace range_sensor
{


GenericSensor::GenericSensor(omni::physx::IPhysx* physxPtr, carb::fastcache::FastCache* fastCachePtr)
    : RangeSensorComponent(physxPtr, fastCachePtr)
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


    if (typedPrim.GetSamplingRateAttr().HasValue())
    {
        typedPrim.GetSamplingRateAttr().Get(&mSamplingRate);
    }

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

    // if both batches are empty, set A first, then B on the next tick.
    // the last batch that's set is always the backup batch, the pActiveBatch should point to the earlier set batch.
    // if one of the batches become empty during data wrapping, the next tick should fill the batch before it checks in
    // line 475 (so it shouldn't skip any ticks for scanning)
    if (mAzimuth_A.empty())
    {
        mAzimuth_A.assign(sample_length, 0);
        mZenith_A.assign(sample_length, 0);
        memcpy(&mAzimuth_A.front(), azimuth_angles, sample_length * sizeof(float));
        memcpy(&mZenith_A.front(), zenith_angles, sample_length * sizeof(float));

        // the last batch that's set is always the backup batch, the pActiveBatch should point to the earlier set batch.
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

        // the last batch that's set is always the backup batch, the pActiveBatch should point to the earlier set batch.
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


void GenericSensor::setNextBatchOffsets(const float* origin_offsets, const int sample_length)
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


bool raycastClose(const ::physx::PxVec3& pos,
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
void scan(const ::physx::PxVec3& sensor_origin,
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
          std::vector<carb::Float3>& origin_offset,
          float maxDepth,
          float minDepth,
          float metersPerUnit,
          bool zUp)
{

    float invMaxDepth = 1.0f / maxDepth;
    // This isn't correct because the same prim (like carter) would have a different lidar axis if it was in a Y up vs Z
    // up stage. So commented this out and using the pure Z up rotation version
    // ::physx::PxVec3 azimuthDir = zUp ? ::physx::PxVec3(0.0f, 0.0f, 1.0f) : ::physx::PxVec3(0.0f, 1.0f, 0.0f);
    // ::physx::PxVec3 zenithDir = zUp ? ::physx::PxVec3(0.0f, 1.0f, 0.0f) : ::physx::PxVec3(0.0f, 0.0f, 1.0f);

    ::physx::PxVec3 azimuthDir = ::physx::PxVec3(0.0f, 0.0f, 1.0f);
    ::physx::PxVec3 zenithDir = ::physx::PxVec3(0.0f, 1.0f, 0.0f);

    size_t n_scan = azimuth.size();
    for (size_t i = 0; i < n_scan; i++)
    {
        // Pitch then yaw
        ::physx::PxQuat mainrot = worldRotation * ::physx::PxQuat(azimuth[i], azimuthDir);
        ::physx::PxQuat rot = mainrot * ::physx::PxQuat(zenith[i], zenithDir);
        ::physx::PxVec3 unitDir = rot.rotate(::physx::PxVec3(1.0f, 0.0f, 0.0f)).getNormalized();
        ::physx::PxRaycastHit raycastHit;
        // Project the start point out to prevent collisions from origin
        ::physx::PxVec3 origin = sensor_origin + utils::conversions::asPxVec3(origin_offset[i]);
        bool hit = raycastClose(origin + unitDir * minDepth, unitDir, maxDepth, raycastHit, physxScenePtr);

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
            // ::physx::PxVec3 hitPosRelRay = worldRotation.rotateInv(raycastHit.position - origin);
            // hitPosRay[i] = { hitPosRelRay.x, hitPosRelRay.y, hitPosRelRay.z }; // relative to the ray's origin
            ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(raycastHit.position - sensor_origin);
            hitPosition[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z }; // relative to the sensor's origin, not
                                                                        // accounting for individual ray origin offset
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

            else if (drawLines)
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
            // ::physx::PxVec3 hitPosRelRay = worldRotation.rotateInv(hitPos - origin);
            // hitPosRay[i] = { hitPosRelRay.x, hitPosRelRay.y, hitPosRelRay.z }; // relative to the ray's origin
            ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(hitPos - sensor_origin);
            hitPosition[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z }; // relative to the sensor's origin, not
                                                                        // accounting for individual ray origin offset
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

            else if (drawLines)
            {
                omni::isaac::range_sensor::DebugData data;

                auto temp = origin + unitDir * minDepth;
                data.startPos = { temp.x, temp.y, temp.z };
                data.endPos = { hitPos.x, hitPos.y, hitPos.z };
                data.color = 255 + (255 << 8) + (255 << 16) + (50 << 24);
                debugLines.push_back(data);
            }
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
            mAzimuth_A = {};
            mZenith_A = {};
            mOffset_A = {};
        }
        else if (pActiveAzimuth == mAzimuth_B.data())
        {
            pActiveAzimuth = mAzimuth_A.data();
            pActiveZenith = mZenith_A.data();
            pActiveOffset = mOffset_A.data();
            mAzimuth_B = {};
            mZenith_B = {};
            mOffset_B = {};
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


void GenericSensor::tick()
{
    if (!mPxScene)
    {
        CARB_LOG_ERROR("Physics Scene does not exist");
        return;
    }


    carb::fastcache::Transform parentTrans;
    parentTrans.orientation = { 0, 0, 0, 1 };
    auto genericLocalTrans = omni::usd::UsdUtils::getLocalTransformMatrix(mStage->GetPrimAtPath(mPrim.GetPath()));
    ::physx::PxVec3 finalTranslation = utils::conversions::asPxVec3(genericLocalTrans.ExtractTranslation());
    ::physx::PxQuat finalRotation = utils::conversions::asPxQuat(genericLocalTrans.ExtractRotation().GetQuat());
    // Make sure the parent prim has a transform, otherwise use local transform from the generic prim itself
    if (mParentPrim.IsA<pxr::UsdGeomXformable>())
    {
        mFastCachePtr->getTransform(mParentPrim.GetPath(), parentTrans);
        ::physx::PxQuat parentRot = utils::conversions::asPxQuat(parentTrans.orientation);
        finalTranslation = utils::conversions::asPxVec3(parentTrans.position) + parentRot.rotate(finalTranslation);
        finalRotation = parentRot * finalRotation;
    }

    mDebugLines.clear();
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
        if (mDrawLines)
        {
            scan<false, true>(finalTranslation, finalRotation, mPhysx, mPxScene, mDebugLines, mDepth, mHitPos,
                              mLinearDepth, mIntensity, mZenith, mAzimuth, mOffset, mMaxDepth, mMinDepth,
                              mMetersPerUnit, zUp);
        }
        else if (mDrawPoints)
        {
            scan<true, false>(finalTranslation, finalRotation, mPhysx, mPxScene, mDebugLines, mDepth, mHitPos,
                              mLinearDepth, mIntensity, mZenith, mAzimuth, mOffset, mMaxDepth, mMinDepth,
                              mMetersPerUnit, zUp);
        }
        else
        {
            scan<false, false>(finalTranslation, finalRotation, mPhysx, mPxScene, mDebugLines, mDepth, mHitPos,
                               mLinearDepth, mIntensity, mZenith, mAzimuth, mOffset, mMaxDepth, mMinDepth,
                               mMetersPerUnit, zUp);
        }
        dumpData();
    }
}


}
}
}
