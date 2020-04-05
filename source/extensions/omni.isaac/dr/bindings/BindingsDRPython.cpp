// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "omni/isaac/dr/DomainRandomizer.h"

#include <carb/BindingsPythonUtils.h>

#include <memory>
#include <string>
#include <vector>

CARB_BINDINGS("omni.isaac.dr.python")

namespace omni
{
namespace isaac
{
namespace dr
{

}
}
}

namespace
{

PYBIND11_MODULE(_dr, m)
{
    using namespace carb;
    using namespace omni::isaac::dr;

    m.doc() = "pybind11 omni.isaac.dr bindings";

    defineInterfaceClass<DomainRandomizer>(m, "DomainRandomizer", "acquire_dr_interface", "release_dr_interface")
        .def("load_component_from_usd", wrapInterfaceFunction(&DomainRandomizer::loadComponentFromUsd), R"pbdoc(
                 Loads DR components from USD file.
             )pbdoc");
}
}
