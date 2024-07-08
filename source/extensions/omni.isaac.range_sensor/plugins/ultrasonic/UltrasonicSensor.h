// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once


#include "../core/RangeSensorComponent.h"
#include "UltrasonicArrayEmissionTimer.h"
#include "UltrasonicEmitter.h"
#include "UltrasonicFiringGroup.h"
#include "UltrasonicReceiverArray.h"

#include <extensions/PxSceneQueryExt.h>
#include <pxr/base/gf/vec3f.h>
#include <pxr/usd/usd/inherits.h>
#include <rangeSensorSchema/ultrasonicArray.h>

#include <RangeSensorInterface.h>
#include <vector>

namespace omni
{
namespace isaac
{
namespace range_sensor
{

class UltrasonicSensor : public RangeSensorComponent
{

public:
    UltrasonicSensor(omni::physx::IPhysx* physxPtr, carb::tasking::ITasking* taskingPtr);
    ~UltrasonicSensor();

    virtual void onStart();
    virtual void preTick();
    virtual void tick();
    virtual void onComponentChange();

    int getNumBins() const
    {
        return mNumBins;
    }
    int getNumCols() const
    {
        return mCols;
    }
    int getNumRows() const
    {
        return mRows;
    }
    int getNumEmitters() const
    {
        // TODO make this return without casting
        return static_cast<int>(mEmitters.size());
    }
    // std::vector<uint16_t>& getDepthData() { return mLastDepth[3]; }
    std::vector<uint16_t>& getDepthData(int emitterIndex)
    {
        return mEmitters[emitterIndex]->mDepth;
    }

    std::vector<float>& getLinearDepthData(int emitterIndex)
    {
        return mEmitters[emitterIndex]->mLinearDepth;
    }

    std::vector<float>& getEnvelope(int emitterIndex)
    {
        return mEmitters[emitterIndex]->getEnvelope();
    }

    std::vector<std::vector<float>> getEnvelopeArray()
    {
        std::vector<std::vector<float>> env;
        for (size_t i = 0; i < mEmitters.size(); i++)
        {
            env.push_back(mEmitters[i]->getEnvelope());
        }
        return env;
    }

    std::vector<std::vector<float>> getActiveEnvelopeArray()
    {
        const UltrasonicFiringGroup& group = mFiringGroups[mCurrentFiringGroup];
        std::vector<std::vector<float>> envelopes;
        for (size_t i = 0; i < mEmitters.size(); i++)
        {
            if (group.mIsReceiving[mFreqIdLow][i])
            {
                envelopes.push_back(mEmitters[i]->getEnvelopeLow());
            }
            if (group.mIsReceiving[mFreqIdHigh][i])
            {
                envelopes.push_back(mEmitters[i]->getEnvelopeHigh());
            }
        }
        return envelopes;
    }

    std::vector<float> getEnvelopeArrayFlattened()
    {
        auto envArray = getEnvelopeArray();
        std::vector<float> flattenedEnvelope;
        for (size_t i = 0; i < envArray.size(); i++)
        {
            for (int j = 0; j < mNumBins; j++)
            {
                flattenedEnvelope.push_back(envArray[i][j]);
            }
        }
        return flattenedEnvelope;
    }
    std::vector<uint8_t>& getIntensityData(int emitterIndex)
    {
        return mEmitters[emitterIndex]->mIntensity;
    }

    std::vector<carb::Int2> getEmitterFiringInfo()
    {
        const UltrasonicFiringGroup& group = mFiringGroups[mCurrentFiringGroup];

        std::vector<carb::Int2> info;
        for (size_t i = 0; i < mEmitters.size(); i++)
        {
            if (group.mIsFiring[mFreqIdLow][i])
            {
                info.push_back(carb::Int2({ static_cast<int>(i), static_cast<int>(mFreqIdLow) }));
            }
            if (group.mIsFiring[mFreqIdHigh][i])
            {
                info.push_back(carb::Int2({ static_cast<int>(i), static_cast<int>(mFreqIdHigh) }));
            }
        }

        // for (size_t i = 0; i < group.mEmitterModes.size(); i++)
        // {
        //     info.push_back(carb::Int2({ group.mEmitterModes[i][0], group.mEmitterModes[i][1] }));
        // }
        return info;
    }
    std::vector<carb::Int2> getReceiverFiringInfo()
    {
        const UltrasonicFiringGroup& group = mFiringGroups[mCurrentFiringGroup];

        std::vector<carb::Int2> info;

        for (size_t i = 0; i < mEmitters.size(); i++)
        {
            if (group.mIsReceiving[mFreqIdLow][i])
            {
                info.push_back(carb::Int2({ static_cast<int>(i), static_cast<int>(mFreqIdLow) }));
            }
            if (group.mIsReceiving[mFreqIdHigh][i])
            {
                info.push_back(carb::Int2({ static_cast<int>(i), static_cast<int>(mFreqIdHigh) }));
            }
        }

        // for (size_t i = 0; i < group.mReceiverModes.size(); i++)
        // {
        //     info.push_back(carb::Int2({ group.mReceiverModes[i][0], group.mReceiverModes[i][1] }));
        // }
        return info;
    }

    // these (zenith and azimuth getters) are the same across all emitters on the sensor for now
    // in other words, all emitters have the same resolution, shape, etc
    std::vector<float>& getZenithData()
    {
        return mZenith;
    }
    std::vector<float>& getAzimuthData()
    {
        return mAzimuth;
    }

    virtual void onEmitterChange(const pxr::UsdPrim& prim);
    virtual void onFiringGroupChange(const pxr::UsdPrim& prim);

private:
    const size_t mFreqIdLow = 0;
    const size_t mFreqIdHigh = 1;

    // std::vector<std::vector<bool>> mIsReceiving; //(2, std::vector<bool>());
    // std::vector<std::vector<bool>> mIsFiring; //(2, std::vector<bool>());

    int mNumBins = 224;
    bool mUseBRDF = false;
    bool mUseUSSMaterialsForBRDF = false;
    float mHorizontalFov = 60.0f;
    float mVerticalFov = 30.0f;
    float mHorizontalResolution = 0.4f;
    float mVerticalResolution = 4.0f;

    // difference between m[min|max]Depth and m[min|max]Range is division by the units
    // mMinRange and mMaxRange are defined in parent component
    float mMinDepth = 0;
    float mMaxDepth = 100000; // 100 m in cm

    int mRows; // = 0,
    int mCols; // = 0;

    std::vector<float> mZenith;
    std::vector<float> mAzimuth;


    std::vector<std::unique_ptr<UltrasonicEmitter>> mEmitters;
    std::vector<UltrasonicFiringGroup> mFiringGroups;
    std::vector<std::vector<USSEnvelope>> mEnvelopeList; // List of uss envelopes per firing mode
    UltrasonicReceiverArray mReceiverArray;
    size_t mCurrentFiringGroup = 0;

    std::vector<std::vector<::physx::PxVec3>> mWorldPoints;
    std::vector<std::vector<::physx::PxVec3>> mNormals;
    std::vector<std::vector<::physx::PxVec4>> mWorldMaterials;

    std::vector<std::vector<uint8_t>> mAdjacency;

    void dumpData(double dt);
    void clampRangeBounds();
    void updateDepthBounds();

    carb::tasking::ITasking* mTasking = nullptr;
    carb::tasking::Counter* mTaskCounter = nullptr;
};


}
}
}
