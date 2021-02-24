// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <vector>
#include <string>
#include <rangeSensorSchema/lidar.h>

#include "../Core/GxfComponent.h"

#include "LidarComponent.h"
#include <carb/logging/Log.h>
#include <carb/profiler/Profile.h>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{
namespace gxf_bridge
{
LidarComponent::LidarComponent() : GxfComponent()
{

    framework = carb::getFramework();
    if (!framework)
    {
        CARB_LOG_ERROR("*** Failed to get Carbonite framework\n");
        return;
    }

    mLidarSensorInterface = framework->acquireInterface<omni::isaac::range_sensor::LidarSensorInterface>();
    if (!mLidarSensorInterface)
    {
        CARB_LOG_ERROR("Failed to acquire omni::isaac::range_sensor interface");
        return;
    }
}

LidarComponent::~LidarComponent()
{
    framework->releaseInterface(mLidarSensorInterface);
}

void LidarComponent::onStart()
{
    onComponentChange();
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
    mSkipFirstFrame = true;
}
void LidarComponent::tick()
{
}

void LidarComponent::publishAllMessages()
{
    if (mSkipFirstFrame)
    {
        mSkipFirstFrame = false;
        return;
    }
    CARB_PROFILE_ZONE(0, "REB LidarComponent Tick");

    pxr::UsdPrim prim = mStage->GetPrimAtPath(mLidarPath);
    if (!prim.IsA<pxr::RangeSensorSchemaLidar>())
    {
        CARB_LOG_ERROR("Prim is not a USS Prim");
        return;
    }
    pxr::RangeSensorSchemaLidar lidarPrim = pxr::RangeSensorSchemaLidar(prim);
    if (!mLidarSensorInterface->isLidarSensor(mLidarPath.GetString().c_str()))
    {
        CARB_LOG_ERROR("Prim is not registered with USS extension");
        return;
    }

    int numColsTicked = mLidarSensorInterface->getNumColsTicked(mLidarPath.GetString().c_str());
    int numRows = mLidarSensorInterface->getNumRows(mLidarPath.GetString().c_str());
    // int numBeams = numColsTicked * numRows;

    // Create the message
    auto maybe_message = nvidia::isaac::CreateRangescanMessage(
        mContext, mAllocator, numColsTicked /* horizontal angles */, numRows /* vertical angles */);
    if (!maybe_message)
    {
        // return maybe_message.error();
        CARB_LOG_ERROR("could not create range scan message, %d", maybe_message.error());
        return;
    }
    auto message = std::move(maybe_message.value());

    // Fill in tensors
    float* theta = mLidarSensorInterface->getAzimuthData(mLidarPath.GetString().c_str());
    float* phi = mLidarSensorInterface->getZenithData(mLidarPath.GetString().c_str());
    float* ranges = mLidarSensorInterface->getLinearDepthData(mLidarPath.GetString().c_str());

    float maxRange = 100;
    if (lidarPrim.GetMaxRangeAttr().HasValue())
    {
        lidarPrim.GetMaxRangeAttr().Get(&maxRange);
    }

    for (int i = 0; i < numColsTicked; i++)
    {
        message.horizontal_angles(i) = static_cast<double>(theta[i]);
    }
    for (int j = 0; j < numRows; j++)
    {
        message.vertical_angles(j) = static_cast<double>(phi[j]);
    }
    for (int i = 0; i < numColsTicked; i++)
    {
        for (int j = 0; j < numRows; j++)
        {
            message.ranges(i, j) = static_cast<double>(ranges[i * numRows + j]);
            // TODO: use getIntensityData()
            message.intensities(i, j) = 1.0;
        }
    }

    // Fill in meta data
    message.info->range_denormalizer = 1.0;
    message.info->intensity_denormalizer = 1.0;
    message.info->delta_time = 0.0;
    message.info->invalid_range = 0.0;
    message.info->out_of_range = static_cast<double>(maxRange);
    // TODO: get pose uid from pose tree
    message.pose_frame_uid->uid = 0u;
    message.timestamp->acqtime = this->mTimeNanoSeconds + mComponentTimeOffsetNanoSeconds;
    message.timestamp->pubtime = ::isaac::NowCount();

    publish(mOutputComponent, mScanChannelName, std::move(message.entity));
}
void LidarComponent::onComponentChange()
{
    // CARB_LOG_ERROR("LidarComponent Update");
    GxfComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEngineLidar& typedPrim = (pxr::RobotEngineBridgeSchemaRobotEngineLidar)mPrim;
    isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mScanChannelName);

    pxr::SdfPathVector targets;
    typedPrim.GetLidarPrimRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        return;
    }
    mLidarPath = targets[0];
}
}
}
}
}
