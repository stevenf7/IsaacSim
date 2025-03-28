// SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#include <carb/BindingsPythonUtils.h>
#include <carb/logging/Log.h>

#include <isaacsim/robot/wheeled_robots/IWheeledRobots.h>

CARB_BINDINGS("isaacsim.robot.wheeled_robots.python")

namespace isaacsim
{
namespace robot
{
namespace wheeled_robots
{
} // namespace wheeled_robots
} // namespace robot
} // namespace isaacsim

namespace
{

/**
 * @brief Python bindings for the Wheeled Robots module
 *
 * Provides Python interface access to the wheeled robots functionality
 * through pybind11 bindings.
 */
PYBIND11_MODULE(_isaacsim_robot_wheeled_robots, m)
{
    // clang-format off
    using namespace carb;
    using namespace isaacsim::robot::wheeled_robots;

    m.doc() = R"pbdoc(
        Internal interface that is automatically called when the extension is loaded so that Omnigraph nodes are registered.

        Example:

            # import  isaacsim.robot.wheeled_robots.bindings._isaacsim_robot_wheeled_robots as _isaacsim_robot_wheeled_robots

            # Acquire the interface
            interface = _isaacsim_robot_wheeled_robots.acquire_wheeled_robots_interface()

            # Use the interface
            # ...

            # Release the interface
            _isaacsim_robot_wheeled_robots.release_wheeled_robots_interface(interface)
    )pbdoc";

    defineInterfaceClass<IWheeledRobots>(
        m,
        "IWheeledRobots",
        "acquire_wheeled_robots_interface",
        "release_wheeled_robots_interface"
    );
}
} // namespace anonymous
