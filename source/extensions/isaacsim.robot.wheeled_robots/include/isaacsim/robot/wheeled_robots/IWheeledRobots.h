// Copyright (c) 2024-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <carb/Interface.h>

namespace isaacsim
{
namespace robot
{
namespace wheeled_robots
{

/**
 * @brief Interface for wheeled robot control functionality.
 *
 * This interface provides the foundation for wheeled robot control in Isaac Sim.
 * While it contains no direct functions, implementing this interface:
 * - Enables plugin loading and initialization
 * - Triggers carbOnPluginStartup() and carbOnPluginShutdown() lifecycle methods
 * - Provides access to the Carbonite plugin ecosystem
 *
 * Extensions can build upon this interface by defining custom functionality
 * and Python bindings as needed.
 */
struct IWheeledRobots
{
    CARB_PLUGIN_INTERFACE("isaacsim::robot::wheeled_robots", 1, 0);
};

} // namespace wheeled_robots
} // namespace robot
} // namespace isaacsim
