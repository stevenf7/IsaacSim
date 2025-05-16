// SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#include <carb/PluginUtils.h>
#include <carb/events/EventsUtils.h>

#include <isaacsim/core/simulation_manager/ISimulationManager.h>
#include <isaacsim/core/simulation_manager/UsdNoticeListener.h>
#include <omni/ext/IExt.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/fabric/stage/StageReaderWriter.h>
#include <omni/kit/IMinimal.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/physx/IPhysx.h>

#include <algorithm>

/**
 * @brief Plugin descriptor for the simulation manager plugin.
 * @details Defines the plugin's name, description, author, hot reload capability, and version.
 */
const struct carb::PluginImplDesc g_kPluginDesc = { "isaacsim.core.simulation_manager.plugin",
                                                    "Helpful text describing the plugin", "Author",
                                                    carb::PluginHotReload::eEnabled, "dev" };

namespace
{
omni::physx::IPhysx* g_physXInterface = nullptr;
omni::physx::SubscriptionId g_physicsOnStepSubscription;
carb::events::ISubscriptionPtr g_physicsEventSubscription;
omni::kit::StageUpdatePtr g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
double g_simulationTime = 0.0;
double g_simulationTimeMonotonic = 0.0;
double g_systemTime = 0.0;
size_t g_numPhysicsSteps = 0;
bool g_simulating = false;
bool g_paused = false;
}

namespace isaacsim
{
namespace core
{
namespace simulation_manager
{

/**
 * @class SimulationManagerImpl
 * @brief Implementation of the ISimulationManager interface.
 * @details
 * Provides functionality for managing simulation-related events and callbacks.
 * Handles USD notices and maintains callback registrations for physics scene additions
 * and deletion events.
 */
class SimulationManagerImpl : public ISimulationManager
{
public:
    /**
     * @brief Constructor for SimulationManagerImpl.
     * @details
     * Initializes the USD notice listener and registers it to handle USD notices.
     */
    SimulationManagerImpl()
    {
        m_usdNoticeListener = new UsdNoticeListener();
        m_usdNoticeListenerKey =
            pxr::TfNotice::Register(pxr::TfCreateWeakPtr(m_usdNoticeListener), &UsdNoticeListener::handle);
    }

    /**
     * @brief Destructor for SimulationManagerImpl.
     * @details
     * Cleans up the USD notice listener.
     */
    ~SimulationManagerImpl()
    {
        delete m_usdNoticeListener;
    }

    /**
     * @brief Registers a callback function to be called when an object is deleted.
     * @details
     * The callback will be invoked with the path of the deleted object as a parameter.
     *
     * @param[in] callback Function to be called when an object is deleted.
     * @return Unique identifier for the registered callback.
     */
    int registerDeletionCallback(const std::function<void(std::string)>& callback) override
    {
        int& callbackIter = m_usdNoticeListener->getCallbackIter();
        m_usdNoticeListener->getDeletionCallbacks().emplace(callbackIter, callback);
        callbackIter += 1;
        return callbackIter - 1;
    }

    /**
     * @brief Registers a callback function to be called when a physics scene is added.
     * @details
     * The callback will be invoked with the path of the added physics scene as a parameter.
     *
     * @param[in] callback Function to be called when a physics scene is added.
     * @return Unique identifier for the registered callback.
     */
    int registerPhysicsSceneAdditionCallback(const std::function<void(std::string)>& callback) override
    {
        int& callbackIter = m_usdNoticeListener->getCallbackIter();
        m_usdNoticeListener->getPhysicsSceneAdditionCallbacks().emplace(callbackIter, callback);
        callbackIter += 1;
        return callbackIter - 1;
    }

