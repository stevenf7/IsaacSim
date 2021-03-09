// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once


#include "../core/RangeSensorComponent.h"

#include <extensions/PxSceneQueryExt.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <pxr/base/gf/vec3f.h>
#include <pxr/usd/usd/inherits.h>
#include <rangeSensorSchema/generic.h>

#include <vector>

namespace omni
{
namespace isaac
{
namespace range_sensor
{

class GenericSensor : public RangeSensorComponent
{

public:
    GenericSensor(omni::physx::IPhysx* physxPtr, carb::fastcache::FastCache* fastCachePtr);
    ~GenericSensor();

    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();


    int getNumSamplesTicked() const
    {
        return mSamplesPerTick;
    }
    std::vector<uint16_t>& getDepthData()
    {
        return mLastDepth;
    }

    std::vector<float>& getLinearDepthData()
    {
        return mLastLinearDepth;
    }

    std::vector<uint8_t>& getIntensityData()
    {
        return mLastIntensity;
    }

    std::vector<float>& getZenithData()
    {
        return mZenith;
    }

    std::vector<float>& getAzimuthData()
    {
        return mLastAzimuth;
    }

    std::vector<carb::Float3>& getHitPosData()
    {
        return mLastHitPos;
    }
    std::vector<carb::Float3>& getOffsetData()
    {
        return mLastOffset;
    }


    bool sendNextBatch();
    /**
     * @brief indicate whether the next batch of sensor pattern vectors should be sent
     *
     */

    void setNextBatchRays(const float* azimuth_angles, const float* zenith_angles, const int sample_length);
    /**
     *  @brief passing in the next batch of sensor pattern
     */

    void setNextBatchOffsets(const float* origin_offsets, const int sample_length);
    /**
     *  @brief if each ray has its own offset
     */


private:
    void wrapData(int start);
    void dumpData();

    int mSamplingRate; // number of samples per second
    int mBatchSize = 0; // the total number of samples for each batch of data
    int minBatchSize = 0;

    int mLastSample = 0;
    int mSamplesPerTick = 60; // number of samples per tick
    int maxSamplesPerTick = 1000000;

    float mMinDepth = 0;
    float mMaxDepth = 1e8;

    std::vector<float> mAzimuth_A{}, mAzimuth_B{};
    std::vector<float> mZenith_A{}, mZenith_B{};
    std::vector<carb::Float3> mOffset_A{}, mOffset_B{};
    // bool mCustomOffset = false;


    float *pActiveAzimuth, *pActiveZenith;
    carb::Float3* pActiveOffset;

    std::vector<float> mZenith, mLastZenith;
    std::vector<float> mAzimuth, mLastAzimuth;
    std::vector<carb::Float3> mOffset, mLastOffset;

    std::vector<float> mLinearDepth, mLastLinearDepth;
    std::vector<uint8_t> mIntensity, mLastIntensity;
    std::vector<uint16_t> mDepth, mLastDepth;
    std::vector<carb::Float3> mHitPos, mLastHitPos;
};


}
}
}
