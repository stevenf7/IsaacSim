// Copyright (c) 2018-2022, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

namespace omni
{
namespace isaac
{
struct IsaacPartition
{
    CARB_PLUGIN_INTERFACE("omni::isaac::IsaacPartition", 1, 0)

    // Save to USD
    void(CARB_ABI* saveToUsd)() = 0;

    // Set the path to the file to export.
    void(CARB_ABI* setExportPath)(const char* filePath) = 0;

    // Get the path to the file to export.
    char const*(CARB_ABI* getExportPath)() = 0;

    // Clear all cameras.
    void(CARB_ABI* clearCameras)() = 0;

    // Add a camera path to the partition set.
    void(CARB_ABI* addCameraPath)(const char* cameraPath) = 0;

    // Count the number of cameras.
    size_t(CARB_ABI* numCameraPaths)() = 0;

    // Add a camera path to the partition set.
    const char*(CARB_ABI* getCameraPath)(size_t index) = 0;
};
} // isaac
} // omni