    /**
     * @brief Deregisters a previously registered callback.
     * @details
     * Removes a callback from either the physics scene addition callbacks or deletion callbacks
     * based on the provided callback ID.
     *
     * @param[in] callbackId The unique identifier of the callback to deregister.
     * @return True if the callback was successfully deregistered, false otherwise.
     */
    bool deregisterCallback(const int& callbackId) override
    {
        std::map<int, std::function<void(const std::string&)>>& physicsSceneCallbacks =
            m_usdNoticeListener->getPhysicsSceneAdditionCallbacks();
        std::map<int, std::function<void(const std::string&)>>& deletiomCallbacks =
            m_usdNoticeListener->getDeletionCallbacks();
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

    /**
     * @brief Gets the current callback iterator value.
     * @details
     * This value is used to generate unique identifiers for callbacks.
     *
     * @return Reference to the current callback iterator.
     */
    int& getCallbackIter() override
    {
        return m_usdNoticeListener->getCallbackIter();
    }

    /**
     * @brief Sets the callback iterator to a specific value.
     * @details
     * Allows manual control over the callback identifier generation.
     *
     * @param[in] val The value to set the callback iterator to.
     */
    void setCallbackIter(int const& val) override
    {
        int& callbackIter = m_usdNoticeListener->getCallbackIter();
        callbackIter = val;
    }

    /**
     * @brief Gets the current simulation time.
     * @details
     * Returns the current simulation time.
     *
     * @return The current simulation time.
     */
    double getSimulationTime() override
    {
        return g_simulationTime;
    }

    /**
     * @brief Enables or disables the USD notice handler.
     * @details
     * Controls whether USD notices are processed by the notice listener.
     *
     * @param[in] flag True to enable the handler, false to disable it.
     */
    void enableUsdNoticeHandler(bool const& flag) override
    {
        m_usdNoticeListener->enable(flag);
    }

    /**
     * @brief Enables or disables the Fabric USD notice handler for a specific stage.
     * @details
     * Controls whether Fabric USD notices are processed for the specified stage.
     * If enabled, forces a minimal populate of the Fabric USD.
     *
     * @param[in] stageId The ID of the stage to configure.
     * @param[in] flag True to enable the handler, false to disable it.
     */
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

    /**
     * @brief Checks if the Fabric USD notice handler is enabled for a specific stage.
     * @details
     * Determines whether Fabric USD notices are being processed for the specified stage.
     *
     * @param[in] stageId The ID of the stage to check.
     * @return True if the notice handler is enabled, false otherwise.
     */
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

    /**
     * @brief Gets the current physics step count.
     * @details
     * Returns the current physics step count.
     *
     * @return The current physics step count.
     */
    size_t getNumPhysicsSteps() override
    {
        return g_numPhysicsSteps;
    }

    /**
     * @brief Gets the current simulation pause state.
     * @details
     * Returns the current simulation pause state.
     *
     * @return The current simulation pause state.
     */
    bool isSimulating() override
    {
        return g_simulating;
    }

    /**
     * @brief Gets the current simulation pause state.
     * @details
     * Returns the current simulation pause state.
     *
     * @return The current simulation pause state.
     */
    bool isPaused() override
    {
        return g_paused;
    }


    /**
     * @brief Resets the simulation manager.
     * @details
     * Calls all registered deletion callbacks with a root path ("/"),
     * clears all registered callbacks, clears the physics scenes list,
     * and resets the callback iterator to 0.
     */
    void reset() override
    {
        std::vector<int> deletionKeys;
        auto deletionCallbacksMap = m_usdNoticeListener->getDeletionCallbacks();
        std::transform(deletionCallbacksMap.begin(), deletionCallbacksMap.end(), std::back_inserter(deletionKeys),
                       [](auto& p) { return p.first; });
        for (auto const& key : deletionKeys)
        {
            deletionCallbacksMap[key]("/");
        }
        m_usdNoticeListener->getDeletionCallbacks().clear();
        m_usdNoticeListener->getPhysicsSceneAdditionCallbacks().clear();
        m_usdNoticeListener->getPhysicsScenes().clear();
        int& callbackIter = m_usdNoticeListener->getCallbackIter();
        callbackIter = 0;
    }

private:
    /**
     * @brief USD notice listener object that handles USD notices.
     */
    UsdNoticeListener* m_usdNoticeListener = nullptr;

    /**
     * @brief Key for the registered USD notice listener.
     */
    pxr::TfNotice::Key m_usdNoticeListenerKey;
};

/**
 * @brief Callback function for physics step events.
 * @details
 * Updates the simulation time and physics step count.
 *
 * @param[in] timeElapsed The elapsed time since the last physics step.
 */
void onPhysicsStep(float timeElapsed, void* userData)
{
    g_simulationTime += timeElapsed;
    g_simulationTimeMonotonic += timeElapsed;
    g_numPhysicsSteps += 1;
    g_systemTime = std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();
    g_simulating = true;
}
/**
 * @brief Callback function for stop events.
 * @details
 * Resets the simulation time and physics step count.
 *
 * @param[in] userData User data pointer.
 */
void onStop(void* userData)
{
    g_simulationTime = 0;
    g_numPhysicsSteps = 0;
}

/**
 * @brief Callback function for stage attach events.
 * @details
 * Resets the simulation time and physics step count.
 *
 * @param[in] stageId The ID of the stage.
 */
void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    g_simulationTime = 0;
    g_numPhysicsSteps = 0;
}

/**
 * @class Extension
 * @brief Implementation of the IExt interface for the simulation manager extension.
 * @details
 * Provides lifecycle management for the simulation manager extension.
 */
class Extension : public omni::ext::IExt
{
public:
    /**
     * @brief Method called when the extension is loaded/enabled.
     * @details
     * Initializes the extension when it is loaded.
     *
     * @param[in] extId The ID of the extension being loaded.
     */
    void onStartup(const char* extId) override
    {
        // TODO: in case there is more than one physics scene which one is returned?
        g_physXInterface = carb::getCachedInterface<omni::physx::IPhysx>();
        g_physicsOnStepSubscription = g_physXInterface->subscribePhysicsOnStepEvents(false, 0, onPhysicsStep, nullptr);
        g_systemTime = std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();

        g_physicsEventSubscription = carb::events::createSubscriptionToPop(
            g_physXInterface->getSimulationEventStreamV2().get(),
            [](carb::events::IEvent* e)
            {
                if (e->type == omni::physx::SimulationEvent::eStopped)
                {
                    g_simulating = false;
                    g_paused = false;
                }
                else if (e->type == omni::physx::SimulationEvent::ePaused)
                {
                    g_paused = true;
                }
                else if (e->type == omni::physx::SimulationEvent::eResumed)
                {
                    g_simulating = true;
                    g_paused = false;
                }
            },
            0, "IsaacSim.Core.SimulationManager.SimulationEvent");

        g_stageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>()->getStageUpdate();
        omni::kit::StageUpdateNodeDesc desc = { 0 };
        desc.displayName = "Isaac Simulation Manager";
        desc.onStop = onStop;
        desc.onAttach = onAttach;
        g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);
    }

