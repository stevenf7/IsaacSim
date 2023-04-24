// Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <omni/isaac/partition/IsaacPartition.h>

// clang-format off
#include <carb/Defines.h>
#include <omni/usd/UsdUtils.h>

#include <string>
#include <vector>
// clang-format on

namespace omni
{
namespace isaac
{
class IsaacPartitionProcessor final : public IsaacPartition
{
public:
    IsaacPartitionProcessor() = default;
    virtual ~IsaacPartitionProcessor() = default;

    // IsaacPartition Interface
    void setExportPath(const char* filePath);
    char const* getExportPath();
    void clearCameras();
    void addCameraPath(const char* cameraPath);
    size_t numCameraPaths();
    const char* getCameraPath(size_t index);
    void saveToUsd();

    // Utilities
    std::string getExportFileName() const;
    std::string getExportExtension() const;
    std::string getPartitionFileName(const std::string& partition) const;

    long int mStageId{ 0 };
    double mMetersPerUnit{ 1.0 };
    std::vector<std::string> mCameras{};
    std::string mExportFileName{};
};
}
}
