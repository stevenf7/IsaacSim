// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsUtils.h>

#include <omni/isaac/motion_planning/MotionPlanning.h>
#include <pybind11/pybind11/pybind11.h>

CARB_BINDINGS("omni.isaac.motion_planning.python")

namespace
{

namespace py = pybind11;

template <typename InterfaceType>
py::class_<InterfaceType> defineInterfaceClass(py::module& m,
                                               const char* className,
                                               const char* acquireFuncName,
                                               const char* releaseFuncName = nullptr)
{
    m.def(
        acquireFuncName,
        [](const char* pluginName, const char* libraryPath) {
            return libraryPath ? acquireInterfaceFromLibraryForBindings<InterfaceType>(libraryPath) :
                                 acquireInterfaceForBindings<InterfaceType>(pluginName);
        },
        py::arg("plugin_name") = nullptr, py::arg("library_path") = nullptr, py::return_value_policy::reference);

    if (releaseFuncName)
    {
        m.def(releaseFuncName, [](InterfaceType* iface) { carb::getFramework()->releaseInterface(iface); });
    }

    return py::class_<InterfaceType>(m, className);
}


PYBIND11_MODULE(_motion_planning, m)
{
    using namespace carb;
    using namespace omni::isaac::motion_planning;

    m.doc() = "Isaac motion planning bindings";

    py::class_<Approach>(m, "Approach")
        .def(py::init<const carb::Float3&, double, double>())
        .def_readwrite("direction", &Approach::direction)
        .def_readwrite("standoff", &Approach::standoff)
        .def_readwrite("std_dev", &Approach::std_dev);

    py::class_<Command>(m, "Command")
        .def(py::init<const carb::Float3&>())
        .def(py::init<const carb::Float3&, const Approach&>())
        .def_readwrite("target", &Command::target)
        .def_readwrite("approach", &Command::approach)
        .def_readwrite("user_weight", &Command::user_weight);

    py::class_<PartialPoseCommand>(m, "PartialPoseCommand")
        .def(py::init<>())
        .def_readwrite("commands", &PartialPoseCommand::commands)
        .def("set",
             [](PartialPoseCommand& self, const Command& command, int index) {
                 if (index < FrameElement::NUM_FRAME_ELEMENTS)
                 {
                     self.commands[index] = command;
                 }
             })
        .def("reset", [](PartialPoseCommand& self, const Command& command, int index) {
            if (index < FrameElement::NUM_FRAME_ELEMENTS)
            {
                self.commands[index].reset();
            }
        });

    py::enum_<FrameElement>(m, "FrameElement", py::arithmetic(), "Types of joint")
        .value("ORIG", FrameElement::ORIG)
        .value("AXIS_X", FrameElement::AXIS_X)
        .value("AXIS_Y", FrameElement::AXIS_Y)
        .value("AXIS_Z", FrameElement::AXIS_Z)
        .value("NUM_FRAME_ELEMENTS", FrameElement::NUM_FRAME_ELEMENTS)
        .export_values();

    defineInterfaceClass<MotionPlanning>(
        m, "MotionPlanning", "acquire_motion_planning_interface", "release_motion_planning_interface")

        .def("registerRmp", wrapInterfaceFunction(&MotionPlanning::registerRmp))
        .def("unregisterRmp", wrapInterfaceFunction(&MotionPlanning::unregisterRmp))
        .def("setFrequency", wrapInterfaceFunction(&MotionPlanning::setFrequency))
        .def("setTargetGlobal", wrapInterfaceFunction(&MotionPlanning::setTargetGlobal))
        .def("setTargetLocal", wrapInterfaceFunction(&MotionPlanning::setTargetLocal))
        .def("goLocal", wrapInterfaceFunction(&MotionPlanning::goLocal))
        .def("getError", wrapInterfaceFunction(&MotionPlanning::getError))
        .def("getRMPState", wrapInterfaceFunction(&MotionPlanning::getRMPState))
        .def("getRMPTarget", wrapInterfaceFunction(&MotionPlanning::getRMPTarget))
        .def("addObstacle", wrapInterfaceFunction(&MotionPlanning::addObstacle))
        .def("updateObstacle", wrapInterfaceFunction(&MotionPlanning::updateObstacle))
        .def("removeObstacle", wrapInterfaceFunction(&MotionPlanning::removeObstacle))
        .def("enableObstacle", wrapInterfaceFunction(&MotionPlanning::enableObstacle))
        .def("disableObstacle", wrapInterfaceFunction(&MotionPlanning::disableObstacle))
        .def("updateGetRelativePoses", wrapInterfaceFunction(&MotionPlanning::updateGetRelativePoses))
        .def("setDefaultConfig", wrapInterfaceFunction(&MotionPlanning::setDefaultConfig));
}
}
