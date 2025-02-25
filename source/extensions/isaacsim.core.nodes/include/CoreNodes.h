// Copyright (c) 2021-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <carb/Interface.h>
#include <carb/logging/Log.h>

#include <omni/fabric/RationalTime.h>

namespace isaacsim
{

namespace core
{
namespace nodes
{

/**
 * Minimal interface.
 *
 * It doesn't have any functions, but just implementing it and acquiring will load your plugin, trigger call of
 * carbOnPluginStartup() and carbOnPluginShutdown() methods and allow you to use other Carbonite plugins. That by itself
 * can get you quite far and useful as basic building block for Kit extensions. One can define their own interface with
 * own python python bindings when needed and abandon that one.
 */
struct CoreNodes
{
    CARB_PLUGIN_INTERFACE("isaacsim::core::nodes", 1, 1);

    /**
     * @brief Gets the current simulation time.
     * @return Current simulation time in seconds.
     */
    double(CARB_ABI* getSimTime)();

    /**
     * @brief Gets the monotonic simulation time.
     * @return Monotonically increasing simulation time in seconds.
     */
    double(CARB_ABI* getSimTimeMonotonic)();

    /**
     * @brief Gets the current system time.
     * @return Current system time in seconds.
     */
    double(CARB_ABI* getSystemTime)();

    /**
     * @brief Gets the number of physics steps executed.
     * @return Number of physics steps completed since simulation start.
     */
    size_t(CARB_ABI* getPhysicsNumSteps)();

    // TODO: deprecated : use getSimTimeAtTime instead
    /**
     * @brief Gets simulation time at a specific software frame.
     * @deprecated Use getSimTimeAtTime instead.
     * @param[in] swhFrame Frame number to query time for.
     * @return Simulation time in seconds at the specified frame.
     */
    double(CARB_ABI* getSimTimeAtSwhFrame)(const int64_t swhFrame);

    // TODO: deprecated : use getSimTimeMonotonicAtTime instead
    /**
     * @brief Gets monotonic simulation time at a specific software frame.
     * @deprecated Use getSimTimeMonotonicAtTime instead.
     * @param[in] swhFrame Frame number to query time for.
     * @return Monotonic simulation time in seconds at the specified frame.
     */
    double(CARB_ABI* getSimTimeMonotonicAtSwhFrame)(const int64_t swhFrame);

    // TODO: deprecated : use getSystemTimeAtTime instead
    /**
     * @brief Gets system time at a specific software frame.
     * @deprecated Use getSystemTimeAtTime instead.
     * @param[in] swhFrame Frame number to query time for.
     * @return System time in seconds at the specified frame.
     */
    double(CARB_ABI* getSystemTimeAtSwhFrame)(const int64_t swhFrame);

    /**
     * @brief Adds a handle to the handle registry.
     * @param[in] handle Pointer to the handle to add.
     * @return Unique identifier for the added handle.
     */
    uint64_t(CARB_ABI* addHandle)(void* handle);

    /**
     * @brief Retrieves a handle from the handle registry.
     * @param[in] handleId Unique identifier of the handle to retrieve.
     * @return Pointer to the handle if found, nullptr otherwise.
     */
    void*(CARB_ABI* getHandle)(const uint64_t handleId);

    /**
     * @brief Removes a handle from the handle registry.
     * @param[in] handleId Unique identifier of the handle to remove.
     * @return True if handle was successfully removed, false otherwise.
     */
    bool(CARB_ABI* removeHandle)(const uint64_t handleId);

    /**
     * @brief Gets simulation time at a specific rational time.
     * @param[in] time Rational time to query simulation time for.
     * @return Simulation time in seconds at the specified time.
     */
    double(CARB_ABI* getSimTimeAtTime)(const omni::fabric::RationalTime& time);

    /**
     * @brief Gets monotonic simulation time at a specific rational time.
     * @param[in] time Rational time to query monotonic simulation time for.
     * @return Monotonic simulation time in seconds at the specified time.
     */
    double(CARB_ABI* getSimTimeMonotonicAtTime)(const omni::fabric::RationalTime& time);

    /**
     * @brief Gets system time at a specific rational time.
     * @param[in] time Rational time to query system time for.
     * @return System time in seconds at the specified time.
     */
    double(CARB_ABI* getSystemTimeAtTime)(const omni::fabric::RationalTime& time);
};
} // action
} // graph
} // omni
