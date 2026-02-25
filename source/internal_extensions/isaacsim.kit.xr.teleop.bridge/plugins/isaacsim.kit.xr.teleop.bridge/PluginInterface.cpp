// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#define CARB_EXPORTS

#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>
#include <carb/settings/SettingsUtils.h>

#include <isaacsim/kit/xr/teleop/bridge/ITeleopBridge.h>
#include <omni/core/IWeakObject.h>
#include <omni/kit/xr/system/openxr/IOpenXRComponent.h>
#include <omni/kit/xr/system/openxr/IOpenXRExtension.h>
#include <openxr/openxr.h>

#include <algorithm>
#include <atomic>
#include <cinttypes>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

// Plugin dependencies
CARB_PLUGIN_IMPL_DEPS(omni::kit::xr::openxr::IOpenXRExtension_v1, carb::settings::ISettings)

namespace isaacsim::kit::xr::teleop::bridge
{

namespace
{
constexpr const char* kRequiredExtensionsSetSetting = "/exts/isaacsim.kit.xr.teleop.bridge/openxr/requiredExtensions/set";
constexpr const char* kRequiredExtensionsAddSetting = "/exts/isaacsim.kit.xr.teleop.bridge/openxr/requiredExtensions/add";
constexpr const char* kRequiredExtensionsRemoveSetting =
    "/exts/isaacsim.kit.xr.teleop.bridge/openxr/requiredExtensions/remove";

std::vector<std::string> getStringArraySetting(carb::settings::ISettings* settings, const char* path)
{
    std::vector<std::string> values;
    if (!settings)
    {
        return values;
    }

    const size_t arrayLength = settings->getArrayLength(path);
    values.reserve(arrayLength);
    for (size_t i = 0; i < arrayLength; ++i)
    {
        std::string value = carb::settings::getStringAt(settings, path, i);
        if (!value.empty())
        {
            values.push_back(std::move(value));
        }
    }
    return values;
}

void appendUniqueValues(std::vector<std::string>& values, const std::vector<std::string>& toAppend)
{
    for (const std::string& value : toAppend)
    {
        if (value.empty())
        {
            continue;
        }

        if (std::find(values.begin(), values.end(), value) == values.end())
        {
            values.push_back(value);
        }
    }
}

void removeValues(std::vector<std::string>& values, const std::vector<std::string>& toRemove)
{
    if (toRemove.empty())
    {
        return;
    }

    const std::unordered_set<std::string> removeSet(toRemove.begin(), toRemove.end());
    values.erase(std::remove_if(values.begin(), values.end(),
                                [&removeSet](const std::string& value) { return removeSet.count(value) > 0; }),
                 values.end());
}

void logExtensionList(const char* stage, const std::vector<std::string>& values)
{
    CARB_LOG_INFO("%s (%zu)", stage, values.size());
    for (const std::string& value : values)
    {
        CARB_LOG_INFO("  - %s", value.c_str());
    }
}

class RequiredExtensionsRegistryStateImpl final : public ITeleopBridge::RequiredExtensionsRegistryState
{
public:
    uint64_t subscribe(const ITeleopBridge::RequiredExtensionsCallback& callback)
    {
        if (!callback)
        {
            CARB_LOG_WARN("Ignored required extension callback subscription: callback is empty");
            return 0;
        }

        const uint64_t subscriptionId = m_nextSubscriptionId.fetch_add(1);
        std::lock_guard<std::mutex> lock(m_mutex);
        m_callbacks[subscriptionId] = callback;
        return subscriptionId;
    }

    virtual void unsubscribe(uint64_t subscriptionId) noexcept override
    {
        if (subscriptionId == 0)
        {
            return;
        }

        std::lock_guard<std::mutex> lock(m_mutex);
        m_callbacks.erase(subscriptionId);
    }

    std::vector<std::pair<uint64_t, ITeleopBridge::RequiredExtensionsCallback>> getCallbackSnapshot() const
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        std::vector<std::pair<uint64_t, ITeleopBridge::RequiredExtensionsCallback>> callbackEntries;
        callbackEntries.reserve(m_callbacks.size());
        for (const auto& callbackEntry : m_callbacks)
        {
            callbackEntries.push_back(callbackEntry);
        }
        return callbackEntries;
    }

