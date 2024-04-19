// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
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

#include "SensorNodeUtils.h"

#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/InterfaceUtils.h>

#include <omni/math/linalg/matrix.h>
#include <omni/math/linalg/quat.h>
#include <omni/math/linalg/vec.h>
#include <omni/sensors/lidar/ILidarProfileReaderFactory.h>

namespace omni
{
namespace isaac
{
namespace sensor
{

void getTransformFromSensorPose(const omni::sensors::FrameAtTime& inPose, omni::math::linalg::matrix4d& matrixOutput)
{
    // async.pose is [X, Y, Z, W].
    // quatd is i,j,k,w, but constructor is quatd(w, i, j, k)
    omni::math::linalg::vec3d posM{ inPose.posM.x, inPose.posM.y, inPose.posM.z };
    omni::math::linalg::quatd pose{ inPose.orientation.w, inPose.orientation.x, inPose.orientation.y,
                                    inPose.orientation.z };
    matrixOutput.SetIdentity();
    matrixOutput.SetRotateOnly(pose);
    matrixOutput.SetTranslateOnly(posM);
}
float LidarConfigHelper::getFarRange() const
{

    return this->scanType == LidarScanType::kSolidState ? this->solidStateProfile.farRangeM :
                                                          this->rotaryProfile.farRangeM;
}

float LidarConfigHelper::getNearRange() const
{

    return this->scanType == LidarScanType::kSolidState ? this->solidStateProfile.nearRangeM :
                                                          this->rotaryProfile.nearRangeM;
}

uint32_t LidarConfigHelper::getNumChannels() const
{

    return this->scanType == LidarScanType::kSolidState ? this->solidStateProfile.numberOfChannels :
                                                          this->rotaryProfile.numberOfChannels;
}
uint32_t LidarConfigHelper::getNumEchos() const
{

    return this->scanType == LidarScanType::kSolidState ? this->solidStateProfile.maxReturns :
                                                          this->rotaryProfile.maxReturns;
}


uint32_t LidarConfigHelper::getReturnsPerScan() const
{
    return this->getNumEchos() * this->getNumChannels() * this->getTicksPerScan();
}


uint32_t LidarConfigHelper::getTicksPerScan() const
{
    return this->scanType == LidarScanType::kSolidState ?
               1 :

               this->rotaryProfile.reportRateBaseHz / this->rotaryProfile.scanRateBaseHz;
}
// if inConfig and config are different, then the profile needs to be updated, and if there is an error, then
// return true only if config was updated.
bool LidarConfigHelper::updateLidarConfig(const char* renderProductPath)
{
    std::string curConfig = "";
    pxr::UsdAttribute configAttr =
        omni::isaac::utils::getCameraAttributeFromRenderProduct("sensorModelConfig", renderProductPath);
    if (configAttr.IsValid())
    {
        omni::isaac::utils::safeGetAttribute(configAttr, curConfig);
    }
    if (curConfig == this->config)
    {
        return false;
    }

    this->config = curConfig;

    if (this->config == "")
    {
        this->scanType = LidarScanType::kUnknown;
        return false;
    }

    omni::sensors::lidar::ILidarProfileReaderPtr profileReader =
        carb::getCachedInterface<omni::sensors::lidar::ILidarProfileReaderFactory>()->createInstance();
    const auto json = profileReader->getProfileJsonAtPaths(curConfig.c_str());

    bool updated{ false };
    if (profileReader)
    {
        profileReader->init(json.c_str());
        this->scanType = profileReader->lidarScanType();
        if (this->scanType == LidarScanType::kSolidState)
        {
            updated = profileReader->update((void*)&this->solidStateProfile);
        }
        else if (this->scanType == LidarScanType::kRotary)
        {
            updated = profileReader->update((void*)&this->rotaryProfile);
        }
        if (!updated)
        {
            this->scanType = LidarScanType::kUnknown;
        }
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
