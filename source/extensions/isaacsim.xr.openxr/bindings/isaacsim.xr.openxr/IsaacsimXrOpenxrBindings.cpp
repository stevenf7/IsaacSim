// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsPythonUtils.h>

#include <isaacsim/xr/openxr/OpenXR.h>


CARB_BINDINGS("isaacsim.xr.openxr.python")

namespace
{

PYBIND11_MODULE(_openxr, m)
{
    using namespace isaacsim::xr::openxr;

    m.doc() = "pybind11 isaacsim.xr.openxr.pybind bindings";

    // C++ API
    m.def("set_default_status", &setDefaultStatus);

    // carb interface
    carb::defineInterfaceClass<IOpenxr>(m, "IOpenxr", "acquire_openxr_interface", "release_openxr_interface")
        .def("register_object", &IOpenxr::registerObject);
}

}
