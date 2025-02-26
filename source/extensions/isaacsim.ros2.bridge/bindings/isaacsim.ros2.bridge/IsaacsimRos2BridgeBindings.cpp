// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

/** @file
 * @brief Python bindings for the ROS 2 bridge interface
 * @details
 * This file provides Python bindings for the ROS 2 bridge functionality in Isaac Sim.
 * It exposes the core ROS 2 bridge interface to Python, allowing Python scripts to
 * interact with ROS 2 functionality through the bridge.
 */

#include <carb/BindingsPythonUtils.h>

#include <isaacsim/ros2/bridge/Ros2Bridge.h>
#include <pybind11/numpy.h>

CARB_BINDINGS("isaacsim.ros2.bridge.python")

namespace isaacsim
{
namespace ros2
{
namespace bridge
{
} // namespace bridge
} // namespace ros2
} // namespace isaacsim

namespace
{

/**
 * @brief Python module definition for ROS 2 bridge bindings
 * @details
 * Creates and configures the Python module that exposes ROS 2 bridge functionality.
 * The module provides access to the Ros2Bridge interface and its methods for
 * managing ROS 2 communication in Isaac Sim.
 *
 * @param[in,out] m Python module object to configure
 */
PYBIND11_MODULE(_ros2_bridge, m)
{
    using namespace carb;
    using namespace isaacsim::ros2::bridge;

    m.doc() = "Isaac ROS2 bridge bindings";

    {
        defineInterfaceClass<Ros2Bridge>(m, "Ros2Bridge", "acquire_ros2_bridge_interface", "release_ros2_bridge_interface")
            .def("get_startup_status", wrapInterfaceFunction(&Ros2Bridge::getStartupStatus));
    }
}

} // namespace anonymous
