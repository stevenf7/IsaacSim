// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "Component.h"
#include "ComponentManager.h"

#include <omni/usd/UtilsIncludes.h>
//
#include <omni/fabric/usd/PathConversion.h>
#include <omni/usd/UsdUtils.h>

#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace isaacsim
{
namespace core
{
namespace includes
{

/**
 * @class UsdNoticeListener
 * @brief Custom USD notice listener for handling object changes in the stage
 * @details
 * Implements a specialized listener for USD object change notifications, specifically handling
 * prim additions, removals, and modifications. This listener is essential for maintaining
 * synchronization between the USD stage and component management system.
 */
class UsdNoticeListener : public omni::usd::UsdUtils::UsdNoticeListener<pxr::UsdNotice::ObjectsChanged>
{
public:
    /**
     * @brief Constructs a new USD notice listener
     * @param[in] manager Pointer to the component manager that will handle notifications
     */
    UsdNoticeListener(ComponentManager* manager) : m_manager(manager)
    {
        m_stage = m_manager->getStage();
    }

    /**
     * @brief Handles USD object change notifications
     * @details
     * Processes notifications about changes to USD objects, including prim additions,
     * removals, and modifications. Triggers appropriate component manager callbacks.
     *
     * @param[in] objectsChanged The notification containing information about changed objects
     */
    virtual void handleNotice(const pxr::UsdNotice::ObjectsChanged& objectsChanged) override
    {
        if (m_stage != objectsChanged.GetStage())
        {
            return;
        }

        for (auto& path : objectsChanged.GetResyncedPaths())
        {
            if (path.IsAbsoluteRootOrPrimPath())
            {
                // CARB_LOG_WARN("ResyncedPaths: %s", path.GetText());
                const auto& primPath = (path == PXR_NS::SdfPath::AbsoluteRootPath() ? path : path.GetPrimPath());

                // If prim is removed, remove it and its descendants from selection.
                pxr::UsdPrim prim = m_stage->GetPrimAtPath(primPath);

                // CARB_LOG_INFO("Prim %s valid %d", primPath.GetString().c_str(), prim.IsValid());
                if (prim.IsValid() == false) // removed prim
                {
                    m_manager->onComponentRemove(primPath);
                }
            }
        }
        for (auto& path : objectsChanged.GetChangedInfoOnlyPaths())
        {
            auto primPath =
                m_stage->GetPseudoRoot().GetPath() == path ? m_stage->GetPseudoRoot().GetPath() : path.GetPrimPath();

            // Update the component attached to this prim, onComponentChange checks to see if the prim exists in
            // this BridgeApplication
            pxr::UsdPrim prim = m_stage->GetPrimAtPath(primPath);
            m_manager->onComponentChange(prim);
        }
    }

private:
    /** @brief Weak pointer to the USD stage being monitored */
    pxr::UsdStageWeakPtr m_stage = nullptr;

    /** @brief Pointer to the component manager handling notifications */
    ComponentManager* m_manager = nullptr;
};

/**
 * @class BridgeApplicationBase
 * @brief Base template class for bridge applications managing USD-based components
 * @details
 * Provides core functionality for managing components within a USD stage, including
 * component lifecycle management, event handling, and synchronization with USD changes.
 * This class serves as a bridge between the USD stage and component-based application logic.
 *
 * @tparam ComponentType The base component type managed by this application
 *
 * @note This class inherits from ComponentManager and pxr::TfWeakBase
 * @warning Derived classes must implement pure virtual functions
 */
template <class ComponentType>
class BridgeApplicationBase : public ComponentManager, public pxr::TfWeakBase
{
public:
    /**
     * @brief Constructs a new BridgeApplicationBase instance
     */
    BridgeApplicationBase() = default;

    /**
     * @brief Destroys the application instance and cleans up resources
     * @details Releases the notice listener and deletes all managed components
     */
    ~BridgeApplicationBase()
    {
        m_noticeListener.reset();
        deleteAllComponents();
    }

    /**
     * @brief Initializes the application with a USD stage
     * @details Sets up the stage reference and creates the notice listener
     *
     * @param[in] stage Weak pointer to the USD stage to be managed
     * @post Application is initialized with the stage and notice listener
     */
    virtual void initialize(pxr::UsdStageWeakPtr stage)
    {
        m_stage = stage;
        m_noticeListener = std::make_unique<UsdNoticeListener>(this);
        m_noticeListener->registerListener();
    }

    /**
     * @brief Updates the application and all components
     * @details Pure virtual function that must be implemented by derived classes
     *
     * @param[in] dt Time step in seconds since the last tick
     */
    virtual void tick(double dt) = 0;

    /**
     * @brief Initializes components from the current stage
     * @details
     * Scans the USD stage for prims matching component types and creates
     * corresponding components. Uses the USD runtime API for efficient traversal.
     */
    virtual void initComponents()
    {
        PXR_NS::UsdStageCache& cache = PXR_NS::UsdUtilsStageCache::Get();
        omni::fabric::UsdStageId stageId = { static_cast<uint64_t>(cache.GetId(m_stage).ToLongInt()) };
        omni::fabric::IStageReaderWriter* iStageReaderWriter =
            carb::getCachedInterface<omni::fabric::IStageReaderWriter>();
        omni::fabric::StageReaderWriterId stageInProgress = iStageReaderWriter->get(stageId);
        usdrt::UsdStageRefPtr usdrtStage = usdrt::UsdStage::Attach(stageId, stageInProgress);

        const std::vector<std::string> componentIsAVector = getComponentIsAVector();
        for (const std::string& componentIsA : componentIsAVector)
        {
            const std::vector<usdrt::SdfPath> componentPaths =
                usdrtStage->GetPrimsWithTypeName(usdrt::TfToken(componentIsA));

            for (const usdrt::SdfPath& usdrtPath : componentPaths)
            {
                const omni::fabric::PathC pathC(usdrtPath);
                const pxr::SdfPath usdPath = omni::fabric::toSdfPath(pathC);
                pxr::UsdPrim prim = m_stage->GetPrimAtPath(usdPath);

                onComponentAdd(prim);
            }
        }
    }

    /**
     * @brief Gets the list of component type names to search for in the stage
     * @return Vector of strings containing component type names
     */
    virtual std::vector<std::string> getComponentIsAVector() const = 0;

    /**
     * @brief Creates a new component for the given prim
     * @details Pure virtual function that must be implemented by derived classes
     *
     * @param[in] prim The USD prim to create a component for
     */
    virtual void onComponentAdd(const pxr::UsdPrim& prim) = 0;

    /**
     * @brief Updates a component when its corresponding prim changes
     * @details Triggers the component's change handler if it exists
     *
     * @param[in] prim The USD prim that changed
     */
    virtual void onComponentChange(const pxr::UsdPrim& prim)
    {
        // update properties of this prim (onComponentChange)
        if (m_components.find(prim.GetPath().GetString()) != m_components.end())
        {
            m_components[prim.GetPath().GetString()]->onComponentChange();
        }
    }

    /**
     * @brief Updates components during physics simulation steps
     * @details Override this to implement physics-specific component updates
     *
     * @param[in] dt Physics time step in seconds
     */
    virtual void onPhysicsStep(float dt)
    {
    }

    /**
     * @brief Removes components associated with a prim and its descendants
     * @details
     * Safely removes components when their corresponding prims are deleted from the stage.
     * Uses a mutex to ensure thread-safe component removal.
     *
     * @param[in] primPath Path to the prim being removed
     * @thread_safety This method is thread-safe
     */
    virtual void onComponentRemove(const pxr::SdfPath& primPath)
    {
        std::unique_lock<std::mutex> lck(m_componentMtx);
        // Delete component for any children of this prim
        for (auto it = m_components.begin(); it != m_components.end();)
        {
            // CARB_LOG_WARN("Check: Prim %s %s", primPath.GetString().c_str(), it->first.c_str());
            // if ((it->first).find(primPath.GetString()) != std::string::npos)
            if (pxr::SdfPath(it->first).HasPrefix(primPath))
            {
                CARB_LOG_INFO("Delete: Prim %s %s", primPath.GetString().c_str(), it->first.c_str());
                it->second.reset();
                it = m_components.erase(it);
            }
            else
            {
                it++;
            }
        }
    }

    /**
     * @brief Removes all components and performs cleanup
     * @details
     * Thread-safe method to remove all components and release their resources
     *
     * @thread_safety This method is thread-safe
     */
    virtual void deleteAllComponents()
    {
        std::unique_lock<std::mutex> lck(m_componentMtx);
        for (auto& component : m_components)
        {
            component.second.reset();
        }
        m_components.clear();
    }

protected:
    /** @brief Map of component paths to their corresponding component instances */
    std::unordered_map<std::string, std::unique_ptr<ComponentType>> m_components;

    /** @brief USD notice listener for stage changes */
    std::unique_ptr<UsdNoticeListener> m_noticeListener;

    /** @brief Mutex for thread-safe component operations */
    std::mutex m_componentMtx;
};

/**
 * @typedef BridgeApplication
 * @brief Convenience typedef for BridgeApplicationBase specialized with the base Component type
 */
typedef BridgeApplicationBase<Component> BridgeApplication;

}
}
}
