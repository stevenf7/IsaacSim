// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
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

#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <robotEngineBridgeSchema/robotEngineLidar.h>

#include <string>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{
class LidarComponent : public IsaacComponent
{
public:
    /**
     * @brief Construct a new Lidar Component object
     *
     * @param appHandle
     * @param prim
     * @param stage
     */
    LidarComponent();

    /**
     * @brief Destroy the Lidar Component object
     *
     */
    ~LidarComponent();


    /**
     * @brief The lidar pointer might not be valid, so force update on start
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
    omni::isaac::range_sensor::LidarSensorInterface* mLidarSensorInterface = nullptr;


    /// The name of the channel on which state informations is published
    std::string mOutputComponent = "output";
    std::string mScanChannelName = "rangescan";
    pxr::SdfPath mLidarPath = pxr::SdfPath("/");

    omni::isaac::range_sensor::RangeSensorHandle mLidarSensorHandle = omni::isaac::range_sensor::kInvalidHandle;
    bool mSkipFirstFrame = true;
};
}
}
}
