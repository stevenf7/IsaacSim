// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once


#include "../core/RangeSensorComponent.h"
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
        return mDepth[emitterIndex];
    }
    std::vector<float>& getLinearDepthData(int emitterIndex)
    {
        return mLastLinearDepth[emitterIndex];
    }
    std::vector<uint8_t>& getIntensityData(int emitterIndex)
    {
        return mLastIntensity[emitterIndex];
    }
    // these are the same across all sensors for now
    std::vector<float>& getZenithData()
    {
        return mLastZenith;
    }
    std::vector<float>& getAzimuthData()
    {
        return mLastAzimuth;
    }

private:
    UltrasonicEmitter emitter;
    const static size_t NUM_EMITTERS = 8;
    float mHorizontalFov = 60.0f;
    float mVerticalFov = 30.0f;
    float mHorizontalResolution = 0.4f;
    float mVerticalResolution = 4.0f;


    float mMinDepth = 0;
    float mMaxDepth = 1e8;
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

    std::vector<std::vector<float>> mLinearDepth;
    std::vector<std::vector<float>> mLastLinearDepth;
    std::vector<std::vector<uint8_t>> mIntensity;
    std::vector<std::vector<uint8_t>> mLastIntensity;

    std::vector<std::vector<uint16_t>> mDepth;
    std::vector<std::vector<uint16_t>> mLastDepth;
    std::vector<std::vector<carb::Float3>> mHitPos;
    std::vector<std::vector<carb::Float3>> mLastHitPos;
    std::vector<std::vector<omni::isaac::range_sensor::DebugData>> mEmitterDebugLines;

    void dumpData(double dt);
};


}
}
}
