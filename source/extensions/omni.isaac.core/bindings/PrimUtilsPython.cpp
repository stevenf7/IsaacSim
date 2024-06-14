// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on
#include <carb/BindingsPythonUtils.h>

#include <PrimUtils.h>


CARB_BINDINGS("omni.isaac.core.python")

namespace
{

namespace py = pybind11;


PYBIND11_MODULE(_core, m)
{
    using namespace carb;
    using namespace omni::isaac::core;
    // We use carb data types, must import bindings for them
    auto carb_module = py::module::import("carb");

    m.def("_find_matching_prim_paths", &findMatchingPrimPaths);
}
}
