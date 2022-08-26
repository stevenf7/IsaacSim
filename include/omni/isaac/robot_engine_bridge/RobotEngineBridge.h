// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
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
namespace robot_engine_bridge
{

struct RobotEngineBridge
{
    CARB_PLUGIN_INTERFACE("omni::isaac::robot_engine_bridge::RobotEngineBridge", 0, 1);

    bool(CARB_ABI* createApplication)(std::string assetPath,
                                      std::string appFile,
                                      std::vector<const char*> modulePaths,
                                      std::vector<const char*> jsonFiles);
    bool(CARB_ABI* destroyApplication)();
    bool(CARB_ABI* tickComponent)(const std::string& primPath);
    std::string const(CARB_ABI* getLastError)();
    void(CARB_ABI* initializeStageLoader)(const std::string& inputComponent,
                                          const std::string& requestChannelName,
                                          const std::string& cameraRequestChannelName,
                                          const std::string& outputComponent,
                                          const std::string& replyChannelName);
    bool(CARB_ABI* executeCommand)(const std::string& command);
    bool(CARB_ABI* publishJsonMessage)(
        std::string node, std::string component, std::string channel, uint64_t typeID, std::string jsonString);
    int64_t const(CARB_ABI* getSimTimeNano)();
    int64_t const(CARB_ABI* getAppOffsetNano)();
    int64_t const(CARB_ABI* getAppHandle)();
    void* const(CARB_ABI* getCApiHandle)();
};

}
}
}
