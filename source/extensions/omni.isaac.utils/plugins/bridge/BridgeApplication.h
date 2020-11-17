// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../core/Component.h"
#include "../core/ComponentManager.h"

#include <omni/usd/UtilsIncludes.h>
//
#include <omni/usd/UsdUtils.h>

#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace omni
{
namespace isaac
{
namespace utils
{

// This custom Usd notice listener is required to clean up properly
class UsdNoticeListener : public omni::usd::UsdUtils::UsdNoticeListener<pxr::UsdNotice::ObjectsChanged>

{
public:
    UsdNoticeListener(ComponentManager* manager) : mManager(manager)
    {
        mStage = mManager->getStage();
    }

    virtual void handleNotice(const pxr::UsdNotice::ObjectsChanged& objectsChanged) override
    {
        if (mStage != objectsChanged.GetStage())
        {
            return;
        }

        for (auto& path : objectsChanged.GetResyncedPaths())
        {
            if (path.IsAbsoluteRootOrPrimPath())
            {
                // CARB_LOG_WARN("ResyncedPaths: %s", path.GetText());
                auto primPath =
                    mStage->GetPseudoRoot().GetPath() == path ? mStage->GetPseudoRoot().GetPath() : path.GetPrimPath();

                // If prim is removed, remove it and its descendants from selection.
                pxr::UsdPrim prim = mStage->GetPrimAtPath(primPath);

                // CARB_LOG_WARN("Prim valid %d", prim.IsValid());
                if (prim.IsValid() == false) // remove prim
                {
                    mManager->onComponentRemove(primPath);
                }
            }
        }
        for (auto& path : objectsChanged.GetChangedInfoOnlyPaths())
        {
            auto primPath =
                mStage->GetPseudoRoot().GetPath() == path ? mStage->GetPseudoRoot().GetPath() : path.GetPrimPath();

            // Update the component attached to this prim, onComponentChange checks to see if the prim exists in
            // this BridgeApplication
            pxr::UsdPrim prim = mStage->GetPrimAtPath(primPath);
            mManager->onComponentChange(prim);
        }
    }

private:
    pxr::UsdStageWeakPtr mStage = nullptr;
    ComponentManager* mManager = nullptr;
};


template <class ComponentType>
class BridgeApplicationBase : public ComponentManager, public pxr::TfWeakBase
{
public:
    /**
     * @brief Construct a new Application object
     *
     */
    BridgeApplicationBase()
    {
    }

    /**
     * @brief Destroy the Isaac Application object
     *
     */

    ~BridgeApplicationBase()
    {
        mNoticeListener->revokeListener();
        deleteAllComponents();
    }

    /**
     * @brief Set the USD stage for this application
     *
     * @param stage
     */
    virtual void initialize(pxr::UsdStageWeakPtr stage)
    {
        mStage = stage;
        mNoticeListener = std::make_unique<UsdNoticeListener>(this);
        mNoticeListener->registerListener();
    }

    /**
     * @brief Tick the application and all components
     * Pure virtual, must be defined by the child class
     * @param dt
     */
    virtual void tick(double dt) = 0;

    /**
     * @brief Initialize components from the current stage
     *
     */
    virtual void initComponents()
    {
        pxr::UsdPrimRange range = mStage->Traverse();

        for (pxr::UsdPrimRange::iterator iter = range.begin(); iter != range.end(); ++iter)
        {
            pxr::UsdPrim prim = *iter;
            onComponentAdd(prim);
        }
    }


    /**
     * @brief Create a supported component in this application
     * Pure virtual, must be defined by the child class
     * @param prim
     */
    virtual void onComponentAdd(const pxr::UsdPrim& prim) = 0;

    /**
     * @brief Update properties of this prim (onComponentChange)
     *
     * @param prim
     */
    virtual void onComponentChange(const pxr::UsdPrim& prim)
    {
        // update properties of this prim (onComponentChange)
        if (mComponents.find(prim.GetPath().GetString()) != mComponents.end())
        {
            mComponents[prim.GetPath().GetString()]->onComponentChange();
        }
    }

    /**
     * @brief Delete component
     *
     * @param prim
     */
    virtual void onComponentRemove(const pxr::SdfPath& primPath)
    {
        // delete component for this prim
        if (mComponents.find(primPath.GetString()) != mComponents.end())
        {
            // CARB_LOG_WARN("Delete: Prim %s", primPath.GetString().c_str());
            mComponents[primPath.GetString()].reset();
            mComponents.erase(primPath.GetString());
        }
    }

    /** Remove all components and perform cleanup
     * @brief
     *
     */
    virtual void deleteAllComponents()
    {
        for (auto& component : mComponents)
        {
            component.second.reset();
        }
        mComponents.clear();
    }

protected:
    std::unordered_map<std::string, std::unique_ptr<ComponentType>> mComponents;
    std::unique_ptr<UsdNoticeListener> mNoticeListener;
};

typedef BridgeApplicationBase<Component> BridgeApplication;


}
}
}
