// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

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
#include <drSchema/baseComponent.h>
#include <drSchema/colorComponent.h>
#include <drSchema/lightComponent.h>
#include <drSchema/movementComponent.h>
#include <drSchema/rotationComponent.h>
#include <drSchema/scaleComponent.h>
#include <drSchema/transformComponent.h>
#include <drSchema/textureComponent.h>
#include <drSchema/materialComponent.h>
#include <drSchema/meshComponent.h>
#include <drSchema/visibilityComponent.h>
#include <drSchema/attributeComponent.h>

namespace omni
{
namespace isaac
{
namespace dr
{

DRManager::DRManager(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
{
    mDynamicControlPtr = dynamicControlPtr;
}

DRManager::~DRManager()
{
}

void DRManager::initialize(pxr::UsdStageWeakPtr stage, carb::tokens::ITokens* tokens, omni::renderer::IDebugDraw* debugDraw)
{
    utils::BridgeApplicationBase<DRComponentBase<pxr::DrSchemaBaseComponent>>::initialize(stage);
    mTokens = tokens;
    mDebugDrawPtr = debugDraw;
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
    // CARB_LOG_WARN("Tick: %lf - %lf", mTimeElapsed, dt);

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
    if (!(prim.GetTypeName().GetString() == "ColorComponent") && !(prim.GetTypeName().GetString() == "TextureComponent") &&
        !(prim.GetTypeName().GetString() == "MaterialComponent") &&
        !(prim.GetTypeName().GetString() == "MovementComponent") &&
        !(prim.GetTypeName().GetString() == "RotationComponent") &&
        !(prim.GetTypeName().GetString() == "ScaleComponent") &&
        !(prim.GetTypeName().GetString() == "TransformComponent") &&
        !(prim.GetTypeName().GetString() == "LightComponent") && !(prim.GetTypeName().GetString() == "MeshComponent") &&
        !(prim.GetTypeName().GetString() == "VisibilityComponent") &&
        !(prim.GetTypeName().GetString() == "AttributeComponent"))
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

    if (prim.GetTypeName().GetString() == "ColorComponent")
    {
        component = std::make_unique<DRComponentColor>(mTokens);
        component->initialize(pxr::DrSchemaColorComponent(prim), mStage);
    }
    else if (prim.GetTypeName().GetString() == "TextureComponent")
    {
        component = std::make_unique<DRComponentTexture>(mTokens);
        component->initialize(pxr::DrSchemaTextureComponent(prim), mStage);
    }
    else if (prim.GetTypeName().GetString() == "MaterialComponent")
    {
        component = std::make_unique<DRComponentMaterial>();
        component->initialize(pxr::DrSchemaMaterialComponent(prim), mStage);
    }
    else if (prim.GetTypeName().GetString() == "MovementComponent")
    {
        component = std::make_unique<DRComponentMovement>(mDynamicControlPtr, mDebugDrawPtr);
        component->initialize(pxr::DrSchemaMovementComponent(prim), mStage);
    }
    else if (prim.GetTypeName().GetString() == "RotationComponent")
    {
        component = std::make_unique<DRComponentRotation>();
        component->initialize(pxr::DrSchemaRotationComponent(prim), mStage);
    }
    else if (prim.GetTypeName().GetString() == "ScaleComponent")
    {
        component = std::make_unique<DRComponentScale>();
        component->initialize(pxr::DrSchemaScaleComponent(prim), mStage);
    }
    else if (prim.GetTypeName().GetString() == "TransformComponent")
    {
        component = std::make_unique<DRComponentTransform>(mDynamicControlPtr, mDebugDrawPtr);
        component->initialize(pxr::DrSchemaTransformComponent(prim), mStage);
    }
    else if (prim.GetTypeName().GetString() == "LightComponent")
    {
        component = std::make_unique<DRComponentLight>();
        component->initialize(pxr::DrSchemaLightComponent(prim), mStage);
    }
    else if (prim.GetTypeName().GetString() == "MeshComponent")
    {
        component = std::make_unique<DRComponentMesh>();
        component->initialize(pxr::DrSchemaMeshComponent(prim), mStage);
    }
    else if (prim.GetTypeName().GetString() == "VisibilityComponent")
    {
        component = std::make_unique<DRComponentVisibility>();
        component->initialize(pxr::DrSchemaVisibilityComponent(prim), mStage);
    }
    else if (prim.GetTypeName().GetString() == "AttributeComponent")
    {
        component = std::make_unique<DRComponentAttribute>();
        component->initialize(pxr::DrSchemaAttributeComponent(prim), mStage);
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
