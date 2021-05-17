// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

#include <stdint.h>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge_gxf
{

struct GxfBridge
{
    CARB_PLUGIN_INTERFACE("omni::isaac::robot_engine_bridge_gxf::GxfBridge", 0, 1);
    bool(CARB_ABI* createApplication)(const std::string& basePath,
                                      const std::string& manifestFile,
                                      const std::vector<std::string>& graphFiles);
    bool(CARB_ABI* destroyApplication)();
    bool(CARB_ABI* tickComponent)(const std::string& primPath);
    bool(CARB_ABI* executeCommand)(const std::string& command);
};
}
}
}