    void clear()
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_callbacks.clear();
        m_nextSubscriptionId.store(1);
    }

private:
    mutable std::mutex m_mutex;
    std::unordered_map<uint64_t, ITeleopBridge::RequiredExtensionsCallback> m_callbacks;
    std::atomic<uint64_t> m_nextSubscriptionId{ 1 };
};

std::shared_ptr<RequiredExtensionsRegistryStateImpl> g_requiredExtensionsRegistryState =
    std::make_shared<RequiredExtensionsRegistryStateImpl>();

void appendRequiredExtensionsFromCallbacks(std::vector<std::string>& requiredExtensions)
{
    auto registryState = g_requiredExtensionsRegistryState;
    if (!registryState)
    {
        return;
    }

    const std::vector<std::pair<uint64_t, ITeleopBridge::RequiredExtensionsCallback>> callbackEntries =
        registryState->getCallbackSnapshot();

    for (const auto& callbackEntry : callbackEntries)
    {
        const uint64_t subscriptionId = callbackEntry.first;
        const auto& callback = callbackEntry.second;
        if (!callback)
        {
            continue;
        }

        try
        {
            std::vector<std::string> callbackExtensions = callback();
            if (!callbackExtensions.empty())
            {
                CARB_LOG_INFO(
                    "requiredExtensions.callback[%" PRIu64 "] (%zu)", subscriptionId, callbackExtensions.size());
            }
            appendUniqueValues(requiredExtensions, callbackExtensions);
        }
        catch (...)
        {
            CARB_LOG_ERROR("requiredExtensions.callback[%" PRIu64 "] raised an exception", subscriptionId);
        }
    }
}
} // namespace

/**
 * @brief Identity pose constant used as the default pose when creating reference spaces.
 *
 * @details Matches the identity pose definition in Kit's OxrUtils.h. Quaternion is
 * {x=0, y=0, z=0, w=1} and position is {x=0, y=0, z=0}.
 */
static constexpr XrPosef kIdentityPose = { { 0.0f, 0.0f, 0.0f, 1.0f }, { 0.0f, 0.0f, 0.0f } };

/**
 * @class BridgeComponent
 * @brief OpenXR Component that receives lifecycle callbacks from Kit's OpenXR system.
 *
 * @details This component receives lifecycle callbacks:
 * - initialize(): Called with instance and xrGetInstanceProcAddr.
 * - onSessionStart(): Called when XR session starts.
 * - onSessionStop(): Called when XR session stops.
 *
 * @note For callbacks to fire, this component must be registered BEFORE
 * OpenXR creates its instance. This requires the extension to load early
 * in the app startup, before XR mode is activated.
 */
class BridgeComponent : public omni::core::ImplementsWeak<omni::kit::xr::openxr::OpenXRComponentBase>
{
public:
    /**
     * @brief Get the cached OpenXR instance handle.
     *
     * @return The XrInstance handle, or XR_NULL_HANDLE if not initialized.
     */
    XrInstance getInstance() const
    {
        return m_instance;
    }

    /**
     * @brief Get the cached OpenXR session handle.
     *
     * @return The XrSession handle, or XR_NULL_HANDLE if no active session.
     */
    XrSession getSession() const
    {
        return m_session;
    }

    /**
     * @brief Get the OpenXR stage reference space handle.
     *
     * @details Creates the stage reference space lazily on first request for the active session.
     *
     * @return The XrSpace handle for the stage space, or XR_NULL_HANDLE if unavailable.
     */
    XrSpace getStageSpace()
    {
        ensureStageSpace();
        return m_stageSpace;
    }

    /**
     * @brief Get the cached xrGetInstanceProcAddr function pointer.
     *
     * @return The function pointer, or nullptr if not initialized.
     */
    PFN_xrGetInstanceProcAddr getInstanceProcAddr() const
    {
        return m_xrGetInstanceProcAddr;
    }

protected:
    /**
     * @brief Get the human-readable display name for this component.
     *
     * @return The display name string.
     */
    virtual std::string getDisplayName() override
    {
        return "Isaac Kit XR Teleop Bridge";
    }

    /**
     * @brief Get the unique identifier for this OpenXR component.
     *
     * @return The component identifier string.
     */
    virtual std::string getOpenXRComponentId() override
    {
        return "isaacsim.kit.xr.teleop.bridge";
    }

