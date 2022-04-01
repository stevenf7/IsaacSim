// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#include <carb/BindingsPythonUtils.h>
#include <carb/logging/Log.h>

#include <omni/isaac/core_nodes/CoreNodes.h>

CARB_BINDINGS("omni.isaac.core_nodes.python")


namespace
{

PYBIND11_MODULE(_omni_isaac_core_nodes, m)
{
    // clang-format off
    using namespace carb;

    m.doc() = "pybind11 omni.isaac.core_nodes bindings";

    defineInterfaceClass< omni::isaac::core_nodes::CoreNodes>(m, "CoreNodes", "acquire_interface", "release_interface");
}
}
