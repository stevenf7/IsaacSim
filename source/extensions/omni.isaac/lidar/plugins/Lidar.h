// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once


#include <carb/physx/physx.h>
#include <carb/renderer/Renderer.h>

#include <LidarSchema/lidar.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <pxr/base/gf/vec3f.h>
#include <pxr/usd/usd/inherits.h>

#include <PxActor.h>
#include <PxArticulationJointReducedCoordinate.h>
#include <PxArticulationLink.h>
#include <PxArticulationReducedCoordinate.h>
#include <PxRigidDynamic.h>
#include <PxScene.h>
#include <vector>


using namespace pxr;


namespace omni
{
namespace isaac
{
namespace lidar
{

struct Lidar
{

public:
    Lidar(carb::physics::PhysX* physx_ptr,
          omni::isaac::dynamic_control::DynamicControl* dc_ptr,
          const pxr::LidarSchemaLidar& prim,
          float metersPerUnit);
    Lidar()
    {
    }
    ~Lidar();


    void init(const pxr::LidarSchemaLidar& prim);

    SdfPath getPath() const
    {
        return mPrim.GetPath();
    }

    float getHorizontalFov() const
    {
        return mHorizontalFov;
    }

    float getVerticalFov() const
    {
        return mVerticalFov;
    }

    float getRotationRate() const
    {
        return mRotationRate;
    }

    float getHorizontalResolution() const
    {
        return mHorizontalResolution;
    }

    float getVerticalResolution() const
    {
        return mVerticalResolution;
    }

    float getMinRange() const
    {
        return mMinRange;
    }

    float getMaxRange() const
    {
        return mMaxRange;
    }

    bool getHighLod() const
    {
        return mHighLod;
    }

    bool getDrawLidarPoints() const
    {
        return mDrawLidarPoints;
    }


    void update(float elapsedTime);


    int getNumCols() const
    {
        return mCols;
    }

    int getNumRows() const
    {
        return mRows;
    }

    int getLastNumColsTicked() const
    {
        return mLastNumColsTicked;
    }

    std::vector<uint16_t>& getLastDepthData()
    {
        return mLastDepth;
    }

    std::vector<uint8_t>& getLastIntensityData()
    {
        return mLastIntensity;
    }

    std::vector<float>& getLastZenithData()
    {
        return mZenith;
    }

    std::vector<float>& getLastAzimuthData()
    {
        return mLastAzimuth;
    }

    std::vector<carb::renderer::Line>& getDebugLines()
    {
        return mDebugLines;
    }

    pxr::LidarSchemaLidar& getPrim()
    {
        return mPrim;
    }


private:
    void scan(int start, int stop);
    void dumpData(int start, int stop, float elapsedTime);


    pxr::LidarSchemaLidar mPrim;

    bool mValid;

    // From the prim
    float mHorizontalFov;
    float mVerticalFov;
    float mRotationRate;
    float mHorizontalResolution;
    float mVerticalResolution;
    float mMinRange;
    float mMaxRange;
    bool mHighLod;
    bool mDrawLidarPoints;

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
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    omni::isaac::dynamic_control::DcHandle mRigidBodyHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    std::vector<carb::renderer::Line> mDebugLines;

    carb::physics::PhysX* mPhysx = nullptr;
    UsdStageRefPtr mStage;
    float mMetersPerUnit;
};


}
}
}