    /**
     * @brief Populate the list of required OpenXR extensions for this component.
     *
     * @param[out] ret Vector to which required extension names are appended.
     */
    virtual void getRequiredExtensions(std::vector<std::string>& ret) override
    {
        std::vector<std::string> requiredExtensions;
        auto* settings = carb::getCachedInterface<carb::settings::ISettings>();
        if (!settings)
        {
            CARB_LOG_WARN("ISettings not available, using hardcoded defaults");
            requiredExtensions = { "XR_KHR_convert_timespec_time", "XR_NVX1_tensor_data" };
        }
        else
        {
            const auto getAndLog = [settings](const char* path, const char* stage)
            {
                std::vector<std::string> values = getStringArraySetting(settings, path);
                logExtensionList(stage, values);
                return values;
            };

            requiredExtensions = getAndLog(kRequiredExtensionsSetSetting, "requiredExtensions.set");
            appendUniqueValues(requiredExtensions, getAndLog(kRequiredExtensionsAddSetting, "requiredExtensions.add"));
            removeValues(requiredExtensions, getAndLog(kRequiredExtensionsRemoveSetting, "requiredExtensions.remove"));
        }

        appendRequiredExtensionsFromCallbacks(requiredExtensions);
        logExtensionList("resolved requiredExtensions", requiredExtensions);

        ret.insert(ret.end(), requiredExtensions.begin(), requiredExtensions.end());
    }

    /**
     * @brief Initialize the component with OpenXR instance and function loader.
     *
     * @details Caches the OpenXR instance handle and xrGetInstanceProcAddr, then
     * resolves function pointers for xrCreateReferenceSpace and xrDestroySpace
     * needed to manage stage reference spaces during session lifecycle.
     *
     * @param[in] instance The OpenXR instance handle.
     * @param[in] xrGetInstanceProcAddr Function pointer for resolving OpenXR functions.
     * @param[in] xrSystemId The OpenXR system identifier.
     * @param[in] openXRVersion The OpenXR runtime version.
     *
     * @return True if initialization succeeded, false on failure.
     */
    virtual bool initialize(XrInstance instance,
                            PFN_xrGetInstanceProcAddr xrGetInstanceProcAddr,
                            XrSystemId xrSystemId,
                            XrVersion openXRVersion) override
    {
        CARB_LOG_INFO("Component initialize() called with instance %p", instance);

        m_instance = instance;
        m_xrGetInstanceProcAddr = xrGetInstanceProcAddr;

        // Load required function pointers using the provided xrGetInstanceProcAddr
        XrResult result = xrGetInstanceProcAddr(
            instance, "xrCreateReferenceSpace", reinterpret_cast<PFN_xrVoidFunction*>(&m_xrCreateReferenceSpace));
        if (XR_FAILED(result) || !m_xrCreateReferenceSpace)
        {
            CARB_LOG_ERROR("Failed to get xrCreateReferenceSpace");
            return false;
        }

        result =
            xrGetInstanceProcAddr(instance, "xrDestroySpace", reinterpret_cast<PFN_xrVoidFunction*>(&m_xrDestroySpace));
        if (XR_FAILED(result) || !m_xrDestroySpace)
        {
            CARB_LOG_ERROR("Failed to get xrDestroySpace");
            return false;
        }

        CARB_LOG_INFO("Component initialized successfully");
        return true;
    }

    /**
     * @brief Shut down the component and release cached handles.
     *
     * @details Resets the OpenXR instance handle and all resolved function pointers.
     * Stage space cleanup is handled in onSessionStop().
     *
     * @param[in] instance The OpenXR instance handle being destroyed.
     */
    virtual void shutdown(XrInstance instance) override
    {
        CARB_LOG_INFO("Component shutdown() called");

        // Cleanup is handled in onSessionStop, but reset state here too
        m_instance = XR_NULL_HANDLE;
        m_xrGetInstanceProcAddr = nullptr;
        m_xrCreateReferenceSpace = nullptr;
        m_xrDestroySpace = nullptr;
    }

    /**
     * @brief Handle the start of an OpenXR session.
     *
     * @details Caches the session handle. Stage reference space creation is deferred
     * until getStageSpace() is called.
     *
     * @param[in] session The newly started OpenXR session.
     * @param[in] mode The XR mode token indicating the type of session.
     */
    virtual void onSessionStart(XrSession session, omni::kit::xr::XRToken mode) override
    {
        CARB_LOG_INFO("onSessionStart() called with session %p", session);

        if (m_stageSpace != XR_NULL_HANDLE && m_xrDestroySpace)
        {
            m_xrDestroySpace(m_stageSpace);
            m_stageSpace = XR_NULL_HANDLE;
        }
        m_session = session;
    }

