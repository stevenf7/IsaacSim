// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.


#define CARB_EXPORTS

#include <carb/PluginUtils.h>
#include <carb/settings/ISettings.h>

#include <isaacsim/xr/openxr/OpenXR.h>
#include <omni/core/IWeakObject.h>
#include <omni/ext/IExt.h>
#include <omni/kit/xr/system/openxr/IOpenXRComponent.h>
#include <omni/kit/xr/system/openxr/IOpenXRExtension.h>
#include <omni/kit/xr/tokens/XRTokens.h>


#define LOG_LEVEL carb::logging::kLevelWarn

CARB_PLUGIN_IMPL_DEPS(carb::settings::ISettings,
                      carb::events::IEvents,
                      carb::dictionary::IDictionary,
                      omni::kit::xr::openxr::IOpenXRExtension_v1)

namespace isaacsim::xr::openxr
{

class HandTrackingImpl : public omni::core::ImplementsWeak<omni::kit::xr::openxr::OpenXRComponentBase_UpdateTracking>
{

protected:
    inline void _checkOxr(XrResult err, const char* function, const char* file, int line)
    {
        if (err == XR_SUCCESS)
        {
            return;
        }

        std::vector<char> buffer(XR_MAX_RESULT_STRING_SIZE, 0);

        std::string exceptStr;
        if (m_instance != XR_NULL_HANDLE && m_xrResultToString != nullptr)
        {
            XrResult resultToStringResult = m_xrResultToString(m_instance, err, buffer.data());

            if (resultToStringResult == XR_SUCCESS)
            {
                exceptStr = buffer.data();
            }
            else
            {
                exceptStr = "Unknown OpenXR Error [" + std::to_string(err) + "]";
            }
        }
        else
        {
            exceptStr = "Unknown OpenXR Error [" + std::to_string(err) + "]";
        }

        if (err > 0)
        {
            if (err == XR_SESSION_NOT_FOCUSED)
            {
                return;
            }

            exceptStr += " ";
            exceptStr += file;
            exceptStr += ":";
            exceptStr += std::to_string(line);
            CARB_LOG_ERROR("Non-fatal OXR error: %s", exceptStr.c_str());
            return;
        }

        throw omni::kit::xr::XRException(exceptStr, function, file, line);
    }

#define CHECK_OXR(call) HandTrackingImpl::_checkOxr((call), __FUNCTION__, __FILE__, __LINE__)

public:
    struct HandJointResult
    {
        std::array<XrHandJointLocationEXT, XR_HAND_JOINT_COUNT_EXT> jointLocations;
        std::array<XrHandJointVelocityEXT, XR_HAND_JOINT_COUNT_EXT> jointVelocities;
    };

    // Returns true if hand is visible or a reasonable interpolation was possible at "time".
    // Results are stored in jointLocations / jointVelocities / jointPoses respectively
    std::optional<HandJointResult> querySingleHandJoints(XrHandEXT hand, std::optional<XrTime> time)
    {
        auto& tracker = hand == XR_HAND_LEFT_EXT ? m_handTrackerLeft : m_handTrackerRight;
        CARB_PROFILE_ZONE(carb::profiler::kCaptureMaskDefault, "HandTrackingExtension::querySingleHandJoints");
        HandJointResult result = {};

        XrHandJointsLocateInfoEXT locateInfo{ XR_TYPE_HAND_JOINTS_LOCATE_INFO_EXT };
        locateInfo.baseSpace = m_trackingSpace;
        locateInfo.time = time.value_or(m_lastFrameData.frameTime);

        if (locateInfo.time <= 0)
        {
            return {};
        }

        if (tracker == XR_NULL_HANDLE)
        {
            return {};
        }

        // Set our member arrays m_jointLocations/velocities as the targets
        XrHandJointVelocitiesEXT velocityTarget{ XR_TYPE_HAND_JOINT_VELOCITIES_EXT };
        velocityTarget.jointVelocities = result.jointVelocities.data();
        velocityTarget.jointCount = static_cast<uint32_t>(result.jointVelocities.size());

        XrHandJointLocationsEXT locationTarget{ XR_TYPE_HAND_JOINT_LOCATIONS_EXT };
        locationTarget.jointLocations = result.jointLocations.data();
        locationTarget.jointCount = static_cast<uint32_t>(result.jointLocations.size());
        locationTarget.next = &velocityTarget;
        if (XR_SUCCESS != m_xrLocateHandJointsEXT(tracker, &locateInfo, &locationTarget))
        {
            return {};
        }

        if (!locationTarget.isActive)
        {
            return {};
        }

        return result;
    }

protected:
    virtual std::string getDisplayName() override
    {
        return "IsaacSim OpenXR Hand Tracking";
    }

