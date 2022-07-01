#define CARB_EXPORTS

#include "MjcfImporter.h"
#include "stdio.h"

#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>

#include <omni/ext/IExt.h>
#include <omni/isaac/mjcf/mjcf.h>
#include <omni/kit/IApp.h>
#include <omni/kit/IStageUpdate.h>
// clang-format off
#include <omni/usd/UsdContextIncludes.h>
#include <omni/usd/UsdContext.h>
// clang-format on

#define EXTENSION_NAME "omni.isaac.mjcf.plugin"

using namespace carb;

const struct carb::PluginImplDesc kPluginImpl = { EXTENSION_NAME, "MJCF Utilities", "NVIDIA",
                                                  carb::PluginHotReload::eEnabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::mjcf::Mjcf)
CARB_PLUGIN_IMPL_DEPS(omni::kit::IApp, carb::logging::ILogging)

namespace
{

// passed in from python
void createAssetFromMJCF(const char* fileName, const char* primName, const omni::isaac::mjcf::ImportConfig& config)
{
    omni::isaac::mjcf::MJCFImporter mjcf(fileName);
    if (!mjcf.isLoaded)
    {
        printf("cannot load mjcf xml file\n");
    }
    Transform trans = Transform();
    pxr::UsdStageWeakPtr stage = omni::usd::UsdContext::getContext()->getStage();

    if (!mjcf.AddPhysicsEntities(stage, trans, primName, config))
    {
        printf("no physics entities found!\n");
    }
}

}

CARB_EXPORT void carbOnPluginStartup()
{
    CARB_LOG_INFO("Startup MJCF Extension");
}


CARB_EXPORT void carbOnPluginShutdown()
{
}


void fillInterface(omni::isaac::mjcf::Mjcf& iface)
{
    using namespace omni::isaac::mjcf;
    memset(&iface, 0, sizeof(iface));
    // iface.helloWorld = helloWorld;
    iface.createAssetFromMJCF = createAssetFromMJCF;
    // iface.importRobot = importRobot;
}