    /**
     * @brief Handle the stop of an OpenXR session.
     *
     * @details Destroys the stage reference space and resets the session handle.
     *
     * @param[in] session The OpenXR session being stopped.
     */
    virtual void onSessionStop(XrSession session) override
    {
        CARB_LOG_INFO("onSessionStop() called");

        // Destroy the stage space
        if (m_stageSpace != XR_NULL_HANDLE && m_xrDestroySpace)
        {
            m_xrDestroySpace(m_stageSpace);
            m_stageSpace = XR_NULL_HANDLE;
        }

        m_session = XR_NULL_HANDLE;
    }

private:
    /**
     * @brief Ensure stage reference space exists for the active session.
     *
     * @details Tries STAGE first, then falls back to LOCAL if STAGE is unsupported.
     */
    void ensureStageSpace()
    {
        if (m_stageSpace != XR_NULL_HANDLE || m_session == XR_NULL_HANDLE || !m_xrCreateReferenceSpace)
        {
            return;
        }

        XrReferenceSpaceCreateInfo createInfo{ XR_TYPE_REFERENCE_SPACE_CREATE_INFO };
        createInfo.referenceSpaceType = XR_REFERENCE_SPACE_TYPE_STAGE;
        createInfo.poseInReferenceSpace = kIdentityPose;

        XrResult result = m_xrCreateReferenceSpace(m_session, &createInfo, &m_stageSpace);
        if (XR_FAILED(result))
        {
            CARB_LOG_WARN("Failed to create STAGE reference space: %d, trying LOCAL", result);
            createInfo.referenceSpaceType = XR_REFERENCE_SPACE_TYPE_LOCAL;
            result = m_xrCreateReferenceSpace(m_session, &createInfo, &m_stageSpace);
            if (XR_FAILED(result))
            {
                CARB_LOG_ERROR("Failed to create any reference space: %d", result);
                m_stageSpace = XR_NULL_HANDLE;
                return;
            }
            CARB_LOG_WARN("Created LOCAL reference space as fallback");
            return;
        }

        CARB_LOG_INFO("Created STAGE reference space");
    }

    /** @brief Cached OpenXR instance handle. */
    XrInstance m_instance = XR_NULL_HANDLE;

    /** @brief Cached OpenXR session handle, set during onSessionStart(). */
    XrSession m_session = XR_NULL_HANDLE;

    /** @brief Cached stage reference space, created during onSessionStart(). */
    XrSpace m_stageSpace = XR_NULL_HANDLE;

    /** @brief Cached xrGetInstanceProcAddr function pointer from initialize(). */
    PFN_xrGetInstanceProcAddr m_xrGetInstanceProcAddr = nullptr;

    /** @brief Resolved xrCreateReferenceSpace function pointer. */
    PFN_xrCreateReferenceSpace m_xrCreateReferenceSpace = nullptr;

    /** @brief Resolved xrDestroySpace function pointer. */
    PFN_xrDestroySpace m_xrDestroySpace = nullptr;
};

/**
 * @class TeleopBridgeImpl
 * @brief Implementation of the ITeleopBridge Carbonite interface.
 *
 * @details This class implements the Carbonite interface and manages the OpenXR component
 * registration with Kit's XR system. It delegates handle queries to
 * IOpenXRExtension_v1 when available, falling back to the BridgeComponent
 * for handles not exposed by that interface.
 */
class TeleopBridgeImpl : public ITeleopBridge
{
public:
    virtual ~TeleopBridgeImpl() = default;

    /**
     * @brief Get the current OpenXR instance handle.
     *
     * @details Queries IOpenXRExtension_v1 first; falls back to the BridgeComponent
     * if the extension interface is not available.
     *
     * @return The XrInstance handle as uint64, or 0 if no active session.
     */
    virtual uint64_t getInstanceHandle() noexcept override
    {
        auto* ext = carb::getCachedInterface<omni::kit::xr::openxr::IOpenXRExtension_v1>();
        if (ext)
        {
            return ext->getInstanceHandle();
        }
        // Fallback to component if extension not available
        auto* component = getComponent();
        return component ? reinterpret_cast<uint64_t>(component->getInstance()) : 0;
    }

