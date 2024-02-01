// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsPythonUtils.h>
#include <carb/logging/Log.h>

#include <IOmniIsaacWheeledRobots.h>


CARB_BINDINGS("omni.isaac.wheeled_robots.python")

namespace
{

PYBIND11_MODULE(_omni_isaac_wheeled_robots, m)
{
    // clang-format off
    using namespace carb;

    m.doc() = "pybind11 omni.isaac.wheeled_robots bindings";

    defineInterfaceClass<omni::isaac::wheeled_robots::IOmniIsaacWheeledRobots>(m, "IOmniIsaacWheeledRobots", "acquire_interface", "release_interface");
}
}
