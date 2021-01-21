// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once


#include "../core/RangeSensorComponent.h"
#include "UltrasonicArrayEmissionTimer.h"
#include "UltrasonicEmitter.h"

#include <extensions/PxSceneQueryExt.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <pxr/base/gf/vec3f.h>
#include <pxr/usd/usd/inherits.h>
#include <rangeSensorSchema/ultrasonic.h>

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
    UltrasonicSensor(omni::physx::IPhysx* physxPtr, carb::fastcache::FastCache* fastCachePtr);
    ~UltrasonicSensor();

    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();

    int getNumBins() const
    {
        return NUM_BINS;
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
        return NUM_EMITTERS;
    }
    // std::vector<uint16_t>& getDepthData() { return mLastDepth[3]; }
    std::vector<uint16_t>& getDepthData(int emitterIndex)
    {
        return mEmitters[emitterIndex].mDepth;
    }
    std::vector<float>& getLinearDepthData(int emitterIndex)
    {
        return mEmitters[emitterIndex].mLastLinearDepth;
    }
    std::vector<float>& getEnvelope(int emitterIndex)
    {
        return mEmitters[emitterIndex].getEnvelope();
    }
    std::vector<std::vector<float>> getEnvelopeArray()
    {
        std::vector<std::vector<float>> env;
        for (size_t i = 0; i < mEmitters.size(); i++)
        {
            env.push_back(mEmitters[i].getEnvelope());
        }
        return env;
    }

    std::vector<float> getEnvelopeArrayFlattened()
    {
        auto envArray = getEnvelopeArray();
        std::vector<float> flattenedEnvelope;
        for (size_t i = 0; i < envArray.size(); i++)
        {
            for (size_t j = 0; j < NUM_BINS; j++)
            {
                flattenedEnvelope.push_back(envArray[i][j]);
            }
        }
        return flattenedEnvelope;
    }
    std::vector<uint8_t>& getIntensityData(int emitterIndex)
    {
        return mEmitters[emitterIndex].mLastIntensity;
    }

    // these (zenith and azimuth getters) are the same across all emitters on the sensor for now
    // in other words, all emitters have the same resolution, shape, etc
    std::vector<float>& getZenithData()
    {
        return mLastZenith;
    }
    std::vector<float>& getAzimuthData()
    {
        return mLastAzimuth;
    }

private:
    const static size_t NUM_EMITTERS = 12;
    const static size_t NUM_BINS = 224;
    float mHorizontalFov = 60.0f;
    float mVerticalFov = 30.0f;
    float mHorizontalResolution = 0.4f;
    float mVerticalResolution = 4.0f;


    // difference between m[min|max]Depth and m[min|max]Range is division by the units
    // mMinRange and mMaxRange are defined in parent component
    float mMinDepth;
    float mMaxDepth;
    float mMaxStepSize = 0;
    int mMaxColsPerTick = 0;
    int mLastCol = 0;
    float mRemainingTime = 0;

    int mRows; // = 0,
    int mCols; // = 0;

    std::vector<float> mZenith;
    std::vector<float> mAzimuth;
    std::vector<float> mLastAzimuth;
    std::vector<float> mLastZenith;


    UltrasonicArrayEmissionTimer mEmissionTimer;
    std::vector<UltrasonicEmitter> mEmitters;

    void dumpData(double dt);
    void clampRangeBounds();
    void updateDepthBounds();
};


}
}
}
