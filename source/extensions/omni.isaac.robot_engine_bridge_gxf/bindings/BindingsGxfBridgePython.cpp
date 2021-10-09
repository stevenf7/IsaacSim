// Copyright (c) 2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/robot_engine_bridge_gxf/GxfBridge.h>
#include <pybind11/pybind11/numpy.h>

CARB_BINDINGS("omni.isaac.robot_engine_bridge_gxf.python")

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge_gxf
{

}
}
}

namespace
{
PYBIND11_MODULE(_robot_engine_bridge_gxf, m)
{
    using namespace carb;
    using namespace omni::isaac::robot_engine_bridge_gxf;

    m.doc() = "Isaac gxf bridge bindings";

    defineInterfaceClass<GxfBridge>(
        m, "GxfBridge", "acquire_robot_engine_bridge_gxf_interface", "release_robot_engine_bridge_gxf_interface")
        .def("create_application", wrapInterfaceFunction(&GxfBridge::createApplication))
        .def("destroy_application", wrapInterfaceFunction(&GxfBridge::destroyApplication))
        .def("tick_component", wrapInterfaceFunction(&GxfBridge::tickComponent))
        .def("execute_command", wrapInterfaceFunction(&GxfBridge::executeCommand));
}
}
