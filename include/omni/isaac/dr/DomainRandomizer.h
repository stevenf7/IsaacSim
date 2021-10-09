// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
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

#include <map>
#include <string>
#include <vector>

namespace omni
{
namespace isaac
{
namespace dr
{

struct DomainRandomizer
{
    CARB_PLUGIN_INTERFACE("omni::isaac::dr::DomainRandomizer", 0, 1);

    void(CARB_ABI* randomizeOnce)();
    void(CARB_ABI* toggleManualMode)();
    std::string(CARB_ABI* getDRLayerName)();
};
}
}
}
