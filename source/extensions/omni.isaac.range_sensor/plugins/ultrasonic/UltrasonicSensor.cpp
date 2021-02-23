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

#include "UltrasonicSensor.h"
#include "USSEnvelope.h"

#include "../RangeSensorUtils.h"


#include <carb/InterfaceUtils.h>
#include "FiringGroupUtils.h"

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
    : RangeSensorComponent(physxPtr, fastCachePtr),
      mIsReceiving(2, std::vector<bool>()),
      mIsFiring(2, std::vector<bool>())
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


    pxr::SdfPathVector emitterTargets;
    typedPrim.GetEmitterPrimsRel().GetTargets(&emitterTargets);

    if (emitterTargets.size() == 0)
    {
        return;
    }


    mEmitters.clear();
    for (size_t i = 0; i < emitterTargets.size(); i++)
    {
        pxr::UsdPrim prim = mStage->GetPrimAtPath(emitterTargets[i]);
        if (prim.IsA<pxr::RangeSensorSchemaUltrasonicEmitter>())
        {
            const pxr::RangeSensorSchemaUltrasonicEmitter& typedPrim = (pxr::RangeSensorSchemaUltrasonicEmitter)prim;
            mEmitters.push_back(UltrasonicEmitter());
            mEmitters[i].initialize(typedPrim, mStage, mNumBins, mMaxDepth * mMetersPerUnit, mRows, mCols);
        }
    }

    pxr::SdfPathVector firingGroupTargets;
    typedPrim.GetFiringGroupsRel().GetTargets(&firingGroupTargets);
    mFiringGroups.clear();
    if (firingGroupTargets.size() != 0)
    {
        for (size_t i = 0; i < firingGroupTargets.size(); i++)
        {
            pxr::UsdPrim prim = mStage->GetPrimAtPath(firingGroupTargets[i]);
            if (prim.IsA<pxr::RangeSensorSchemaUltrasonicFiringGroup>())
            {
                const pxr::RangeSensorSchemaUltrasonicFiringGroup& typedPrim =
                    (pxr::RangeSensorSchemaUltrasonicFiringGroup)prim;
                mFiringGroups.push_back(UltrasonicFiringGroup());
                mFiringGroups[i].initialize(typedPrim, mStage);
            }
        }
    }

    mReceiverArray.mMetersPerUnit = mMetersPerUnit;
}


void UltrasonicSensor::tick()
{
    if (!mPxScene)
    {
        CARB_LOG_ERROR("Physics Scene does not exist");
        return;
    }
    // TODO @markb: there's a lot of work happening both when there are and aren't firing groups;
    // a lot of this should probably be abstracted away into UltrasonicReceiver or similar
    if (mFiringGroups.size() > 0)
    {

        const UltrasonicFiringGroup& group = mFiringGroups[mCurrentFiringGroup];

        std::vector<std::vector<::physx::PxVec3>> worldPoints(mEmitters.size());
        std::vector<::physx::PxVec3> origins = omni::isaac::range_sensor::extractOrigins(mEmitters, mFastCachePtr);
        std::vector<std::vector<uint8_t>> adjacency = omni::isaac::range_sensor::extractAdjacencyVectors(mEmitters);

        // fire low then high
        std::vector<std::vector<USSEnvelope>> envelopeList(
            2, std::vector<USSEnvelope>(0, USSEnvelope(mNumBins, mMaxDepth * mMetersPerUnit)));


        mIsFiring[mFreqIdLow] =
            omni::isaac::range_sensor::modesToBooleanVector(group.mEmitterModes, mFreqIdLow, mEmitters.size());
        mIsFiring[mFreqIdHigh] =
            omni::isaac::range_sensor::modesToBooleanVector(group.mEmitterModes, mFreqIdHigh, mEmitters.size());

        mIsReceiving[mFreqIdLow] =
            omni::isaac::range_sensor::modesToBooleanVector(group.mReceiverModes, mFreqIdLow, mEmitters.size());
        mIsReceiving[mFreqIdHigh] =
            omni::isaac::range_sensor::modesToBooleanVector(group.mReceiverModes, mFreqIdHigh, mEmitters.size());
        for (size_t currentFreqId = 0; currentFreqId <= 1; currentFreqId++)
        {
            for (size_t i = 0; i < group.mEmitterModes.size(); i++)
            {
                // TODO do both low and high inside of this loop

                pxr::GfVec2i emitterMode = group.mEmitterModes[i];
                // TODO use emitterMode[1] which contains the mode data
                mEmitters[emitterMode[0]].doScan(
                    mFastCachePtr, mPhysx, mPxScene, mZenith, mAzimuth, mMaxDepth, mMinDepth);

                if (worldPoints[emitterMode[0]].size() == 0)
                {
                    worldPoints[emitterMode[0]] = mEmitters[emitterMode[0]].mHitPosWorld;
                }
                // TODO Use the goup.mReceiverModes array to do envelope calculation
            }

            envelopeList[currentFreqId] = mReceiverArray.getCombinedEnvelopeList(
                mNumBins, mMaxDepth * mMetersPerUnit, adjacency, mIsFiring[currentFreqId], mIsReceiving[currentFreqId],
                origins, origins, worldPoints);
        }
        // this is mode 0; do mode 1
        for (size_t j = 0; j < envelopeList[0].size(); j++)
        {
            // set low and hi envelopes
            mEmitters[j].setEnvelopes(envelopeList[mFreqIdLow][j], envelopeList[mFreqIdHigh][j],
                                      mIsReceiving[mFreqIdLow][j], mIsReceiving[mFreqIdHigh][j]);
        }
        // Increment and clamp the firing group
        mCurrentFiringGroup += 1;
        mCurrentFiringGroup = mCurrentFiringGroup % mFiringGroups.size();
    }
    else
    {
        // Fire everything if there is no group info
        for (size_t i = 0; i < mEmitters.size(); i++)
        {
            mEmitters[i].doScan(mFastCachePtr, mPhysx, mPxScene, mZenith, mAzimuth, mMaxDepth, mMinDepth);
            std::vector<float> totalDepth;
            // all direct intensity; low + high = 1
            std::vector<float> intensities(mEmitters[i].mLinearDepth.size(), 0.5f);
            for (size_t j = 0; j < mEmitters[i].mLinearDepth.size(); j++)
            {
                totalDepth.push_back(mEmitters[i].mLinearDepth[j] * 2.f);
            }
            USSEnvelope env(mNumBins, mMaxDepth * mMetersPerUnit);
            env.updateEnvelope(totalDepth, intensities);
            mEmitters[i].setEnvelopes(env, env, true, true);
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
void UltrasonicSensor::onFiringGroupChange(const pxr::UsdPrim& prim)
{
    for (auto& group : mFiringGroups)
    {
        if (group.getPrim().GetPrim() == prim)
        {
            group.onComponentChange();
        }
    }
}

}
}
}