    /**
     * @brief Get the current OpenXR session handle.
     *
     * @details Queries IOpenXRExtension_v1 first; falls back to the BridgeComponent
     * if the extension interface is not available.
     *
     * @return The XrSession handle as uint64, or 0 if no active session.
     */
    virtual uint64_t getSessionHandle() noexcept override
    {
        auto* ext = carb::getCachedInterface<omni::kit::xr::openxr::IOpenXRExtension_v1>();
        if (ext)
        {
            return ext->getSessionHandle();
        }
        // Fallback to component if extension not available
        auto* component = getComponent();
        return component ? reinterpret_cast<uint64_t>(component->getSession()) : 0;
    }

    /**
     * @brief Get the OpenXR stage reference space handle.
     *
     * @details Always uses the BridgeComponent since IOpenXRExtension_v1 does not
     * expose the stage space handle.
     *
     * @return The XrSpace handle as uint64, or 0 if no active session.
     */
    virtual uint64_t getStageSpaceHandle() noexcept override
    {
        // IOpenXRExtension_v1 doesn't expose this, use component
        auto* component = getComponent();
        return component ? reinterpret_cast<uint64_t>(component->getStageSpace()) : 0;
    }

    /**
     * @brief Get the xrGetInstanceProcAddr function pointer.
     *
     * @details Always uses the BridgeComponent since IOpenXRExtension_v1 does not
     * expose the function pointer.
     *
     * @return The function pointer as uint64, or 0 if not available.
     */
    virtual uint64_t getInstanceProcAddr() noexcept override
    {
        // IOpenXRExtension_v1 doesn't expose this, use component
        auto* component = getComponent();
        return component ? reinterpret_cast<uint64_t>(component->getInstanceProcAddr()) : 0;
    }

    virtual RequiredExtensionsSubscription subscribeRequiredExtensions(const RequiredExtensionsCallback& callback) noexcept override
    {
        auto registryState = g_requiredExtensionsRegistryState;
        if (!registryState)
        {
            CARB_LOG_WARN("Required extension callback registry is unavailable");
            return RequiredExtensionsSubscription();
        }

        const uint64_t subscriptionId = registryState->subscribe(callback);
        if (subscriptionId == 0)
        {
            return RequiredExtensionsSubscription();
        }

        return makeRequiredExtensionsSubscription(registryState, subscriptionId);
    }

    /**
     * @brief Initialize the extension by registering the OpenXR component.
     *
     * @details Creates a BridgeComponent instance and registers it with Kit's OpenXR
     * component registry via IOpenXRExtension_v1.
     */
    void initExtension() noexcept
    {
        try
        {
            CARB_LOG_INFO("Registering OpenXR component");

            // Create the component and register it with Kit's OpenXR system
            omni::core::ObjectPtr<omni::kit::xr::openxr::IOpenXRComponent_v1> component =
                omni::core::steal(new BridgeComponent()).as<omni::kit::xr::openxr::IOpenXRComponent_v1>();

            m_component = component;

            auto* xrInterface = carb::getFramework()->acquireInterface<omni::kit::xr::openxr::IOpenXRExtension_v1>();
            if (xrInterface)
            {
                auto componentRegistry = xrInterface->getComponentRegistry();
                if (componentRegistry)
                {
                    componentRegistry->registerOpenXRComponent(component);
                    CARB_LOG_INFO("Component registered successfully");
                }
            }
            else
            {
                CARB_LOG_WARN("IOpenXRExtension_v1 not available");
            }
        }
        catch (...)
        {
            CARB_LOG_ERROR("Failed to register component");
        }
    }

