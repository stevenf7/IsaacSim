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
    DRManager();
    ~DRManager();
    void initialize(pxr::UsdStageWeakPtr stage, carb::tokens::ITokens* tokens);
    void tick(double dt);
    void onComponentAdd(const pxr::UsdPrim& prim);
    void tickManual();

private:
    carb::tokens::ITokens* mTokens;
    omni::usd::Layers* mLayer = nullptr;
    std::string mDRLayerName = "";
    double mTimeElapsed = 0.0f;
    std::string mRootLayerIdentifier = "";
};
}
}
}
