// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRManager.h"
#include "plugins/bridge/BridgeApplication.h"

#include <boost/algorithm/string.hpp>
#include <carb/settings/ISettings.h>
#include <carb/tokens/ITokens.h>
#include <carb/tokens/TokensUtils.h>
#include <omni/usd/Layers.h>
#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/LayerUtils.h>
#include <omni/usd/UsdContext.h>
#include <DrSchema/baseComponent.h>
#include <DrSchema/colorComponent.h>
#include <DrSchema/lightComponent.h>
#include <DrSchema/movementComponent.h>
#include <DrSchema/rotationComponent.h>
#include <DrSchema/scaleComponent.h>
#include <DrSchema/textureComponent.h>
#include <DrSchema/materialComponent.h>
#include <DrSchema/meshComponent.h>
#include <DrSchema/visibilityComponent.h>

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
}

void DRManager::initialize(pxr::UsdStageWeakPtr stage, carb::tokens::ITokens* tokens)
{
    utils::BridgeApplicationBase<DRComponentBase<pxr::DrSchemaBaseComponent>>::initialize(stage);
    mTokens = tokens;
    mRootLayerIdentifier = mStage->GetRootLayer()->GetIdentifier();
    mDRLayerName = "";
    mNewSublayer = nullptr;
}

void removePrimSpecFromLayer(const std::string& layerIdentifier, const std::string& primPath)
{
    auto layerHandle = omni::usd::LayerUtils::findOrOpen(layerIdentifier);
    if (layerHandle)
    {
        const auto& primSpec = layerHandle->GetPrimAtPath(PXR_NS::SdfPath(primPath));
        if (primSpec)
        {
            auto parent = primSpec->GetRealNameParent();
            if (parent)
            {
                parent->RemoveNameChild(primSpec);
            }
        }
    }
}

void DRManager::tick(double dt)
{

    mTimeElapsed += dt;
    // CARB_LOG_WARN("Tick: %f - %f", mTimeElapsed, dt);

    if (mNewSublayer)
    {
        pxr::UsdEditContext context(mStage, mNewSublayer);
        for (auto& component : mComponents)
        {
            if (component.second->mDoStart == true)
            {
                component.second->onStart();
                component.second->mDoStart = false;
            }
        }

        for (auto& component : mComponents)
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
}

void DRManager::onComponentAdd(const pxr::UsdPrim& prim)
{
    if (!prim.IsA<pxr::DrSchemaBaseComponent>())
        return;

    std::string primPath = prim.GetPath().GetString();
    std::unique_ptr<DRComponentBase<pxr::DrSchemaBaseComponent>> component;
    if (mDRLayerName == "")
    {
        mLayer = omni::usd::UsdContext::getContext()->getLayers();
        const std::string layerPath = "";
        const std::string layerName = "DRLayer";
        size_t finalPosition;
        mNewSublayer = omni::usd::LayerUtils::createSublayer(
            mStage, mStage->GetSessionLayer(), 0, layerPath.c_str(), false, finalPosition);
        mDRLayerName = mNewSublayer->GetIdentifier();
        // omni::usd::LayerUtils::setCustomLayerName(mNewSublayer, mDRLayerName, pxr::TfToken(layerName.c_str()));
    }
    if (mComponents.find(primPath) != mComponents.end())
        return;

    if (prim.IsA<pxr::DrSchemaColorComponent>())
    {
        component = std::make_unique<DRComponentColor>(mTokens);
        component->initialize(pxr::DrSchemaColorComponent(prim), mStage);
    }
    else if (prim.IsA<pxr::DrSchemaTextureComponent>())
    {
        component = std::make_unique<DRComponentTexture>(mTokens);
        component->initialize(pxr::DrSchemaTextureComponent(prim), mStage);
    }
    else if (prim.IsA<pxr::DrSchemaMaterialComponent>())
    {
        component = std::make_unique<DRComponentMaterial>();
        component->initialize(pxr::DrSchemaMaterialComponent(prim), mStage);
    }
    else if (prim.IsA<pxr::DrSchemaMovementComponent>())
    {
        component = std::make_unique<DRComponentMovement>();
        component->initialize(pxr::DrSchemaMovementComponent(prim), mStage);
    }
    else if (prim.IsA<pxr::DrSchemaRotationComponent>())
    {
        component = std::make_unique<DRComponentRotation>();
        component->initialize(pxr::DrSchemaRotationComponent(prim), mStage);
    }
    else if (prim.IsA<pxr::DrSchemaScaleComponent>())
    {
        component = std::make_unique<DRComponentScale>();
        component->initialize(pxr::DrSchemaScaleComponent(prim), mStage);
    }
    else if (prim.IsA<pxr::DrSchemaLightComponent>())
    {
        component = std::make_unique<DRComponentLight>();
        component->initialize(pxr::DrSchemaLightComponent(prim), mStage);
    }
    else if (prim.IsA<pxr::DrSchemaMeshComponent>())
    {
        component = std::make_unique<DRComponentMesh>();
        component->initialize(pxr::DrSchemaMeshComponent(prim), mStage);
    }
    else if (prim.IsA<pxr::DrSchemaVisibilityComponent>())
    {
        component = std::make_unique<DRComponentVisibility>();
        component->initialize(pxr::DrSchemaVisibilityComponent(prim), mStage);
    }
    if (component)
    {
        component->mDRLayerName = mDRLayerName;
        mComponents[primPath] = std::move(component);
        CARB_LOG_INFO("Create: Prim %s", prim.GetPath().GetString().c_str());
    }
}

void DRManager::tickManual()
{

    if (mNewSublayer)
    {
        pxr::UsdEditContext context(mStage, mNewSublayer);
        for (auto& component : mComponents)
        {
            if (component.second->mDoStart == true)
            {
                component.second->onStart();
                component.second->mDoStart = false;
            }
        }

        for (auto& component : mComponents)
            if (component.second)
                component.second->tick();
    }
}

void DRManager::onStop()
{
    std::string authoringLayerId = omni::usd::LayerUtils::getAuthoringLayerIdentifier(mStage);
    auto authlayer = omni::usd::LayerUtils::findOrOpen(authoringLayerId);

    // Delete delta in the authoring layer
    auto primSpec = authlayer->GetPrimAtPath(pxr::SdfPath(mStage->GetDefaultPrim().GetPath().GetString() + "/DR"));
    if (primSpec)
    {
        removePrimSpecFromLayer(authoringLayerId, mStage->GetDefaultPrim().GetPath().GetString() + "/DR");
    }
}

}
}
}
