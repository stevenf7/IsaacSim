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


DRManager::DRManager(pxr::UsdStageWeakPtr stage, carb::tokens::ITokens* tokens)
{
    mStage = stage;
    mTokens = tokens;
    mRootLayerIdentifier = mStage->GetRootLayer()->GetIdentifier();
}

DRManager::~DRManager()
{
    deleteAllComponents();
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

void DRManager::onComponentAdd(const pxr::UsdPrim& prim)
{
    if (std::find(mSupportedComponents.begin(), mSupportedComponents.end(), prim.GetTypeName()) ==
        mSupportedComponents.end())
        return;

    std::string compName;
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
    prim.GetAttribute(pxr::TfToken("compName")).Get(&compName);
    if (mComponentMap.find(compName) != mComponentMap.end())
        return;

    if (prim.GetTypeName() == "ColorComponent")
    {
        component = std::make_unique<DRComponentColor>(mTokens);
        component->initialize(prim, mStage);
        component->onComponentChange();
        component->onStart();
        mAllComponents.push_back(std::move(component));
        mComponentMap[compName] = (int)mAllComponents.size() - 1;
        CARB_LOG_WARN("Component ID %d of type Color Created", (int)mAllComponents.size() - 1);
    }
    else if (prim.GetTypeName() == "TextureComponent")
    {
        component = std::make_unique<DRComponentTexture>();
        component->initialize(prim, mStage);
        component->onComponentChange();
        component->onStart();
        mAllComponents.push_back(std::move(component));
        mComponentMap[compName] = (int)mAllComponents.size() - 1;
        CARB_LOG_WARN("Component ID %d of type Texture Created", (int)mAllComponents.size() - 1);
    }
    else if (prim.GetTypeName() == "MovementComponent")
    {
        component = std::make_unique<DRComponentMovement>();
        component->initialize(prim, mStage);
        component->onComponentChange();
        component->onStart();
        mAllComponents.push_back(std::move(component));
        mComponentMap[compName] = (int)mAllComponents.size() - 1;
        CARB_LOG_WARN("Component ID %d of type Movement Created", (int)mAllComponents.size() - 1);
    }
    else if (prim.GetTypeName() == "ScaleComponent")
    {
        component = std::make_unique<DRComponentScale>();
        component->initialize(prim, mStage);
        component->onComponentChange();
        component->onStart();
        mAllComponents.push_back(std::move(component));
        mComponentMap[compName] = (int)mAllComponents.size() - 1;
        CARB_LOG_WARN("Component ID %d of type Scale Created", (int)mAllComponents.size() - 1);
    }
    else if (prim.GetTypeName() == "LightComponent")
    {
        component = std::make_unique<DRComponentLight>();
        component->initialize(prim, mStage);
        component->onComponentChange();
        component->onStart();
        mAllComponents.push_back(std::move(component));
        mComponentMap[compName] = (int)mAllComponents.size() - 1;
        CARB_LOG_WARN("Component ID %d of type Light Created", (int)mAllComponents.size() - 1);
    }
}

void DRManager::onComponentChange(const pxr::UsdPrim& prim)
{
    if (std::find(mSupportedComponents.begin(), mSupportedComponents.end(), prim.GetTypeName()) ==
        mSupportedComponents.end())
        return;

    std::string compName;
    prim.GetAttribute(pxr::TfToken("compName")).Get(&compName);
    if (prim.GetTypeName() == "ColorComponent")
    {
        mAllComponents[mComponentMap[compName]]->onComponentChange();
    }
    else if (prim.GetTypeName() == "TextureComponent")
    {
        mAllComponents[mComponentMap[compName]]->onComponentChange();
    }
    else if (prim.GetTypeName() == "MovementComponent")
    {
        mAllComponents[mComponentMap[compName]]->onComponentChange();
    }
    else if (prim.GetTypeName() == "ScaleComponent")
    {
        mAllComponents[mComponentMap[compName]]->onComponentChange();
    }
    else if (prim.GetTypeName() == "LightComponent")
    {
        mAllComponents[mComponentMap[compName]]->onComponentChange();
    }
}

void DRManager::deleteAllComponents()
{
    for (auto& component : mAllComponents)
    {
        if (component)
        {
            component.reset();
        }
    }
    mAllComponents.clear();
    mDoOnce = false;
}

void DRManager::tick(const float dt)
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
        if (component && (component->mRandomizationDurationInterval == -1 ||
                          ((mTimeElapsed - component->mLastTickTime) >= component->mRandomizationDurationInterval)))
        {
            component->mLastTickTime = mTimeElapsed;
            component->tick(dt);
        }
    }
}
}
}
}
