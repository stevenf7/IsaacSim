// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
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

#include "LidarComponent.h"

#include "../Core/GxfComponent.h"
#include "gems/composite/composite_from_tensor.hpp"
#include "gems/range_scan/range_scan_types.hpp"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/logging/Log.h>
#include <carb/profiler/Profile.h>

#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <rangeSensorSchema/lidar.h>

#include <string>
#include <vector>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge_gxf
{

LidarComponent::LidarComponent() : GxfComponent()
{


    mLidarSensorInterface = carb::getCachedInterface<omni::isaac::range_sensor::LidarSensorInterface>();
    if (!mLidarSensorInterface)
    {
        CARB_LOG_ERROR("Failed to acquire omni::isaac::range_sensor interface");
        return;
    }
}

LidarComponent::~LidarComponent()
{
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

    // Fill in pose uid
    const std::string path = mLidarPath.GetString();
    auto maybeUid = mPoseTreeMap->findOrCreateNamedFrame(path);
    if (!maybeUid)
    {
        CARB_LOG_WARN("Cannot find pose uid for lidar %s", path.c_str());
        return;
    }

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

    int numHorizontalAngles = mLidarSensorInterface->getNumColsTicked(mLidarPath.GetString().c_str());
    int numVerticalAngles = mLidarSensorInterface->getNumRows(mLidarPath.GetString().c_str());
    int numBeams = numHorizontalAngles * numVerticalAngles;

    // Create the message
    auto maybe_message = nvidia::isaac::CreateRangeScanMessage(mContext, mAllocator, numBeams);
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
    isaac::utils::safeGetAttribute(lidarPrim.GetMaxRangeAttr(), maxRange);

    for (int i = 0, ray_idx = 0; i < numHorizontalAngles; i++)
    {
        for (int j = 0; j < numVerticalAngles; j++, ray_idx++)
        {
            auto maybe_beam =
                nvidia::isaac::CompositeFromTensor<nvidia::isaac::RangeScanView<float>>(message.beams.slice(ray_idx));
            if (!maybe_beam)
            {
                CARB_LOG_ERROR("could not create RangeScanView for ray %d, %d", ray_idx, maybe_message.error());
                return;
            }
            nvidia::isaac::RangeScanView<float>& beam = maybe_beam.value();
            // TODO: fill this from spinning lidar model
            beam.relative_time() = 0.0;
            beam.horizontal_angle() = theta[i];
            beam.vertical_angle() = -phi[j];
            beam.range() = ranges[ray_idx];
            // TODO: use getIntensityData()
            beam.intensity() = 1.0;
        }
    }

    // Fill in meta data
    message.info->delta_time = 0.0;
    message.info->invalid_range = 0.0;
    message.info->out_of_range = static_cast<double>(maxRange);

    message.pose_frame_uid->uid = maybeUid.value();
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