    virtual std::string getOpenXRComponentId() override
    {
        return "isaacsim.xr.openxr.hand_tracking";
    }

    virtual void getRequiredExtensions(std::vector<std::string>& ret) override
    {
        ret = std::vector<std::string>{ XR_EXT_HAND_TRACKING_EXTENSION_NAME };
    }

    virtual bool initialize(XrInstance instance,
                            PFN_xrGetInstanceProcAddr xrGetInstanceProcAddr,
                            XrSystemId xrSystemId,
                            XrVersion openXRVersion) override
    {
        m_instance = instance;

// Load required function pointers
#define LOAD_XR_FUNCTION(name)                                                                                         \
    CHECK_OXR(xrGetInstanceProcAddr(m_instance, #name, reinterpret_cast<PFN_xrVoidFunction*>(&m_##name)))
        LOAD_XR_FUNCTION(xrResultToString);
        LOAD_XR_FUNCTION(xrGetSystemProperties);
        LOAD_XR_FUNCTION(xrCreateHandTrackerEXT);
        LOAD_XR_FUNCTION(xrDestroyHandTrackerEXT);
        LOAD_XR_FUNCTION(xrLocateHandJointsEXT);
        LOAD_XR_FUNCTION(xrCreateReferenceSpace);


        // Check if current system has hand tracking support
        XrSystemHandTrackingPropertiesEXT handTrackingProperties{ XR_TYPE_SYSTEM_HAND_TRACKING_PROPERTIES_EXT };
        XrSystemProperties systemProperties{ XR_TYPE_SYSTEM_PROPERTIES, &handTrackingProperties };

        CHECK_OXR(m_xrGetSystemProperties(m_instance, xrSystemId, &systemProperties));

        m_supportsHandTracking = handTrackingProperties.supportsHandTracking;

        return m_supportsHandTracking;
    }

    virtual void onSessionStart(XrSession session, omni::kit::xr::XRToken mode) override
    {
        m_session = session;

        createSpace();

        // Create hand trackers for default set of hand joints.
        m_handTrackerLeft = XrHandTrackerEXT{};
        m_handTrackerRight = XrHandTrackerEXT{};
        XrHandTrackerCreateInfoEXT handInfo{ XR_TYPE_HAND_TRACKER_CREATE_INFO_EXT };
        handInfo.handJointSet = XR_HAND_JOINT_SET_DEFAULT_EXT;

        handInfo.hand = XR_HAND_LEFT_EXT;
        CHECK_OXR(m_xrCreateHandTrackerEXT(m_session, &handInfo, &m_handTrackerLeft));

        handInfo.hand = XR_HAND_RIGHT_EXT;
        CHECK_OXR(m_xrCreateHandTrackerEXT(m_session, &handInfo, &m_handTrackerRight));
    }

    virtual void onSessionStop(XrSession session) override
    {
        if (m_handTrackerLeft != XR_NULL_HANDLE)
        {
            CHECK_OXR(m_xrDestroyHandTrackerEXT(m_handTrackerLeft));
            m_handTrackerLeft = XR_NULL_HANDLE;
        }
        if (m_handTrackerRight != XR_NULL_HANDLE)
        {
            CHECK_OXR(m_xrDestroyHandTrackerEXT(m_handTrackerRight));
            m_handTrackerRight = XR_NULL_HANDLE;
        }

        m_session = XR_NULL_HANDLE;
    }

    // Check for tracked locations every frame
    virtual void updateTracking(const omni::kit::xr::openxr::UpdateTrackingFrameData_v1& frameData) override
    {
        CARB_PROFILE_ZONE(carb::profiler::kCaptureMaskDefault, "HandTrackingExtension::updateTracking");
        if (!m_supportsHandTracking)
        {
            return;
        }

        m_lastFrameData = frameData;
    }

protected:
    static constexpr XrPosef identity_pose = { { 0.0f, 0.0f, 0.0f, 1.0f }, { 0.0f, 0.0f, 0.0f } };

    // Create m_trackingSpace which will be used for all future hand joint queries.
    void createSpace()
    {
        XrReferenceSpaceCreateInfo referenceSpaceCreateInfo{ XR_TYPE_REFERENCE_SPACE_CREATE_INFO };
        referenceSpaceCreateInfo.referenceSpaceType = XR_REFERENCE_SPACE_TYPE_STAGE;
        referenceSpaceCreateInfo.poseInReferenceSpace = identity_pose;

        CHECK_OXR(m_xrCreateReferenceSpace(m_session, &referenceSpaceCreateInfo, &m_trackingSpace));
    }

    XrInstance m_instance = XR_NULL_HANDLE;
    XrSession m_session = XR_NULL_HANDLE;

    // Space used for hand trackers. Defaults to Stage space
    XrSpace m_trackingSpace = XR_NULL_HANDLE;

    XrHandTrackerEXT m_handTrackerLeft = XR_NULL_HANDLE;
    XrHandTrackerEXT m_handTrackerRight = XR_NULL_HANDLE;

    // Required core OpenXR functions
    PFN_xrResultToString m_xrResultToString = nullptr;
    PFN_xrGetSystemProperties m_xrGetSystemProperties = nullptr;
    PFN_xrCreateReferenceSpace m_xrCreateReferenceSpace = nullptr;

    // Required extension functions from XR_EXT_hand_tracking
    PFN_xrCreateHandTrackerEXT m_xrCreateHandTrackerEXT = nullptr;
    PFN_xrLocateHandJointsEXT m_xrLocateHandJointsEXT = nullptr;
    PFN_xrDestroyHandTrackerEXT m_xrDestroyHandTrackerEXT = nullptr;

    bool m_supportsHandTracking = false;
    omni::kit::xr::openxr::UpdateTrackingFrameData_v1 m_lastFrameData = {};
};

class OpenxrImpl : public IOpenxr
{
public:
    virtual ~OpenxrImpl() = default;

    virtual std::optional<std::array<XrHandJointLocationEXT, XR_HAND_JOINT_COUNT_EXT>> locate_hand_joints(
        XrHandEXT hand, std::optional<XrTime> time) noexcept(false) override
    {
        auto hand_tracker = m_component.getObjectPtr().as<HandTrackingImpl>().get();
        if (hand_tracker == nullptr)
        {
            return {};
        }

        const auto result = hand_tracker->querySingleHandJoints(hand, time);

        if (result)
        {
            return result->jointLocations;
        }
        else
        {
            return {};
        }
    }

    void initExtension() noexcept(false)
    {
        try
        {
            // create this component and register it
            omni::core::ObjectPtr<omni::kit::xr::openxr::IOpenXRComponent_v1> component =
                omni::core::steal(new HandTrackingImpl()).as<omni::kit::xr::openxr::IOpenXRComponent_v1>();

            m_component = component;
            auto* cached_interface = carb::getCachedInterface<omni::kit::xr::openxr::IOpenXRExtension_v1>();
            if (cached_interface)
            {
                cached_interface->getComponentRegistry()->registerOpenXRComponent(component);
            }
        }
        catch (...)
        {
            CARB_LOG_ERROR("Failed to register OpenXR component");
        }
    }

    void deinitExtension() noexcept(false)
    {
        try
        {
            omni::core::ObjectPtr<omni::kit::xr::openxr::IOpenXRComponent_v1> component = m_component.getObjectPtr();
            if (!component)
            {
                // component was already shutdown
                return;
            }

            carb::getCachedInterface<omni::kit::xr::openxr::IOpenXRExtension_v1>()
                ->getComponentRegistry()
                ->unregisterOpenXRComponent(component);
            m_component = nullptr;
        }
        catch (...)
        {
            CARB_LOG_ERROR("Failed to unregister OpenXR component");
        }
    }

private:
    omni::core::WeakPtr<omni::kit::xr::openxr::IOpenXRComponent_v1> m_component; // component instance
};

}

namespace
{
isaacsim::xr::openxr::OpenxrImpl* g_openxr_impl = nullptr;
}

void const CARB_ABI CreateOpenXR()
{
    if (g_openxr_impl == nullptr)
    {
        g_openxr_impl = new isaacsim::xr::openxr::OpenxrImpl();
        g_openxr_impl->initExtension();
    }
}

CARB_EXPORT void carbOnPluginStartup()
{
    CreateOpenXR();
}

CARB_EXPORT void carbOnPluginShutdown()
{
    g_openxr_impl->deinitExtension();
    delete g_openxr_impl;
}

const struct carb::PluginImplDesc pluginImplDesc = { "isaacsim.xr.openxr.plugin", "OpenXR interface", "NVIDIA",
                                                     carb::PluginHotReload::eEnabled, "dev" };

CARB_PLUGIN_IMPL(pluginImplDesc, isaacsim::xr::openxr::OpenxrImpl)

void fillInterface(isaacsim::xr::openxr::OpenxrImpl& iface)
{
    CreateOpenXR();
    iface = *g_openxr_impl;
}
