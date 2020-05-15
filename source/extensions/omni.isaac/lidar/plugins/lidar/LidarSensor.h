// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once


#include "../core/SensorComponent.h"
#include "LidarDebug.h"

#include <carb/fastcache/FastCache.h>
#include <carb/physx/physx.h>
#include <carb/renderer/Renderer.h>

#include <LidarSchema/lidar.h>
#include <pxr/base/gf/vec3f.h>
#include <pxr/usd/usd/inherits.h>

#include <PxActor.h>
#include <PxArticulationJointReducedCoordinate.h>
#include <PxArticulationLink.h>
#include <PxArticulationReducedCoordinate.h>
#include <PxPhysicsAPI.h>
#include <PxRigidDynamic.h>
#include <PxScene.h>
#include <vector>

namespace omni
{
namespace isaac
{
namespace lidar
{

class LidarSensor : public SensorComponent<pxr::LidarSchemaLidar>
{

public:
    LidarSensor();
    ~LidarSensor();
    virtual void initialize(carb::physics::PhysX* physxPtr,
                            carb::fastcache::FastCache* fastCachePtr,
                            const pxr::LidarSchemaLidar& prim,
                            pxr::UsdStageRefPtr stage);
    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();

    bool getDrawLidarPoints()
    {
        return mDrawLidarPoints;
    }

    std::vector<DebugData>& getDebugLines()
    {
        return mDebugLines;
    }

    pxr::LidarSchemaLidar& getPrim()
    {
        return mPrim;
    }

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
    void dumpData(int start, int stop, float elapsedTime);

    // From the prim
    float mHorizontalFov = 360.0f;
    float mVerticalFov = 30.0f;
    float mRotationRate = 20.0f;
    float mHorizontalResolution = 0.4f;
    float mVerticalResolution = 4.0f;
    float mMinRange = 0.4f;
    float mMaxRange = 100.0f;
    bool mHighLod = true;
    bool mDrawLidarPoints = false;
    float mYawOffset = 0.0f;

    // Ranges converted to proper units
    float mMinDepth;
    float mMaxDepth;

    float mMaxStepSize;

    int mRows, mCols;
    int mMaxColsPerTick;

    int mLastCol;
    int mLastNumColsTicked;
    float mColScanSpeed;

    float mRemainingTime;

    std::vector<uint16_t> mDepth;
    std::vector<uint8_t> mIntensity;

    std::vector<float> mZenith;
    std::vector<float> mAzimuth;

    std::vector<uint16_t> mLastDepth;
    std::vector<uint8_t> mLastIntensity;
    std::vector<float> mLastAzimuth;

    std::set<int> mActiveDebugLines;
    carb::fastcache::FastCache* mFastCachePtr = nullptr;

    std::vector<omni::isaac::lidar::DebugData> mDebugLines;

    carb::physics::PhysX* mPhysx = nullptr;
    physx::PxScene* mPxScene = nullptr;
    float mMetersPerUnit;
};


}
}
}
