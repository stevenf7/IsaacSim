// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/gxf_bridge/GxfBridge.h>
#include <pybind11/numpy.h>

CARB_BINDINGS("omni.isaac.gxf_bridge.python")

namespace omni
{
namespace isaac
{
namespace gxf_bridge
{

}
}
}

namespace
{
PYBIND11_MODULE(_gxf_bridge, m)
{
    using namespace carb;
    using namespace omni::isaac::gxf_bridge;

    m.doc() = "Isaac gxf bridge bindings";

    defineInterfaceClass<GxfBridge>(m, "GxfBridge", "acquire_gxf_bridge_interface", "release_gxf_bridge_interface")
        .def("create_default_context", wrapInterfaceFunction(&GxfBridge::createDefaultContext))
        .def("destroy_default_context", wrapInterfaceFunction(&GxfBridge::destroyDefaultContext))
        .def("get_default_context_handle", wrapInterfaceFunction(&GxfBridge::getDefaultContextHandle));
}
}
