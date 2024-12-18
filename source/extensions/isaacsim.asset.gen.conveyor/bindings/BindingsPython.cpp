// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#include "IOmniIsaacConveyor.h"

#include <carb/BindingsPythonUtils.h>
#include <carb/logging/Log.h>

CARB_BINDINGS("isaacsim.asset.gen.conveyor.python")

namespace
{

PYBIND11_MODULE(_isaacsim_asset_gen_conveyor, m)
{
    // clang-format off
    using namespace carb;

    m.doc() = "pybind11 isaacsim.asset.gen.conveyor bindings";

    defineInterfaceClass<omni::isaac::conveyor::IOmniIsaacConveyor>(m, "IOmniIsaacConveyor", "acquire_interface", "release_interface");
}
}
