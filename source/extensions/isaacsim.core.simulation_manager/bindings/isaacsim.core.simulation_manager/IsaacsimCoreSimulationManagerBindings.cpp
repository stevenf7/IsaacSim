// SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.
#include <pch/UsdPCH.h>
// clang-format on

#include <carb/BindingsPythonUtils.h>

#include <isaacsim/core/simulation_manager/ISimulationManager.h>
#include <pybind11/functional.h>


CARB_BINDINGS("isaacsim.core.simulation_manager.python")

namespace
{

PYBIND11_MODULE(_simulation_manager, m)
{
    using namespace isaacsim::core::simulation_manager;

    m.doc() = R"(Omniverse Isaac Sim Simulation Manager Interface

This module provides access to the Simulation Manager which handles events and callbacks
for simulation-related activities, such as physics scene additions and object deletions.
It also manages USD notice handling to track stage changes.)";

    // carb interface
    carb::defineInterfaceClass<ISimulationManager>(
        m, "ISimulationManager", "acquire_simulation_manager_interface", "release_simulation_manager_interface")
        .def("register_deletion_callback", &ISimulationManager::registerDeletionCallback,
             R"(Register a callback for deletion events.

Args:
    callback: Function to be called when an object is deleted. Takes a string path parameter.

Returns:
    int: Unique identifier for the registered callback.)")
        .def("register_physics_scene_addition_callback", &ISimulationManager::registerPhysicsSceneAdditionCallback,
             R"(Register a callback for physics scene addition events.

Args:
    callback: Function to be called when a physics scene is added. Takes a string path parameter.

Returns:
    int: Unique identifier for the registered callback.)")
        .def("deregister_callback", &ISimulationManager::deregisterCallback,
             R"(Deregister a previously registered callback.

Args:
    callback_id: The unique identifier of the callback to deregister.

Returns:
    bool: True if callback was successfully deregistered, False otherwise.)")
        .def("reset", &ISimulationManager::reset,
             R"(Reset the simulation manager to its initial state.

Calls all registered deletion callbacks with the root path ('/'),
clears all registered callbacks, clears the physics scenes list,
and resets the callback iterator to 0.)")
        .def("set_callback_iter", &ISimulationManager::setCallbackIter,
             R"(Set the callback iteration counter.

Args:
    val: New value for the callback iteration counter.)")
        .def("get_callback_iter", &ISimulationManager::getCallbackIter,
             R"(Get the current callback iteration counter.

Returns:
    int: The current callback iteration counter value.)")
        .def("enable_usd_notice_handler", &ISimulationManager::enableUsdNoticeHandler,
             R"(Enable or disable the USD notice handler.

Args:
    flag: True to enable the handler, False to disable.)")
        .def("enable_fabric_usd_notice_handler", &ISimulationManager::enableFabricUsdNoticeHandler,
             R"(Enable or disable the USD notice handler for a specific fabric stage.

Args:
    stage_id: ID of the fabric stage.
    flag: True to enable the handler, False to disable.)")
        .def("is_fabric_usd_notice_handler_enabled", &ISimulationManager::isFabricUsdNoticeHandlerEnabled,
             R"(Check if the USD notice handler is enabled for a specific fabric stage.

Args:
    stage_id: ID of the fabric stage to check.

Returns:
    bool: True if the handler is enabled for the stage, False otherwise.)");
}

}
