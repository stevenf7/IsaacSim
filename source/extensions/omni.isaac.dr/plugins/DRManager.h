// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "DRComponentAttribute.h"
#include "DRComponentBase.h"
#include "DRComponentColor.h"
#include "DRComponentLight.h"
#include "DRComponentMaterial.h"
#include "DRComponentMesh.h"
#include "DRComponentMovement.h"
#include "DRComponentRotation.h"
#include "DRComponentScale.h"
#include "DRComponentTexture.h"
#include "DRComponentTransform.h"
#include "DRComponentVisibility.h"
#include "omni/isaac/bridge/BridgeApplication.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/logging/Log.h>
#include <carb/tokens/ITokens.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/renderer/IDebugDraw.h>

// clang-format off
#include <omni/usd/UsdContextIncludes.h>
#include <omni/usd/Layers.h>
// clang-format on

#include <functional>
#include <string>

namespace omni
{
namespace isaac
{
namespace dr
{

class DRManager : public utils::BridgeApplicationBase<DRComponentBase<pxr::DrSchemaBaseComponent>>
{

public:
    DRManager(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);
    ~DRManager();
    void initialize(pxr::UsdStageWeakPtr stage, carb::tokens::ITokens* tokens, omni::renderer::IDebugDraw* debugDraw);
    void tick(double dt);
    void onComponentAdd(const pxr::UsdPrim& prim);
    void tickManual();
    void onStop();

    std::string getDRLayerName()
    {
        if (mNewSublayer)
        {
            return mNewSublayer->GetIdentifier();
        }
        else
        {
            return "";
        }
    }

private:
    carb::tokens::ITokens* mTokens;
    omni::renderer::IDebugDraw* mDebugDrawPtr;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr;
    omni::usd::Layers* mLayer = nullptr;
    double mTimeElapsed = 0.0;
    pxr::SdfLayerRefPtr mNewSublayer = nullptr;
    size_t mFinalPosition = 0;
    pxr::UsdPrim mDrScope = pxr::UsdPrim();
};
}
}
}
