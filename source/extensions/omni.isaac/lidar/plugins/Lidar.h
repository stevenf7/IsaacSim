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
    Lidar()
    {
    }
    Lidar(const pxr::LidarSchemaLidar& prim);
    ~Lidar();


    void init(const pxr::LidarSchemaLidar& prim);

    SdfPath getPath() const
    {
        return prim.GetPath();
    }

    float getHorizontalFov() const
    {
        return horizontalFov;
    }

    float getVerticalFov() const
    {
        return verticalFov;
    }

    float getRotationRate() const
    {
        return rotationRate;
    }

    float getHorizontalResolution() const
    {
        return horizontalResolution;
    }

    float getVerticalResolution() const
    {
        return verticalResolution;
    }

    float getMinRange() const
    {
        return minRange;
    }

    float getMaxRange() const
    {
        return maxRange;
    }

    bool getHighLod() const
    {
        return highLod;
    }

    bool getDrawLidarPoints() const
    {
        return drawLidarPoints;
    }


    void update(float elapsedTime);


    int getNumCols() const
    {
        return cols;
    }

    int getNumRows() const
    {
        return rows;
    }

    int getLastNumColsTicked() const
    {
        return lastNumColsTicked;
    }

    std::vector<uint16_t>& getLastDepthData()
    {
        return lastDepth;
    }

    std::vector<uint8_t>& getLastIntensityData()
    {
        return lastIntensity;
    }

    std::vector<float>& getLastZenithData()
    {
        return zenith;
    }

    std::vector<float>& getLastAzimuthData()
    {
        return lastAzimuth;
    }


private:
    void addDebugLine(const pxr::GfVec3f& pointA, const pxr::GfVec3f& pointB, const pxr::GfVec3f& color, const int index);
    void clearDebugLines();

    void scan(int start, int stop);
    void dumpData(int start, int stop, float elapsedTime);


    pxr::LidarSchemaLidar prim;

    bool valid;

    // From the prim
    float horizontalFov;
    float verticalFov;
    float rotationRate;
    float horizontalResolution;
    float verticalResolution;
    float minRange;
    float maxRange;
    bool highLod;
    bool drawLidarPoints;

    // Ranges converted to proper units
    float minDepth;
    float maxDepth;

    float maxStepSize;

    int rows, cols;
    int maxColsPerTick;

    int lastCol;
    int lastNumColsTicked;
    float colScanSpeed;

    float remainingTime;

    std::vector<uint16_t> depth;
    std::vector<uint8_t> intensity;

    std::vector<float> zenith;
    std::vector<float> azimuth;

    std::vector<uint16_t> lastDepth;
    std::vector<uint8_t> lastIntensity;
    std::vector<float> lastAzimuth;

    std::set<int> activeDebugLines;
    carb::Framework* framework = nullptr;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    omni::isaac::dynamic_control::DcHandle mRigidBodyHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    // Gross
    // Did this because of linking issues with global variables in LidarInterface.cpp, being used as extern in Lidar.cpp
public:
    static carb::physics::PhysX* physx;
    static UsdStageRefPtr stage;
    static float metersPerUnit;
};


}
}
}
