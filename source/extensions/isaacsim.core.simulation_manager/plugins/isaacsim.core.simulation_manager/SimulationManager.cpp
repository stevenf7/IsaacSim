// Copyright (c) 2024-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include <carb/PluginUtils.h>

#include <isaacsim/core/simulation_manager/SimulationManager.h>
#include <isaacsim/core/simulation_manager/UsdNoticeListener.h>
#include <omni/ext/IExt.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/fabric/stage/StageReaderWriter.h>

#include <algorithm>

const struct carb::PluginImplDesc pluginImplDesc = { "isaacsim.core.simulation_manager.plugin",
                                                     "Helpful text describing the plugin", "Author",
                                                     carb::PluginHotReload::eEnabled, "dev" };

namespace isaacsim
{
namespace core
{
namespace simulation_manager
{

class SimulationManagerImpl : public ISimulationManager
{
public:
    SimulationManagerImpl()
    {
        mUsdNoticeListener = new UsdNoticeListener();
        mUsdNoticeListenerKey =
            pxr::TfNotice::Register(pxr::TfCreateWeakPtr(mUsdNoticeListener), &UsdNoticeListener::handle);
    }

    ~SimulationManagerImpl()
    {
        delete mUsdNoticeListener;
    }

    int registerDeletionCallback(const std::function<void(std::string)>& callback) override
    {
        int& callbackIter = mUsdNoticeListener->getCallbackIter();
        mUsdNoticeListener->getDeletionCallbacks().emplace(callbackIter, callback);
        callbackIter += 1;
        return callbackIter - 1;
    }

    int registerPhysicsSceneAdditionCallback(const std::function<void(std::string)>& callback) override
    {
        int& callbackIter = mUsdNoticeListener->getCallbackIter();
        mUsdNoticeListener->getPhysicsSceneAdditionCallbacks().emplace(callbackIter, callback);
        callbackIter += 1;
        return callbackIter - 1;
    }

    bool deregisterCallback(const int& callbackId) override
    {
        std::map<int, std::function<void(const std::string&)>>& physicsSceneCallbacks =
            mUsdNoticeListener->getPhysicsSceneAdditionCallbacks();
        std::map<int, std::function<void(const std::string&)>>& deletiomCallbacks =
            mUsdNoticeListener->getDeletionCallbacks();
        if (physicsSceneCallbacks.count(callbackId) > 0)
        {
            physicsSceneCallbacks.erase(callbackId);
            return true;
        }
        else if (deletiomCallbacks.count(callbackId) > 0)
        {
            deletiomCallbacks.erase(callbackId);
            return true;
        }
        return false;
    }

    int& getCallbackIter() override
    {
        return mUsdNoticeListener->getCallbackIter();
    }

    void setCallbackIter(int const& val) override
    {
        int& callbackIter = mUsdNoticeListener->getCallbackIter();
        callbackIter = val;
    }
    void enableUsdNoticeHandler(bool const& flag) override
    {
        mUsdNoticeListener->enable(flag);
    }

    void enableFabricUsdNoticeHandler(long stageId, bool const& flag) override
    {
        auto iFabricUsd = carb::getCachedInterface<omni::fabric::IFabricUsd>();
        auto iStageReadWriter = carb::getCachedInterface<omni::fabric::IStageReaderWriter>();
        if (iFabricUsd && iStageReadWriter)
        {
            omni::fabric::StageReaderWriterId stageRwId = iStageReadWriter->get(stageId);
            if (stageRwId.id)
            {
                auto fabricId = iStageReadWriter->getFabricId(stageRwId);
                iFabricUsd->setEnableChangeNotifies(fabricId, flag);
                if (flag)
                {
                    CARB_PROFILE_ZONE(0, "EnableFabricUsdNoticeHandler::forceMinulaPopulate");
                    iFabricUsd->forceMinimalPopulate(fabricId);
                }
            }
        }
    }

    bool isFabricUsdNoticeHandlerEnabled(long stageId) override
    {
        auto iFabricUsd = carb::getCachedInterface<omni::fabric::IFabricUsd>();
        auto iStageReadWriter = carb::getCachedInterface<omni::fabric::IStageReaderWriter>();
        if (iFabricUsd && iStageReadWriter)
        {
            omni::fabric::StageReaderWriterId stageRwId = iStageReadWriter->get(stageId);
            if (stageRwId.id)
            {
                auto fabricId = iStageReadWriter->getFabricId(stageRwId);
                return iFabricUsd->getEnableChangeNotifies(fabricId);
            }
            else
            {
                return false;
            }
        }
        else
        {
            return false;
        }
    }

    void reset() override
    {
        std::vector<int> deletionKeys;
        auto deletionCallbacksMap = mUsdNoticeListener->getDeletionCallbacks();
        std::transform(deletionCallbacksMap.begin(), deletionCallbacksMap.end(), std::back_inserter(deletionKeys),
                       [](auto& p) { return p.first; });
        for (auto const& key : deletionKeys)
        {
            deletionCallbacksMap[key]("/");
        }
        mUsdNoticeListener->getDeletionCallbacks().clear();
        mUsdNoticeListener->getPhysicsSceneAdditionCallbacks().clear();
        mUsdNoticeListener->getPhysicsScenes().clear();
        int& callbackIter = mUsdNoticeListener->getCallbackIter();
        callbackIter = 0;
    }

private:
    UsdNoticeListener* mUsdNoticeListener = nullptr;
    pxr::TfNotice::Key mUsdNoticeListenerKey;
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
    }

    /**
     * Method called when the extension is disabled
     */
    void onShutdown() override
    {
    }
};

} // namespace isaacsim
} // namespace core
} // namespace simulation_manager

/**
 * Optional function (called the first time an interface is acquired from the plugin library)
 */
CARB_EXPORT void carbOnPluginStartup()
{
}

/**
 * Optional function (called right before the OS release the plugin library)
 */
CARB_EXPORT void carbOnPluginShutdown()
{
}

CARB_PLUGIN_IMPL(pluginImplDesc,
                 isaacsim::core::simulation_manager::SimulationManagerImpl,
                 isaacsim::core::simulation_manager::Extension)

void fillInterface(isaacsim::core::simulation_manager::SimulationManagerImpl& iface)
{
}

void fillInterface(isaacsim::core::simulation_manager::Extension& iface)
{
}
