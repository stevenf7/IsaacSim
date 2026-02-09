// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#pragma once

#include <carb/Defines.h>
#include <carb/Interface.h>

#include <cstdint>

namespace isaacsim::kit::xr::teleop::bridge
{

/**
 * @struct ITeleopBridge
 * @brief Interface for accessing OpenXR handles from Kit's XR system.
 *
 * @details This interface provides access to OpenXR handles (instance, session,
 *          stage space, and xrGetInstanceProcAddr) that are managed by Kit's
 *          OpenXR extension. These handles can be used to integrate with
 *          external OpenXR libraries like IsaacTeleop's DeviceIO.
 *
 * The handles are only valid when an XR session is active. Functions return 0
 * when no session is available.
 */
struct ITeleopBridge
{
    CARB_PLUGIN_INTERFACE("isaacsim::kit::xr::teleop::bridge::ITeleopBridge", 1, 0);

    /**
     * @brief Get the current OpenXR instance handle (XrInstance).
     *
     * @return The XrInstance handle as uint64, or 0 if no active session.
     */
    virtual uint64_t getInstanceHandle() noexcept = 0;

    /**
     * @brief Get the current OpenXR session handle (XrSession).
     *
     * @return The XrSession handle as uint64, or 0 if no active session.
     */
    virtual uint64_t getSessionHandle() noexcept = 0;

    /**
     * @brief Get the OpenXR stage reference space handle (XrSpace).
     *
     * @details The stage space is created when the XR session starts, using
     * XR_REFERENCE_SPACE_TYPE_STAGE (or LOCAL as fallback).
     *
     * @return The XrSpace handle as uint64, or 0 if no active session.
     */
    virtual uint64_t getStageSpaceHandle() noexcept = 0;

    /**
     * @brief Get the xrGetInstanceProcAddr function pointer.
     *
     * @details This is the same function pointer passed to the component's initialize()
     * callback, ensuring it uses the same OpenXR dispatch chain as Kit.
     *
     * @return The function pointer as uint64, or 0 if not available.
     */
    virtual uint64_t getInstanceProcAddr() noexcept = 0;
};

} // namespace isaacsim::kit::xr::teleop::bridge
