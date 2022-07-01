// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../Core/IsaacComponent.h"

#include <carb/Types.h>
#include <carb/fastcache/FastCache.h>

#include <omni/isaac/occupancy_map/MapGenerator.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <omni/timeline/ITimeline.h>
#include <robotEngineBridgeSchema/robotEngineOccupancyGridMap.h>

#include <string>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{
class OccupancyGridMapComponent : public IsaacComponent
{
public:
    /**
     * @brief Construct a new ogm Component object
     *
     * @param appHandle
     * @param prim
     * @param stage
     */
    OccupancyGridMapComponent();

    /**
     * @brief Destroy the ogm Component object
     *
     */
    ~OccupancyGridMapComponent();


    /**
     * @brief The ogm pointer might not be valid, so force update on start
     *
     */
    virtual void onStart();

    /**
     * @brief
     *
     */
    virtual void tick();

    /**
     * @brief
     *
     */
    virtual void publishAllMessages();

    /**
     * @brief
     *
     */
    virtual void onComponentChange();

private:
    /// The name of the channel on which state informations is published
    std::string mOutputComponent = "output";
    std::string mChannelName = "occupancy_map";
    pxr::GfVec3f mOffset = pxr::GfVec3f(0, 0, 0);
    float mCellSize = 0.1;
    float mDegreesPerRay = 5;
    float mSurfaceOffset = 0.02;
    float mOccupancyThreshold = 1.0;
    int mMaxRays = 1000000;
    pxr::GfVec2i mMapSize = pxr::GfVec2i(256, 256);
    pxr::SdfPath mParentPrimPath = pxr::SdfPath("/");
    pxr::UsdPrim mParentPrim;
    std::unique_ptr<omni::isaac::occupancy_map::MapGenerator> mGenerator = nullptr;
    omni::physx::IPhysx* mPhysx = nullptr;
    carb::fastcache::FastCache* mFastCachePtr = nullptr;
    omni::timeline::ITimeline* mTimeline = nullptr;

    bool mSkipFirstFrame = true;
    bool mDebugDraw = false;

    float mOccupiedValue = 1.0;
    float mUnoccupiedValue = 0.0;
    float mUnknownValue = 0.5;
    float mStageUnits = 1;
};
}
}
}
