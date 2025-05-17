// SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.
/*
Carbonite SDK API:
  https://docs.omniverse.nvidia.com/kit/docs/carbonite/latest/api/carbonite_api.html
*/

#pragma once

#define CARB_EXPORTS

#ifdef _MSC_VER
#    if ISAACSIM_CORE_SIMULATION_MANAGER_EXPORT
#        define DLL_EXPORT __declspec(dllexport)
#    else
#        define DLL_EXPORT __declspec(dllimport)
#    endif
#else
#    define DLL_EXPORT
#endif


#include <carb/Defines.h>
#include <carb/Interface.h>

#include <omni/fabric/RationalTime.h>
#include <pch/UsdPCH.h>
#include <pxr/pxr.h>

#include <cstdint>
#include <functional>

namespace isaacsim
{
namespace core
{
namespace simulation_manager
{

struct ISimulationManager
{
    CARB_PLUGIN_INTERFACE("isaacsim::core::simulation_manager::ISimulationManager", 2, 0);

    /**
     * @brief Registers a callback function to be called when a deletion event occurs.
     * @param[in] callback Function to be called with the path of the deleted item.
     * @return Unique identifier for the registered callback.
     */
    DLL_EXPORT virtual int registerDeletionCallback(const std::function<void(std::string)>& callback) = 0;

    /**
     * @brief Registers a callback function to be called when a physics scene is added.
     * @param[in] callback Function to be called with the path of the added physics scene.
     * @return Unique identifier for the registered callback.
     */
    DLL_EXPORT virtual int registerPhysicsSceneAdditionCallback(const std::function<void(std::string)>& callback) = 0;

    /**
     * @brief Deregisters a previously registered callback.
     * @param[in] callbackId The unique identifier of the callback to deregister.
     * @return True if callback was successfully deregistered, false otherwise.
     */
    DLL_EXPORT virtual bool deregisterCallback(const int& callbackId) = 0;

    /**
     * @brief Resets the simulation manager to its initial state.
     */
    DLL_EXPORT virtual void reset() = 0;

    /**
     * @brief Gets the current callback iteration counter.
     * @return Reference to the current callback iteration counter.
     */
    DLL_EXPORT virtual int& getCallbackIter() = 0;

    /**
     * @brief Sets the callback iteration counter.
     * @param[in] val New value for the callback iteration counter.
     */
    DLL_EXPORT virtual void setCallbackIter(int const& val) = 0;

    /**
     * @brief Enables or disables the USD notice handler.
     * @param[in] flag True to enable the handler, false to disable.
     */
    DLL_EXPORT virtual void enableUsdNoticeHandler(bool const& flag) = 0;

    /**
     * @brief Enables or disables the USD notice handler for a specific fabric stage.
     * @param[in] stageId ID of the fabric stage.
     * @param[in] flag True to enable the handler, false to disable.
     */
    DLL_EXPORT virtual void enableFabricUsdNoticeHandler(long stageId, bool const& flag) = 0;

    /**
     * @brief Checks if the USD notice handler is enabled for a specific fabric stage.
     * @param[in] stageId ID of the fabric stage to check.
     * @return True if the handler is enabled for the stage, false otherwise.
     */
    DLL_EXPORT virtual bool isFabricUsdNoticeHandlerEnabled(long stageId) = 0;

    /**
     * @brief Gets the current simulation time.
     * @return The current simulation time.
     */
    DLL_EXPORT virtual double getSimulationTime() = 0;

    /**
     * @brief Gets the current simulation time which does not reset when the simulation is stopped.
     * @return The current simulation time.
     */
    DLL_EXPORT virtual double getSimulationTimeMonotonic() = 0;

    /**
     * @brief Gets the current system time.
     * @return The current system time.
     */
    DLL_EXPORT virtual double getSystemTime() = 0;

    /**
     * @brief Gets the current physics step count.
     * @return The current physics step count.
     */
    DLL_EXPORT virtual size_t getNumPhysicsSteps() = 0;

    /**
     * @brief Gets the current simulation time.
     * @return The current simulation time.
     */
    DLL_EXPORT virtual bool isSimulating() = 0;

    /**
     * @brief Gets the current simulation pause state.
     * @return The current simulation pause state.
     */
    DLL_EXPORT virtual bool isPaused() = 0;

    /**
     * @brief Gets simulation time at a specific rational time.
     * @details Returns the simulation time corresponding to a specific rational time.
     *
     * @param[in] time Rational time to query simulation time for.
     * @return Simulation time in seconds at the specified time.
     */
    DLL_EXPORT virtual double getSimulationTimeAtTime(const omni::fabric::RationalTime& rtime) = 0;

    /**
     * @brief Gets monotonic simulation time at a specific rational time.
     * @details Returns the monotonically increasing simulation time corresponding to a specific rational time.
     *
     * @param[in] time Rational time to query monotonic simulation time for.
     * @return Monotonic simulation time in seconds at the specified time.
     */
    DLL_EXPORT virtual double getSimulationTimeMonotonicAtTime(const omni::fabric::RationalTime& rtime) = 0;

    /**
     * @brief Gets system time at a specific rational time.
     * @details Returns the system (real-world) time corresponding to a specific rational time.
     *
     * @param[in] time Rational time to query system time for.
     * @return System time in seconds at the specified time.
     */
    DLL_EXPORT virtual double getSystemTimeAtTime(const omni::fabric::RationalTime& rtime) = 0;
};

} // namespace isaacsim
} // namespace core
} // namespace simulation_manager
