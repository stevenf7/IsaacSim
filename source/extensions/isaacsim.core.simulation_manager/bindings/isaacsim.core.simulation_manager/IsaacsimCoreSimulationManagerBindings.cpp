// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <carb/BindingsPythonUtils.h>

#include <isaacsim/core/simulation_manager/SimulationManager.h>
#include <pybind11/functional.h>


CARB_BINDINGS("isaacsim.core.simulation_manager.python")

namespace
{

PYBIND11_MODULE(_simulation_manager, m)
{
    using namespace isaacsim::core::simulation_manager;

    m.doc() = "pybind11 isaacsim.core.simulation_manager.pybind bindings";

    // carb interface
    carb::defineInterfaceClass<ISimulationManager>(
        m, "ISimulationManager", "acquire_simulation_manager_interface", "release_simulation_manager_interface")
        .def("register_deletion_callback", &ISimulationManager::registerDeletionCallback)
        .def("register_physics_scene_addition_callback", &ISimulationManager::registerPhysicsSceneAdditionCallback)
        .def("deregister_callback", &ISimulationManager::deregisterCallback)
        .def("reset", &ISimulationManager::reset)
        .def("set_callback_iter", &ISimulationManager::setCallbackIter)
        .def("get_callback_iter", &ISimulationManager::getCallbackIter)
        .def("enable_usd_notice_handler", &ISimulationManager::enableUsdNoticeHandler)
        .def("enable_fabric_usd_notice_handler", &ISimulationManager::enableFabricUsdNoticeHandler)
        .def("is_fabric_usd_notice_handler_enabled", &ISimulationManager::isFabricUsdNoticeHandlerEnabled);
}

}
