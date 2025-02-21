// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

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

    m.doc() = "pybind11 isaacsim.robot.wheeled_robots bindings";

    defineInterfaceClass<IWheeledRobots>(
        m,
        "IWheeledRobots",
        "acquire_wheeled_robots_interface",
        "release_wheeled_robots_interface"
    );
}
} // namespace anonymous
