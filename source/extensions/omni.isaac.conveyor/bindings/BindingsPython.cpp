// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
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

CARB_BINDINGS("omni.isaac.conveyor.python")

namespace
{

PYBIND11_MODULE(_omni_isaac_conveyor, m)
{
    // clang-format off
    using namespace carb;

    m.doc() = "pybind11 omni.isaac.conveyor bindings";

    defineInterfaceClass<omni::isaac::conveyor::IOmniIsaacConveyor>(m, "IOmniIsaacConveyor", "acquire_interface", "release_interface");
}
}
