// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#include <carb/BindingsPythonUtils.h>

#include <isaacsim/kit/xr/teleop/bridge/ITeleopBridge.h>
#include <pybind11/functional.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

CARB_BINDINGS("isaacsim.kit.xr.teleop.bridge.python")

namespace
{

PYBIND11_MODULE(_bridge, m)
{
    using namespace isaacsim::kit::xr::teleop::bridge;

    m.doc() = "Isaac Kit XR Teleop Bridge - provides OpenXR handle functions for Kit";

    pybind11::class_<ITeleopBridge::RequiredExtensionsSubscription>(m, "RequiredExtensionsSubscription")
        .def("reset", &ITeleopBridge::RequiredExtensionsSubscription::reset,
             R"doc(
            Explicitly release this required-extension subscription.
            )doc")
        .def("__bool__",
             [](const ITeleopBridge::RequiredExtensionsSubscription& self) { return static_cast<bool>(self); });

    // Define the Carbonite interface class with acquire/release functions
    // This properly integrates with Carbonite's plugin system and triggers
    // carbOnPluginStartup() when the interface is first acquired
    carb::defineInterfaceClass<ITeleopBridge>(
        m, "ITeleopBridge", "acquire_teleop_bridge_interface", "release_teleop_bridge_interface")
        .def("get_instance_handle", &ITeleopBridge::getInstanceHandle,
             R"doc(
            Get the current OpenXR instance handle (XrInstance).

            The instance is obtained from the registered OpenXR component, which receives
            it via lifecycle callbacks from Kit's OpenXR extension.

            Returns:
                int: The XrInstance handle, or 0 if no active OpenXR session.
            )doc")
        .def("get_session_handle", &ITeleopBridge::getSessionHandle,
             R"doc(
            Get the current OpenXR session handle (XrSession).

            The session is obtained from the registered OpenXR component, which receives
            it via the onSessionStart callback from Kit's OpenXR extension.

            Returns:
                int: The XrSession handle, or 0 if no active OpenXR session.
            )doc")
        .def("get_stage_space_handle", &ITeleopBridge::getStageSpaceHandle,
             R"doc(
            Get the OpenXR stage reference space handle (XrSpace).

            The stage space is created automatically when the XR session starts via the
            OpenXR component's onSessionStart callback. It uses XR_REFERENCE_SPACE_TYPE_STAGE
            (or falls back to LOCAL if STAGE is not supported).

            Returns:
                int: The XrSpace handle for the stage space, or 0 if no active session.
            )doc")
        .def("get_instance_proc_addr", &ITeleopBridge::getInstanceProcAddr,
             R"doc(
            Get the xrGetInstanceProcAddr function pointer from the OpenXR loader.

            This is the same function pointer that was passed to the component's initialize()
            callback, ensuring it uses the same OpenXR dispatch chain as Kit.

            Returns:
                int: The xrGetInstanceProcAddr function pointer as uint64, or 0 if not available.
            )doc")
        .def("subscribe_required_extensions", &ITeleopBridge::subscribeRequiredExtensions,
             R"doc(
            Subscribe a callback to contribute additional OpenXR required extensions.

            The callback must return a list of extension names to append to the
            resolved required extension list. Duplicate values are ignored.

            Args:
                callback: Callable with signature ``() -> list[str]``.

            Returns:
                RequiredExtensionsSubscription: Keep this handle alive to keep the callback subscribed.
            )doc");
}

}
