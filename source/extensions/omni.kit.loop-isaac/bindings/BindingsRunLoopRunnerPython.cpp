// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsPythonUtils.h>

#include <pybind11/chrono.h>
#include <pybind11/functional.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <RunLoopRunner.h>

CARB_BINDINGS("omni.kit.loop-isaac.python")

namespace omni
{
namespace kit
{
}
}


namespace
{

namespace py = pybind11;

PYBIND11_MODULE(_loop, m)
{
    using namespace carb;
    using namespace omni::kit;
    // We use carb data types, must import bindings for them
    auto carb_module = py::module::import("carb");

    m.doc() = "Isaac loop bindings";

    defineInterfaceClass<IRunLoopRunnerImpl>(m, "RunLoopRunner", "acquire_loop_interface", "release_loop_interface")

        .def("set_manual_step_size", wrapInterfaceFunction(&IRunLoopRunnerImpl::setManualStepSize),
             R"pbdoc(
                Sets dt for run loop.

                Args: 
                    arg0 (:obj:`double`): The dt value to set to.

                    arg1 (:obj:`str`): The name of the run loop. If name is an empty string, all active run loops are set.

                )pbdoc",
             py::arg("dt") = "0.01667", py::arg("name") = "")
        .def("set_manual_mode", wrapInterfaceFunction(&IRunLoopRunnerImpl::setManualMode),
             R"pbdoc(
                Sets dt for run loop.

                Args: 
                    arg0 (:obj:`bool`): Set to true to enable manual mode.

                    arg1 (:obj:`str`): The name of the run loop. If name is an empty string, all active run loops are set.

                )pbdoc",
             py::arg("enabled") = "True", py::arg("name") = "");
}
}
