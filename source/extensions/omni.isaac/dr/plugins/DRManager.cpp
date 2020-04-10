// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRManager.h"

#include <boost/algorithm/string.hpp>
#include <carb/settings/ISettings.h>
#include <carb/tokens/ITokens.h>
#include <carb/tokens/TokensUtils.h>
#include <omni/usd/Layers.h>
#include <omni/usd/UsdContext.h>

namespace omni
{
namespace isaac
{
namespace dr
{

DRManager::DRManager()
{
}

DRManager::~DRManager()
{
    deleteAllComponents();
}

void DRManager::initialize(pxr::UsdStageRefPtr stage, carb::tokens::ITokens* tokens)
{
    utils::ComponentManager::initialize(stage);
    mTokens = tokens;
    mRootLayerIdentifier = mStage->GetRootLayer()->GetIdentifier();
    mNoticeListener = pxr::TfNotice::Register(pxr::TfCreateWeakPtr(this), &DRManager::handlePrimChanged);
}

void DRManager::tick(double dt)
{
    mTimeElapsed += dt;
    // CARB_LOG_WARN("Tick: %f - %f", mTimeElapsed, dt);
    if (mLayer && mRootLayerIdentifier.compare(mLayer->getAuthoringLayerIdentifier()) == 0)
        mLayer->setAuthoringLayerByIdentifier(mRootLayerIdentifier);

    if (mDoOnce == false)
    {
        loadComponentFromUsd();
        mDoOnce = true;
    }

    for (auto& component : mAllComponents)
    {
        if (component.second &&
            (component.second->mRandomizationDurationInterval == -1 ||
             ((mTimeElapsed - component.second->mLastTickTime) >= component.second->mRandomizationDurationInterval)))
        {
            component.second->mLastTickTime = mTimeElapsed;
            component.second->tick();
        }
    }
}

void DRManager::initComponents()
{
    // Empty
}

void DRManager::onComponentAdd(const pxr::UsdPrim& prim)
{
    if (std::find(mSupportedComponents.begin(), mSupportedComponents.end(), prim.GetTypeName()) ==
        mSupportedComponents.end())
        return;

    std::string primPath = prim.GetPath().GetString();
    std::unique_ptr<DRComponentBase> component;
    if (mDRLayerName == "")
    {
        mLayer = omni::usd::UsdContext::getContext()->getLayers();
        const std::string layerPath = "";
        const std::string layerName = "DRLayer";
        mDRLayerName = mLayer->addSublayer(mRootLayerIdentifier, 0, layerPath.c_str(), false, false, layerName.c_str());
        pxr::UsdEditTarget editTarget(mStage->GetRootLayer());
        mStage->SetEditTarget(editTarget);
    }
    if (mAllComponents.find(primPath) != mAllComponents.end())
        return;

    if (prim.GetTypeName() == "ColorComponent")
    {
        component = std::make_unique<DRComponentColor>(mTokens);
    }
    else if (prim.GetTypeName() == "TextureComponent")
    {
        component = std::make_unique<DRComponentTexture>();
    }
    else if (prim.GetTypeName() == "MovementComponent")
    {
        component = std::make_unique<DRComponentMovement>();
    }
    else if (prim.GetTypeName() == "RotationComponent")
    {
        component = std::make_unique<DRComponentRotation>();
    }
    else if (prim.GetTypeName() == "ScaleComponent")
    {
        component = std::make_unique<DRComponentScale>();
    }
    else if (prim.GetTypeName() == "LightComponent")
    {
        component = std::make_unique<DRComponentLight>();
    }
    component->initialize(prim, mStage);
    component->onComponentChange();
    component->onStart();
    mAllComponents[primPath] = std::move(component);
    CARB_LOG_WARN("Create: Prim %s", prim.GetPath().GetString().c_str());
}

void DRManager::onComponentChange(const pxr::UsdPrim& prim)
{
    if (std::find(mSupportedComponents.begin(), mSupportedComponents.end(), prim.GetTypeName()) ==
        mSupportedComponents.end())
        return;

    std::string primPath = prim.GetPath().GetString();
    if (prim.GetTypeName() == "ColorComponent")
    {
        mAllComponents[primPath]->onComponentChange();
    }
    else if (prim.GetTypeName() == "TextureComponent")
    {
        mAllComponents[primPath]->onComponentChange();
    }
    else if (prim.GetTypeName() == "MovementComponent")
    {
        mAllComponents[primPath]->onComponentChange();
    }
    else if (prim.GetTypeName() == "RotationComponent")
    {
        mAllComponents[primPath]->onComponentChange();
    }
    else if (prim.GetTypeName() == "ScaleComponent")
    {
        mAllComponents[primPath]->onComponentChange();
    }
    else if (prim.GetTypeName() == "LightComponent")
    {
        mAllComponents[primPath]->onComponentChange();
    }
}

void DRManager::onComponentRemove(const pxr::SdfPath& primPath)
{
    // delete component for this prim
    if (mAllComponents.find(primPath.GetString()) != mAllComponents.end())
    {
        CARB_LOG_WARN("Delete: Prim %s", primPath.GetString().c_str());
        mAllComponents[primPath.GetString()].reset();
        mAllComponents.erase(primPath.GetString());
    }
}

void DRManager::deleteAllComponents()
{
    for (auto& component : mAllComponents)
    {
        if (component.second)
        {
            component.second.reset();
        }
    }
    mAllComponents.clear();
    mDoOnce = false;
}

void DRManager::loadComponentFromUsd()
{
    pxr::UsdPrimRange range = mStage->Traverse();
    for (pxr::UsdPrimRange::iterator iter = range.begin(); iter != range.end(); ++iter)
    {
        pxr::UsdPrim childPrim = *iter;
        onComponentAdd(childPrim);
        onComponentChange(childPrim);
    }
}

void DRManager::handlePrimChanged(const class pxr::UsdNotice::ObjectsChanged& objectsChanged)
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
                // CARB_LOG_WARN("Removing: %s", primPath.GetString().c_str());
                onComponentRemove(primPath);
            }
        }
    }
}

}
}
}
