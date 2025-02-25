// Copyright (c) 2024-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
/*
Carbonite SDK API:
  https://docs.omniverse.nvidia.com/kit/docs/carbonite/latest/api/carbonite_api.html
*/

#pragma once

#define CARB_EXPORTS

#ifdef _MSC_VER
#    if OMPRIMUTILSEXPORT
#        define DllExport __declspec(dllexport)
#    else
#        define DllExport __declspec(dllimport)
#    endif
#else
#    define DllExport
#endif


#include <carb/Defines.h>
#include <carb/Interface.h>

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

/**
 * Carbonite interface
 */
struct ISimulationManager
{
    CARB_PLUGIN_INTERFACE("isaacsim::core::simulation_manager::ISimulationManager", 1, 0);

    // ------------------
    // custom API declaration. E.g.:
    /**
     * @brief Registers a callback function to be called when a deletion event occurs.
     * @param[in] callback Function to be called with the path of the deleted item.
     * @return Unique identifier for the registered callback.
     */
    DllExport virtual int registerDeletionCallback(const std::function<void(std::string)>& callback) = 0;

    /**
     * @brief Registers a callback function to be called when a physics scene is added.
     * @param[in] callback Function to be called with the path of the added physics scene.
     * @return Unique identifier for the registered callback.
     */
    DllExport virtual int registerPhysicsSceneAdditionCallback(const std::function<void(std::string)>& callback) = 0;

    /**
     * @brief Deregisters a previously registered callback.
     * @param[in] callbackId The unique identifier of the callback to deregister.
     * @return True if callback was successfully deregistered, false otherwise.
     */
    DllExport virtual bool deregisterCallback(const int& callbackId) = 0;

    /**
     * @brief Resets the simulation manager to its initial state.
     */
    DllExport virtual void reset() = 0;

    /**
     * @brief Gets the current callback iteration counter.
     * @return Reference to the current callback iteration counter.
     */
    DllExport virtual int& getCallbackIter() = 0;

    /**
     * @brief Sets the callback iteration counter.
     * @param[in] val New value for the callback iteration counter.
     */
    DllExport virtual void setCallbackIter(int const& val) = 0;

    /**
     * @brief Enables or disables the USD notice handler.
     * @param[in] flag True to enable the handler, false to disable.
     */
    DllExport virtual void enableUsdNoticeHandler(bool const& flag) = 0;

    /**
     * @brief Enables or disables the USD notice handler for a specific fabric stage.
     * @param[in] stageId ID of the fabric stage.
     * @param[in] flag True to enable the handler, false to disable.
     */
    DllExport virtual void enableFabricUsdNoticeHandler(long stageId, bool const& flag) = 0;

    /**
     * @brief Checks if the USD notice handler is enabled for a specific fabric stage.
     * @param[in] stageId ID of the fabric stage to check.
     * @return True if the handler is enabled for the stage, false otherwise.
     */
    DllExport virtual bool isFabricUsdNoticeHandlerEnabled(long stageId) = 0;
    // ------------------
};

} // namespace isaacsim
} // namespace core
} // namespace simulation_manager
