// Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/robot_engine_bridge/RobotEngineBridge.h>
#include <pybind11/pybind11/numpy.h>

CARB_BINDINGS("omni.isaac.robot_engine_bridge.python")

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

}
}
}

namespace
{
PYBIND11_MODULE(_robot_engine_bridge, m)
{
    using namespace carb;
    using namespace omni::isaac::robot_engine_bridge;

    m.doc() = "Isaac robot engine bridge bindings";

    defineInterfaceClass<RobotEngineBridge>(
        m, "RobotEngineBridge", "acquire_robot_engine_bridge_interface", "release_robot_engine_bridge_interface")

        .def("createApplication", wrapInterfaceFunction(&RobotEngineBridge::createApplication))
        .def("destroyApplication", wrapInterfaceFunction(&RobotEngineBridge::destroyApplication))
        .def("getLastError", wrapInterfaceFunction(&RobotEngineBridge::getLastError))
        .def("initializeStageLoader", wrapInterfaceFunction(&RobotEngineBridge::initializeStageLoader));
}
}
