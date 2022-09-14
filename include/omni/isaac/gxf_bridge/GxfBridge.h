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
namespace gxf_bridge
{

struct GxfBridge
{
    CARB_PLUGIN_INTERFACE("omni::isaac::gxf_bridge::GxfBridge", 0, 1);
    bool(CARB_ABI* createDefaultContext)(const std::string& basePath,
                                         const std::string& manifestFile,
                                         const std::vector<std::string>& graphFiles);
    bool(CARB_ABI* destroyDefaultContext)();
    uint64_t const(CARB_ABI* getDefaultContextHandle)();
};
}
}
}
