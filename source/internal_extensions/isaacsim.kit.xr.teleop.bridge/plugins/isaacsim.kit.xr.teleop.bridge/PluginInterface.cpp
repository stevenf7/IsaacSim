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

#include <isaacsim/kit/xr/teleop/bridge/ITeleopBridge.h>
#include <omni/core/IWeakObject.h>
#include <omni/kit/xr/system/openxr/IOpenXRComponent.h>
#include <omni/kit/xr/system/openxr/IOpenXRExtension.h>
#include <openxr/openxr.h>

// Plugin dependencies
CARB_PLUGIN_IMPL_DEPS(omni::kit::xr::openxr::IOpenXRExtension_v1)

namespace isaacsim::kit::xr::teleop::bridge
{

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
     * @brief Get the cached OpenXR stage reference space handle.
     *
     * @return The XrSpace handle for the stage space, or XR_NULL_HANDLE if no active session.
     */
    XrSpace getStageSpace() const
    {
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
        ret.push_back("XR_KHR_convert_timespec_time");
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
        CARB_LOG_INFO("[isaacsim.kit.xr.teleop.bridge] Component initialize() called with instance %p", instance);

        m_instance = instance;
        m_xrGetInstanceProcAddr = xrGetInstanceProcAddr;

        // Load required function pointers using the provided xrGetInstanceProcAddr
        XrResult result = xrGetInstanceProcAddr(
            instance, "xrCreateReferenceSpace", reinterpret_cast<PFN_xrVoidFunction*>(&m_xrCreateReferenceSpace));
        if (XR_FAILED(result) || !m_xrCreateReferenceSpace)
        {
            CARB_LOG_ERROR("[isaacsim.kit.xr.teleop.bridge] Failed to get xrCreateReferenceSpace");
            return false;
        }

        result =
            xrGetInstanceProcAddr(instance, "xrDestroySpace", reinterpret_cast<PFN_xrVoidFunction*>(&m_xrDestroySpace));
        if (XR_FAILED(result) || !m_xrDestroySpace)
        {
            CARB_LOG_ERROR("[isaacsim.kit.xr.teleop.bridge] Failed to get xrDestroySpace");
            return false;
        }

        CARB_LOG_INFO("[isaacsim.kit.xr.teleop.bridge] Component initialized successfully");
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
        CARB_LOG_INFO("[isaacsim.kit.xr.teleop.bridge] Component shutdown() called");

        // Cleanup is handled in onSessionStop, but reset state here too
        m_instance = XR_NULL_HANDLE;
        m_xrGetInstanceProcAddr = nullptr;
        m_xrCreateReferenceSpace = nullptr;
        m_xrDestroySpace = nullptr;
    }

    /**
     * @brief Handle the start of an OpenXR session.
     *
     * @details Caches the session handle and creates a stage reference space using
     * XR_REFERENCE_SPACE_TYPE_STAGE. Falls back to XR_REFERENCE_SPACE_TYPE_LOCAL
     * if STAGE is not supported by the runtime.
     *
     * @param[in] session The newly started OpenXR session.
     * @param[in] mode The XR mode token indicating the type of session.
     */
    virtual void onSessionStart(XrSession session, omni::kit::xr::XRToken mode) override
    {
        CARB_LOG_INFO("[isaacsim.kit.xr.teleop.bridge] onSessionStart() called with session %p", session);

        m_session = session;

        // Create stage reference space (matching Kit's OxrSessionManager.cpp)
        XrReferenceSpaceCreateInfo createInfo{ XR_TYPE_REFERENCE_SPACE_CREATE_INFO };
        createInfo.referenceSpaceType = XR_REFERENCE_SPACE_TYPE_STAGE;
        createInfo.poseInReferenceSpace = kIdentityPose;

        XrResult result = m_xrCreateReferenceSpace(session, &createInfo, &m_stageSpace);
        if (XR_FAILED(result))
        {
            CARB_LOG_WARN(
                "[isaacsim.kit.xr.teleop.bridge] Failed to create STAGE reference space: %d, trying LOCAL", result);

            // Fall back to LOCAL space if STAGE is not supported
            createInfo.referenceSpaceType = XR_REFERENCE_SPACE_TYPE_LOCAL;
            result = m_xrCreateReferenceSpace(session, &createInfo, &m_stageSpace);
            if (XR_FAILED(result))
            {
                CARB_LOG_ERROR("[isaacsim.kit.xr.teleop.bridge] Failed to create any reference space: %d", result);
                m_stageSpace = XR_NULL_HANDLE;
                return;
            }
            CARB_LOG_WARN("[isaacsim.kit.xr.teleop.bridge] Created LOCAL reference space as fallback");
        }
        else
        {
            CARB_LOG_INFO("[isaacsim.kit.xr.teleop.bridge] Created STAGE reference space");
        }
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
        CARB_LOG_INFO("[isaacsim.kit.xr.teleop.bridge] onSessionStop() called");

        // Destroy the stage space
        if (m_stageSpace != XR_NULL_HANDLE && m_xrDestroySpace)
        {
            m_xrDestroySpace(m_stageSpace);
            m_stageSpace = XR_NULL_HANDLE;
        }

        m_session = XR_NULL_HANDLE;
    }

private:
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
            CARB_LOG_INFO("[isaacsim.kit.xr.teleop.bridge] Registering OpenXR component");

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
                    CARB_LOG_INFO("[isaacsim.kit.xr.teleop.bridge] Component registered successfully");
                }
            }
            else
            {
                CARB_LOG_WARN("[isaacsim.kit.xr.teleop.bridge] IOpenXRExtension_v1 not available");
            }
        }
        catch (...)
        {
            CARB_LOG_ERROR("[isaacsim.kit.xr.teleop.bridge] Failed to register component");
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
            CARB_LOG_ERROR("[isaacsim.kit.xr.teleop.bridge] Exception during component unregistration");
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
    CARB_LOG_INFO("[isaacsim.kit.xr.teleop.bridge] Plugin startup");
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
    // Ensure initialization happens
    if (g_teleopBridgeImpl == nullptr)
    {
        g_teleopBridgeImpl = new isaacsim::kit::xr::teleop::bridge::TeleopBridgeImpl();
        g_teleopBridgeImpl->initExtension();
    }
    iface = *g_teleopBridgeImpl;
}
