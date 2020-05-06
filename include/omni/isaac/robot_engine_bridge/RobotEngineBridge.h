// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
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

#include <stdint.h>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

struct RobotEngineBridge
{
    CARB_PLUGIN_INTERFACE("omni::isaac::robot_engine_bridge::RobotEngineBridge", 0, 1);

    void(CARB_ABI* createApplication)(std::string asset_path,
                                      std::string app_file,
                                      std::vector<const char*> module_paths,
                                      std::vector<const char*> json_files);
    void(CARB_ABI* destroyApplication)();
    std::string const(CARB_ABI* getLastError)();
    void(CARB_ABI* initializeStageLoader)(std::string inputComponent,
                                          std::string requestChannelName,
                                          std::string outputComponent,
                                          std::string replyChannelName);
};
}
}
}
