// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/PluginUtils.h>

#include <isaacsim/xr/openxr/OpenXR.h>
#include <omni/ext/IExt.h>

const struct carb::PluginImplDesc pluginImplDesc = { "isaacsim.xr.openxr.plugin", "Helpful text describing the plugin",
                                                     "Author", carb::PluginHotReload::eEnabled, "dev" };

namespace isaacsim
{
namespace xr
{
namespace openxr
{

void setDefaultStatus(const char* status)
{
    CARB_LOG_INFO("setDefaultStatus %s", status);
}

class OpenxrImpl : public IOpenxr
{
public:
    bool registerObject(uint32_t id) override
    {
        CARB_LOG_INFO("registerObject %d", id);
        mId = id;
        return mId ? true : false;
    }

private:
    uint32_t mId = 0;
};

/**
 * The Extension class
 */
class Extension : public omni::ext::IExt
{
public:
    /**
     * Method called when the extension is loaded/enabled
     */
    void onStartup(const char* extId) override
    {
        CARB_LOG_INFO("onStartup %s", extId);
    }

    /**
     * Method called when the extension is disabled
     */
    void onShutdown() override
    {
        CARB_LOG_INFO("onShutdown");
    }
};

} // namespace isaacsim
} // namespace xr
} // namespace openxr

/**
 * Optional function (called the first time an interface is acquired from the plugin library)
 */
CARB_EXPORT void carbOnPluginStartup()
{
    CARB_LOG_INFO("carbOnPluginStartup");
}

/**
 * Optional function (called right before the OS release the plugin library)
 */
CARB_EXPORT void carbOnPluginShutdown()
{
    CARB_LOG_INFO("carbOnPluginShutdown");
}

CARB_PLUGIN_IMPL(pluginImplDesc, isaacsim::xr::openxr::OpenxrImpl, isaacsim::xr::openxr::Extension)

void fillInterface(isaacsim::xr::openxr::OpenxrImpl& iface)
{
}

void fillInterface(isaacsim::xr::openxr::Extension& iface)
{
}
