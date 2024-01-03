// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
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


namespace omni
{
namespace kit
{

struct IRunLoopRunnerImpl
{
    CARB_PLUGIN_INTERFACE("omni::kit::IRunLoopRunnerImpl", 1, 0);

    void(CARB_ABI* setManualStepSize)(double dt, std::string name);
    void(CARB_ABI* setManualMode)(bool enabled, std::string name);
};
}
}
