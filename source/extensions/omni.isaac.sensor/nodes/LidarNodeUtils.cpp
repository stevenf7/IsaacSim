// Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "LidarNodeUtils.h"

#include <carb/Framework.h>

#include <internal/omni/sensors/lidar/LidarSettings.h>
#include <omni/math/linalg/matrix.h>
#include <omni/math/linalg/quat.h>
#include <omni/math/linalg/vec.h>
#include <omni/sensors/lidar/ILidarProfileReaderFactory.h>


void getTransformFromLidarAsyncParameter(const LidarAsyncParameter& parm, omni::math::linalg::matrix4d& matrixOutput)
{
    // async.pose is [X, Y, Z, W].
    // quatd is i,j,k,w, but constructor is quatd(w, i, j, k)
    omni::math::linalg::vec3d posM{ parm.frameEnd.posM[0], parm.frameEnd.posM[1], parm.frameEnd.posM[2] };
    omni::math::linalg::quatd pose{ parm.frameEnd.orientation[3], parm.frameEnd.orientation[0],
                                    parm.frameEnd.orientation[1], parm.frameEnd.orientation[2] };
    matrixOutput.SetIdentity();
    matrixOutput.SetRotateOnly(pose);
    matrixOutput.SetTranslateOnly(posM);
}

// if inConfig and config are different, then the profile needs to be updated, and if there is an error, then
void updateLidarConfig(std::string inConfig,
                       std::string& config,
                       LidarScanType& scanType,
                       LidarRotaryProfile& rotaryProfile,
                       LidarSolidStateProfile& solidStateProfile)
{
    if (inConfig == config)
    {
        return;
    }

    config = inConfig;

    if (config == "")
    {
        scanType = LidarScanType::kUnknown;
        return;
    }

    const std::string json = omni::sensors::nv::lidar::getProfileJsonAtPaths(inConfig);
    omni::sensors::lidar::ILidarProfileReaderPtr profileReader =
        carb::getCachedInterface<omni::sensors::lidar::ILidarProfileReaderFactory>()->createInstance();

    if (profileReader)
    {
        profileReader->init(json.c_str());
        scanType = profileReader->lidarScanType();
        bool updated{ false };
        if (scanType == LidarScanType::kSolidState)
        {
            updated = profileReader->update((void*)&solidStateProfile);
        }
        else if (scanType == LidarScanType::kRotary)
        {
            updated = profileReader->update((void*)&rotaryProfile);
        }
        if (!updated)
        {
            scanType = LidarScanType::kUnknown;
        }
    }
    else
    {
        scanType = LidarScanType::kUnknown;
    }
}