    /**
     * @brief Deinitialize the extension by unregistering the OpenXR component.
     *
     * @details Unregisters the BridgeComponent from Kit's OpenXR component registry
     * and releases the component reference.
     */
    void deinitExtension() noexcept
    {
        try
        {
            omni::core::ObjectPtr<omni::kit::xr::openxr::IOpenXRComponent_v1> component = m_component.getObjectPtr();
            if (!component)
            {
                return;
            }

            auto* cachedInterface = carb::getCachedInterface<omni::kit::xr::openxr::IOpenXRExtension_v1>();
            if (cachedInterface)
            {
                cachedInterface->getComponentRegistry()->unregisterOpenXRComponent(component);
            }
            m_component = nullptr;
        }
        catch (...)
        {
            CARB_LOG_ERROR("Exception during component unregistration");
        }
    }

private:
    /**
     * @brief Get the underlying BridgeComponent pointer from the weak reference.
     *
     * @return Pointer to the BridgeComponent, or nullptr if the component has been released.
     */
    BridgeComponent* getComponent() const
    {
        auto componentPtr = m_component.getObjectPtr();
        if (componentPtr)
        {
            return componentPtr.as<BridgeComponent>().get();
        }
        return nullptr;
    }

    /** @brief Weak reference to the registered OpenXR component. */
    omni::core::WeakPtr<omni::kit::xr::openxr::IOpenXRComponent_v1> m_component;
};

} // namespace isaacsim::kit::xr::teleop::bridge

// ============================================================================
// Plugin lifecycle
// ============================================================================

namespace
{
/** @brief Global pointer to the singleton TeleopBridgeImpl instance. */
isaacsim::kit::xr::teleop::bridge::TeleopBridgeImpl* g_teleopBridgeImpl = nullptr;
}

/**
 * @brief Carbonite plugin startup callback.
 *
 * @details Creates the TeleopBridgeImpl singleton and registers the OpenXR component.
 */
CARB_EXPORT void carbOnPluginStartup()
{
    CARB_LOG_INFO("Plugin startup");
    if (!isaacsim::kit::xr::teleop::bridge::g_requiredExtensionsRegistryState)
    {
        isaacsim::kit::xr::teleop::bridge::g_requiredExtensionsRegistryState =
            std::make_shared<isaacsim::kit::xr::teleop::bridge::RequiredExtensionsRegistryStateImpl>();
    }

    if (g_teleopBridgeImpl == nullptr)
    {
        g_teleopBridgeImpl = new isaacsim::kit::xr::teleop::bridge::TeleopBridgeImpl();
        g_teleopBridgeImpl->initExtension();
    }
}

/**
 * @brief Carbonite plugin shutdown callback.
 *
 * @details Unregisters the OpenXR component and destroys the TeleopBridgeImpl singleton.
 */
CARB_EXPORT void carbOnPluginShutdown()
{
    if (isaacsim::kit::xr::teleop::bridge::g_requiredExtensionsRegistryState)
    {
        isaacsim::kit::xr::teleop::bridge::g_requiredExtensionsRegistryState->clear();
        isaacsim::kit::xr::teleop::bridge::g_requiredExtensionsRegistryState.reset();
    }

    if (g_teleopBridgeImpl)
    {
        g_teleopBridgeImpl->deinitExtension();
        delete g_teleopBridgeImpl;
        g_teleopBridgeImpl = nullptr;
    }
}

/** @brief Plugin descriptor with name, description, and configuration. */
const struct carb::PluginImplDesc g_kPluginDesc = { "isaacsim.kit.xr.teleop.bridge.plugin",
                                                    "Isaac Kit XR Teleop Bridge - OpenXR Component", "NVIDIA",
                                                    carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(g_kPluginDesc, isaacsim::kit::xr::teleop::bridge::TeleopBridgeImpl)

/**
 * @brief Fill the Carbonite interface with the singleton TeleopBridgeImpl.
 *
 * @details Called by the Carbonite plugin system when the interface is acquired.
 * Ensures the singleton is created if it does not already exist.
 *
 * @param[out] iface Reference to the interface object to populate.
 */
void fillInterface(isaacsim::kit::xr::teleop::bridge::TeleopBridgeImpl& iface)
{
    if (!isaacsim::kit::xr::teleop::bridge::g_requiredExtensionsRegistryState)
    {
        isaacsim::kit::xr::teleop::bridge::g_requiredExtensionsRegistryState =
            std::make_shared<isaacsim::kit::xr::teleop::bridge::RequiredExtensionsRegistryStateImpl>();
    }

    // Ensure initialization happens
    if (g_teleopBridgeImpl == nullptr)
    {
        g_teleopBridgeImpl = new isaacsim::kit::xr::teleop::bridge::TeleopBridgeImpl();
        g_teleopBridgeImpl->initExtension();
    }
    iface = *g_teleopBridgeImpl;
}
