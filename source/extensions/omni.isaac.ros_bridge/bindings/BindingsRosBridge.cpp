// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/ros_bridge/RosBridge.h>
#include <pybind11/pybind11/numpy.h>

CARB_BINDINGS("omni.isaac.ros_bridge.python")

namespace omni
{
namespace isaac
{
namespace ros_bridge
{
}
}
}

namespace
{

PYBIND11_MODULE(_ros_bridge, m)
{
    using namespace carb;
    using namespace omni::isaac::ros_bridge;

    m.doc() = "Isaac ROS bridge bindings";

    {
        defineInterfaceClass<RosBridge>(m, "RosBridge", "acquire_ros_bridge_interface", "release_ros_bridge_interface")
            .def("use_sim_time", wrapInterfaceFunction(&RosBridge::setUseSimTime),
                 R"pbdoc(
                Specify whether ROS bridge nodes publish their timestamp in sim time

                Args:
                    arg0: (:obj:`bool`): `True` for sim time, `False` for system clock

            )pbdoc")
            .def("use_physics_step_sim_time", wrapInterfaceFunction(&RosBridge::setUsePhysicsStepSimTime),
                 R"pbdoc(
                Specify whether ROS bridge nodes use physics step events to update the sim time

                Args:
                    arg0: (:obj:`bool`): `True` to use physics steps, `False` to use rendering/app update steps

            )pbdoc")
            .def("tick_component", wrapInterfaceFunction(&RosBridge::tickComponent),
                 R"pbdoc(
                Tick all publishers/subscribers on a specific component

                Args:
                    arg0: (:obj:`str`): Path to component

                Returns:

                    `True` if component was found, `False` otherwise.

            )pbdoc")
            .def("ros_master_check", wrapInterfaceFunction(&RosBridge::rosMasterCheck),
                 R"pbdoc(

                Returns:

                    `True` if ros master was found, `False` otherwise.

                )pbdoc");
    }
}
}
