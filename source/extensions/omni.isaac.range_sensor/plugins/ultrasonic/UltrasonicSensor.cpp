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

#include "UltrasonicSensor.h"

#include "FiringGroupUtils.h"
#include "USSEnvelope.h"

#include <carb/InterfaceUtils.h>

#include <iostream>
#include <sstream>
#include <string>

using namespace ::physx;
using namespace pxr;

namespace omni
{
namespace isaac
{
namespace range_sensor
{


UltrasonicSensor::UltrasonicSensor(omni::renderer::IDebugDraw* debugDrawPtr,
                                   omni::physx::IPhysx* physxPtr,
                                   carb::tasking::ITasking* taskingPtr)
    : RangeSensorComponent(debugDrawPtr, physxPtr)
{
    mTasking = taskingPtr;
    mTaskCounter = mTasking->createCounter();
}

UltrasonicSensor::~UltrasonicSensor()
{
    mTasking->wait(mTaskCounter);
    mTasking->destroyCounter(mTaskCounter);
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
    isaac::utils::safeGetAttribute(typedPrim.GetUseBRDFAttr(), mUseBRDF);
    isaac::utils::safeGetAttribute(typedPrim.GetUseUSSMaterialsForBRDFAttr(), mUseUSSMaterialsForBRDF);

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
            mEmitters.push_back(std::make_unique<UltrasonicEmitter>());
            mEmitters[i]->initialize(typedPrim, mStage, mPhysx, mNumBins, mMaxDepth * mMetersPerUnit, mRows, mCols,
                                     mDrawLines, mDrawPoints, mZenith, mAzimuth);
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
                mFiringGroups[i].initialize(typedPrim, mStage, mEmitters.size());
            }
        }
    }

    mReceiverArray.mMetersPerUnit = mMetersPerUnit;
    mReceiverArray.mUseBRDF = mUseBRDF;
    mReceiverArray.mUseUSSMaterialsForBRDF = mUseUSSMaterialsForBRDF;
    mReceiverArray.mNumBins = mNumBins;
    mReceiverArray.mMaxDist = mMaxDepth * mMetersPerUnit;
    mReceiverArray.mHorizontalFov = 0.5f * mHorizontalFov * static_cast<float>(M_PI / 180.0);
    mReceiverArray.mVerticalFov = 0.5f * mVerticalFov * static_cast<float>(M_PI / 180.0);

    // we support low and high firing modes currently
    mEnvelopeList.push_back(std::vector<USSEnvelope>(0, USSEnvelope(mNumBins, mMaxDepth * mMetersPerUnit)));
    mEnvelopeList.push_back(std::vector<USSEnvelope>(0, USSEnvelope(mNumBins, mMaxDepth * mMetersPerUnit)));

    mWorldPoints.resize(mEmitters.size());
    mNormals.resize(mEmitters.size());
    mWorldMaterials.resize(mEmitters.size());

    mAdjacency = omni::isaac::range_sensor::extractAdjacencyVectors(mEmitters);
}


struct USSTaskData
{
    float maxDepth;
    float minDepth;
    ::physx::PxScene* pxScene;
    UltrasonicEmitter* emitter;
};

