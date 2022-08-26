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

#include "../Core/IsaacComponent.h"

#include <carb/Framework.h>
#include <carb/InterfaceUtils.h>
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
namespace robot_engine_bridge
{

LidarComponent::LidarComponent() : IsaacComponent()
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
        CARB_LOG_ERROR("Prim is not a Lidar Prim");
        return;
    }
    pxr::RangeSensorSchemaLidar lidarPrim = pxr::RangeSensorSchemaLidar(prim);
    if (!mLidarSensorInterface->isLidarSensor(mLidarPath.GetString().c_str()))
    {
        CARB_LOG_ERROR("Prim is not registered with Lidar extension");
        return;
    }

    // Create the message
    IsaacMessage<isaac_message::RangeScan> scanMessage;

    auto scanMessageProto = scanMessage.initProto();

    int numColsTicked = mLidarSensorInterface->getNumColsTicked(mLidarPath.GetString().c_str());
    int numRows = mLidarSensorInterface->getNumRows(mLidarPath.GetString().c_str());
    int numBeams = numColsTicked * numRows;

    // Initialize the ranges tensor
    auto rangesTensor = scanMessageProto.initRanges();
    rangesTensor.setElementType(ElementType::UINT16);
    rangesTensor.initSizes(2);
    rangesTensor.setSizes({ numColsTicked, numRows });
    rangesTensor.setScanlineStride(0);
    rangesTensor.setDataBufferIndex(0);

    // Initialize the intensities tensor
    auto intensities = scanMessageProto.initIntensities();
    intensities.setElementType(ElementType::UINT8);
    intensities.initSizes(1);
    intensities.setSizes({ 0 });
    intensities.setScanlineStride(0);
    intensities.setDataBufferIndex(1);

    float* theta = mLidarSensorInterface->getAzimuthData(mLidarPath.GetString().c_str());
    float* phi = mLidarSensorInterface->getZenithData(mLidarPath.GetString().c_str());
    uint16_t* ranges = mLidarSensorInterface->getDepthData(mLidarPath.GetString().c_str());

    float maxRange = 100;
    isaac::utils::safeGetAttribute(lidarPrim.GetMaxRangeAttr(), maxRange);

    scanMessageProto.setTheta(kj::ArrayPtr<const float>(theta, theta + numColsTicked));
    scanMessageProto.setPhi(kj::ArrayPtr<const float>(phi, phi + numRows));

    scanMessageProto.setRangeDenormalizer(maxRange);
    scanMessageProto.setIntensityDenormalizer(1.0f);
    scanMessageProto.setDeltaTime(0);
    scanMessageProto.setInvalidRangeThreshold(0.0);
    scanMessageProto.setOutOfRangeThreshold(maxRange);

    std::vector<std::unique_ptr<IsaacBuffer>> buffers(1);
    buffers[0] = std::make_unique<IsaacHostBuffer>(numBeams * sizeof(uint16_t));
    std::memcpy(buffers[0]->data(), ranges, numBeams * sizeof(uint16_t));
    publish(mOutputComponent, mScanChannelName, scanMessage, buffers);
}
void LidarComponent::onComponentChange()
{
    // CARB_LOG_ERROR("LidarComponent Update");
    IsaacComponent::onComponentChange();

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