    /**
     * @brief Method called when the extension is disabled.
     * @details
     * Cleans up the extension when it is disabled.
     */
    void onShutdown() override
    {
    }
};

} // namespace isaacsim
} // namespace core
} // namespace simulation_manager

/**
 * @brief Optional function called the first time an interface is acquired from the plugin library.
 * @details
 * This function is invoked by the Carbonite framework when the plugin is first loaded.
 */
CARB_EXPORT void carbOnPluginStartup()
{
}

/**
 * @brief Optional function called right before the OS releases the plugin library.
 * @details
 * This function is invoked by the Carbonite framework when the plugin is about to be unloaded.
 */
CARB_EXPORT void carbOnPluginShutdown()
{
}

/**
 * @brief Implements the plugin with the specified simulation manager and extension implementations.
 * @details
 * Registers the plugin with the Carbonite framework.
 */
CARB_PLUGIN_IMPL(g_kPluginDesc,
                 isaacsim::core::simulation_manager::SimulationManagerImpl,
                 isaacsim::core::simulation_manager::Extension)

/**
 * @brief Fills the interface for the simulation manager implementation.
 * @details
 * This function is called by the Carbonite framework to initialize the interface.
 *
 * @param[in,out] iface The interface to fill.
 */
void fillInterface(isaacsim::core::simulation_manager::SimulationManagerImpl& iface)
{
}

/**
 * @brief Fills the interface for the extension implementation.
 * @details
 * This function is called by the Carbonite framework to initialize the interface.
 *
 * @param[in,out] iface The interface to fill.
 */
void fillInterface(isaacsim::core::simulation_manager::Extension& iface)
{
}