auto USSTaskFunction = [](void* taskArg)
{
    USSTaskData* taskData = reinterpret_cast<USSTaskData*>(taskArg);
    taskData->emitter->doScan(taskData->maxDepth, taskData->minDepth, taskData->pxScene);
};
void UltrasonicSensor::preTick()
{
    for (size_t i = 0; i < mEmitters.size(); i++)
    {
        mEmitters[i]->updatePose();
    }
}
void UltrasonicSensor::tick()
{

    mLineDrawing->clear();
    mPointDrawing->clear();
    if (!mPxScene)
    {
        CARB_LOG_ERROR("Physics Scene does not exist");
        return;
    }

    if (mFiringGroups.size() > 0)
    {
        // Increment and clamp the firing group
        mCurrentFiringGroup += 1;
        mCurrentFiringGroup = mCurrentFiringGroup % mFiringGroups.size();

        const UltrasonicFiringGroup& group = mFiringGroups[mCurrentFiringGroup];
        // This needs to happen each frame because the emitter moves.
        std::vector<::physx::PxTransform> origins = omni::isaac::range_sensor::extractOrigins(mEmitters);

        // fire low then high

        {
            USSTaskData* taskArray = new USSTaskData[group.mEmitterModes.size()];
            int index = 0;
            // The emitters to fire in this group
            for (size_t i = 0; i < group.mEmitterModes.size(); i++)
            {
                const pxr::GfVec2i& emitterMode = group.mEmitterModes[i];

                // TODO do both low and high inside of this loop
                taskArray[index].maxDepth = mMaxDepth;
                taskArray[index].minDepth = mMinDepth;
                taskArray[index].pxScene = mPxScene;
                taskArray[index].emitter = mEmitters[emitterMode[0]].get();
                // TODO use emitterMode[1] which contains the mode data
                mTasking->addTask(
                    carb::tasking::Priority::eHigh, mTaskCounter, USSTaskFunction, (void*)(taskArray + index));
                index++;
            }
            mTasking->wait(mTaskCounter);
            delete[] taskArray;

            for (size_t i = 0; i < group.mEmitterModes.size(); i++)
            {
                const pxr::GfVec2i& emitterMode = group.mEmitterModes[i];
                // mEmitters[emitterMode[0]]->doScan(mMaxDepth, mMinDepth, mPxScene);
                mWorldPoints[emitterMode[0]].clear();
                mNormals[emitterMode[0]].clear();
                mWorldMaterials[emitterMode[0]].clear();

                // for non BRDF line drawing
                if (mDrawLines && (!mUseBRDF || !mUseUSSMaterialsForBRDF))
                {
                    mLineDrawing->addVertices(mEmitters[emitterMode[0]]->mLines);
                }

                if (mDrawPoints)
                {
                    mPointDrawing->addVertices(mEmitters[emitterMode[0]]->mPoints);
                }

                for (size_t j = 0; j < mEmitters[emitterMode[0]]->mIntensity.size(); j++)
                {
                    if (mEmitters[emitterMode[0]]->mIntensity[j] != 0)
                    {
                        mWorldPoints[emitterMode[0]].push_back(mEmitters[emitterMode[0]]->mHitPosWorld[j]);
                        mNormals[emitterMode[0]].push_back(mEmitters[emitterMode[0]]->mNormals[j]);
                        mWorldMaterials[emitterMode[0]].push_back(mEmitters[emitterMode[0]]->mHitMaterials[j]);
                    }
                }
            }
        }
        // TODO Use the goup.mReceiverModes array to do envelope calculation

        {
            mEnvelopeList[mFreqIdLow] = mReceiverArray.getCombinedEnvelopeList(
                mAdjacency, group.mIsFiring[mFreqIdLow], group.mIsReceiving[mFreqIdLow], origins, origins, mWorldPoints,
                mNormals, mWorldMaterials);

            mEnvelopeList[mFreqIdHigh] = mReceiverArray.getCombinedEnvelopeList(
                mAdjacency, group.mIsFiring[mFreqIdHigh], group.mIsReceiving[mFreqIdHigh], origins, origins,
                mWorldPoints, mNormals, mWorldMaterials);

            // for BRDF line drawing since there are filters on which BRDF lines to draw
            if (mDrawLines && mUseBRDF)
            {
                mLineDrawing->addVertices(mReceiverArray.mReceiverLines);
                mReceiverArray.mReceiverLines.clear();
            }
        }
        {

            // this is mode 0; do mode 1
            for (size_t j = 0; j < mEnvelopeList[0].size(); j++)
            {
                // set low and hi envelopes
                mEmitters[j]->setEnvelopes(mEnvelopeList[mFreqIdLow][j], mEnvelopeList[mFreqIdHigh][j],
                                           group.mIsReceiving[mFreqIdLow][j], group.mIsReceiving[mFreqIdHigh][j]);
            }
        }
    }
    else
    {
        // Fire everything if there is no group info
        for (size_t i = 0; i < mEmitters.size(); i++)
        {
            mEmitters[i]->doScan(mMaxDepth, mMinDepth, mPxScene);
            std::vector<float> totalDepth;
            // all direct intensity; low + high = 1
            // to clarify this, look at setEnvelopes in UltrasonicEmitter
            // it combines the low and the high
            std::vector<float> intensities(mEmitters[i]->mLinearDepth.size(), 0.5f);
            for (size_t j = 0; j < mEmitters[i]->mLinearDepth.size(); j++)
            {
                totalDepth.push_back(mEmitters[i]->mLinearDepth[j] * 2.f);
            }
            USSEnvelope env(mNumBins, mMaxDepth * mMetersPerUnit);
            env.updateEnvelope(totalDepth, intensities);
            // low and high set to the same; effectively doubled
            mEmitters[i]->setEnvelopes(env, env, true, true);

            if (mDrawLines)
            {
                mLineDrawing->addVertices(mEmitters[i]->mLines);
            }

            if (mDrawPoints)
            {
                mPointDrawing->addVertices(mEmitters[i]->mPoints);
            }
        }
    }
}
void UltrasonicSensor::onEmitterChange(const pxr::UsdPrim& prim)
{
    for (auto& emitter : mEmitters)
    {
        if (emitter->getPrim().GetPrim() == prim)
        {
            emitter->onComponentChange();
        }
    }
    mAdjacency = omni::isaac::range_sensor::extractAdjacencyVectors(mEmitters);
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
