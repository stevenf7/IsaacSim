// Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <omni/math/linalg/matrix.h>
#include <omni/sensors/lidar/LidarParameterType.h>
#include <omni/sensors/lidar/LidarProfileTypes.h>

void getTransformFromLidarAsyncParameter(const LidarAsyncParameter& parm, omni::math::linalg::matrix4d& matrixOutput);
bool updateLidarConfig(std::string inConfig,
                       std::string& config,
                       LidarScanType& scanType,
                       LidarRotaryProfile& rotaryProfile,
                       LidarSolidStateProfile& solidStateProfile);
