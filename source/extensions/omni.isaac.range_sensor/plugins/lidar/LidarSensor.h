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

#include <extensions/PxSceneQueryExt.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <pxr/base/gf/vec3f.h>
#include <pxr/usd/usd/inherits.h>
#include <rangeSensorSchema/lidar.h>

#include <vector>

namespace omni
{
namespace isaac
{
namespace range_sensor
{

class LidarSensor : public RangeSensorComponent
{

public:
    LidarSensor(omni::physx::IPhysx* physxPtr, carb::fastcache::FastCache* fastCachePtr);
    ~LidarSensor();

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

    int getNumColsTicked() const
    {
        return mLastNumColsTicked;
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


private:
    void dumpData(int start, int stop, double elapsedTime);

    // From the prim
    float mRotationRate = 20.0f;
    bool mHighLod = true;

    // Ranges converted to proper units
    float mMinDepth = 0;
    float mMaxDepth = 1e8;
    float mMaxStepSize = 0;
    int mMaxColsPerTick = 0;
    int mLastCol = 0;
    float mColScanSpeed = 0;
    double mRemainingTime = 0;


    int mRows = 0, mCols = 0;
    int mLastNumColsTicked = 0;

    std::vector<float> mZenith;
    std::vector<float> mAzimuth, mLastAzimuth;

    std::vector<float> mLinearDepth, mLastLinearDepth;
    std::vector<uint8_t> mIntensity, mLastIntensity;

    std::vector<uint16_t> mDepth, mLastDepth;
    std::vector<carb::Float3> mHitPos;
};


}
}
}
