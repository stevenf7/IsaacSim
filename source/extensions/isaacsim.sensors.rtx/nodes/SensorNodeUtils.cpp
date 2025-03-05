// Copyright (c) 2023-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "SensorNodeUtils.h"

#include "isaacsim/core/utils/UsdUtilities.h"

#include <carb/InterfaceUtils.h>

#include <omni/math/linalg/matrix.h>
#include <omni/math/linalg/quat.h>
#include <omni/math/linalg/vec.h>
#include <omni/sensors/IProfileReader.h>

namespace isaacsim
{
namespace sensors
{
namespace rtx
{

void getTransformFromSensorPose(const omni::sensors::FrameAtTime& inPose, omni::math::linalg::matrix4d& matrixOutput)
{
    // async.pose is [X, Y, Z, W].
    // quatd is i,j,k,w, but constructor is quatd(w, i, j, k)
    omni::math::linalg::vec3d posM{ inPose.posM[0], inPose.posM[1], inPose.posM[2] };
    omni::math::linalg::quatd pose{ inPose.orientation[3], inPose.orientation[0], inPose.orientation[1],
                                    inPose.orientation[2] };
    matrixOutput.SetIdentity();
    matrixOutput.SetRotateOnly(pose);
    matrixOutput.SetTranslateOnly(posM);
}
float LidarConfigHelper::getFarRange() const
{

    return this->profile->farRangeM;
}

float LidarConfigHelper::getNearRange() const
{
    return this->profile->nearRangeM;
}

uint32_t LidarConfigHelper::getNumChannels() const
{
    return this->profile->numberOfChannels;
}

uint32_t LidarConfigHelper::getNumEchos() const
{
    return this->profile->maxReturns;
}

uint32_t LidarConfigHelper::getReturnsPerScan() const
{
    return this->getNumEchos() * this->getNumChannels() * this->getTicksPerScan();
}

uint32_t LidarConfigHelper::getTicksPerScan() const
{
    return this->scanType == LidarScanType::kSolidState ?
               1 :
               this->profile->reportRateBaseHz / this->profile->scanRateBaseHz;
}
// if inConfig and config are different, then the profile needs to be updated, and if there is an error, then
// return true only if config was updated.
bool LidarConfigHelper::updateLidarConfig(const char* renderProductPath)
{
    std::string curConfig = "";
    pxr::UsdAttribute configAttr =
        isaacsim::core::utils::getCameraAttributeFromRenderProduct("sensorModelConfig", renderProductPath);
    if (!configAttr.IsValid())
    {
        return false;
    }
    isaacsim::core::utils::safeGetAttribute(configAttr, curConfig);

    if (this->config == curConfig)
    {
        return false;
    }

    this->config = curConfig;

    if (this->config.empty())
    {
        this->scanType = LidarScanType::kUnknown;
        return false;
    }

    omni::sensors::IProfileReaderPtr profileReader =
        carb::getFramework()->acquireInterface<omni::sensors::IProfileReaderFactory>()->createInstance();
    const auto json = profileReader->getProfileJsonAtPaths(curConfig.c_str(), ProfileType::LIDAR);
    profileReader->init(json.c_str(), ProfileType::LIDAR);
    const auto dataSize = profileReader->dataSizeProfile();
    this->profileBuffer.resize(dataSize);
    bool updated = profileReader->update((void*)this->profileBuffer.data());
    profileReader->release();
    if (updated)
    {
        this->profile = reinterpret_cast<LidarProfile*>(profileBuffer.data());
        this->scanType = this->profile->scanType;
    }
    else
    {
        this->scanType = LidarScanType::kUnknown;
    }

    return updated;
}
}
}
}
