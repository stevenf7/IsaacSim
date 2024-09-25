// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

/** @file
 * @brief Interface to access the ROS 2 factory and context handler for the sourced ROS 2 distribution.
 */
#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

#include <string>
#include <vector>

namespace isaacsim
{
namespace ros2
{
namespace bridge
{

class Ros2Factory;

/**
 * ROS 2 bridge interface
 */
struct Ros2Bridge
{
    CARB_PLUGIN_INTERFACE("isaacsim::ros2::bridge::Ros2Bridge", 0, 2);

    /** Get the memory address of a \ref Ros2ContextHandle shared pointer object.
     *
     * The \ref Ros2ContextHandle object encapsulates a `rcl_context_t` (non-global state of an init/shutdown cycle)
     * instance used in the creation of ROS 2 nodes and other entities.
     *
     * @returns Context handler memory address as 64-bit unsigned integer.
     */
    uint64_t const(CARB_ABI* getDefaultContextHandleAddr)();

    /**
     * Get the factory instance for creating ROS 2 related functions/objects according to the sourced ROS 2
     * distribution.
     *
     * See \ref Ros2Factory for more details about the list of ROS 2 related functions/objects that can be created.
     *
     * @returns A pointer to the factory instance.
     */
    Ros2Factory* const(CARB_ABI* getFactory)();

    /** Check if both the factory and the context handler have been instantiated.
     *
     * Both, the factory (\ref Ros2Factory) and the handler (\ref Ros2ContextHandle) objects are created the first time
     * the `Ros2Bridge` interface is acquired after the plugin is loaded by the `isaacsim.ros2.bridge` extension.
     *
     * @returns Whether the factory and the context handler have been successfully instantiated.
     */
    bool const(CARB_ABI* getStartupStatus)();
};

} // namespace bridge
} // namespace ros2
} // namespace isaacsim
