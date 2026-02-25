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
#include <functional>
#include <memory>
#include <string>
#include <utility>
#include <vector>

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
    CARB_PLUGIN_INTERFACE("isaacsim::kit::xr::teleop::bridge::ITeleopBridge", 1, 3);

    /** @brief Callback invoked to contribute extra required OpenXR extensions. */
    using RequiredExtensionsCallback = std::function<std::vector<std::string>()>;

    /**
     * @brief Internal registry-state interface used by subscription handles.
     */
    class RequiredExtensionsRegistryState
    {
    public:
        virtual ~RequiredExtensionsRegistryState() = default;
        virtual void unsubscribe(uint64_t subscriptionId) noexcept = 0;
    };

    /**
     * @brief RAII subscription handle for required-extension callbacks.
     *
     * @details Destroying this handle automatically unsubscribes the callback.
     */
    class RequiredExtensionsSubscription
    {
    public:
        RequiredExtensionsSubscription() = default;

        RequiredExtensionsSubscription(const RequiredExtensionsSubscription&) = delete;
        RequiredExtensionsSubscription& operator=(const RequiredExtensionsSubscription&) = delete;

        RequiredExtensionsSubscription(RequiredExtensionsSubscription&& other) noexcept
            : m_registryState(std::move(other.m_registryState)), m_subscriptionId(other.m_subscriptionId)
        {
            other.m_subscriptionId = 0;
        }

        RequiredExtensionsSubscription& operator=(RequiredExtensionsSubscription&& other) noexcept
        {
            if (this != &other)
            {
                reset();
                m_registryState = std::move(other.m_registryState);
                m_subscriptionId = other.m_subscriptionId;
                other.m_subscriptionId = 0;
            }
            return *this;
        }

        ~RequiredExtensionsSubscription()
        {
            reset();
        }

        /**
         * @brief Explicitly release this subscription.
         */
        void reset() noexcept
        {
            if (m_subscriptionId != 0)
            {
                if (auto registryState = m_registryState.lock())
                {
                    registryState->unsubscribe(m_subscriptionId);
                }
            }
            m_registryState.reset();
            m_subscriptionId = 0;
        }

        /**
         * @brief Check whether this subscription currently owns a valid registration.
         */
        explicit operator bool() const noexcept
        {
            return m_subscriptionId != 0;
        }

    private:
        RequiredExtensionsSubscription(std::weak_ptr<RequiredExtensionsRegistryState> registryState,
                                       uint64_t subscriptionId) noexcept
            : m_registryState(std::move(registryState)), m_subscriptionId(subscriptionId)
        {
        }

        std::weak_ptr<RequiredExtensionsRegistryState> m_registryState;
        uint64_t m_subscriptionId = 0;

        friend struct ITeleopBridge;
    };

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

    /**
     * @brief Subscribe a callback that can contribute additional required OpenXR extensions.
     *
     * @details Subscribed callbacks are invoked when the OpenXR component resolves
     * required extensions during startup. Callback return values are deduplicated
     * before being appended to the final required extension list.
     *
     * @param[in] callback Callable that returns extension names to append.
     *
     * @return RAII subscription handle. Keep it alive while subscription is active.
     */
    virtual RequiredExtensionsSubscription subscribeRequiredExtensions(
        const RequiredExtensionsCallback& callback) noexcept = 0;

protected:
    /**
     * @brief Helper for implementations to create a subscription handle safely.
     */
    static RequiredExtensionsSubscription makeRequiredExtensionsSubscription(
        std::weak_ptr<RequiredExtensionsRegistryState> registryState, uint64_t subscriptionId) noexcept
    {
        return RequiredExtensionsSubscription(std::move(registryState), subscriptionId);
    }
};

} // namespace isaacsim::kit::xr::teleop::bridge
