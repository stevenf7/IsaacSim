// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "DRComponentBase.h"
#include "DRComponentColor.h"
#include "DRComponentLight.h"
#include "DRComponentMaterial.h"
#include "DRComponentMesh.h"
#include "DRComponentMovement.h"
#include "DRComponentRotation.h"
#include "DRComponentScale.h"
#include "DRComponentTexture.h"
#include "DRComponentVisibility.h"
#include "plugins/bridge/BridgeApplication.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/logging/Log.h>
#include <carb/tokens/ITokens.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>

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
    void initialize(pxr::UsdStageWeakPtr stage, carb::tokens::ITokens* tokens);
    void tick(double dt);
    void onComponentAdd(const pxr::UsdPrim& prim);
    void tickManual();
    void onStop();

private:
    carb::tokens::ITokens* mTokens;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr;
    omni::usd::Layers* mLayer = nullptr;
    std::string mDRLayerName = "";
    double mTimeElapsed = 0.0f;
    std::string mRootLayerIdentifier = "";
    pxr::SdfLayerRefPtr mNewSublayer;
};
}
}
}
