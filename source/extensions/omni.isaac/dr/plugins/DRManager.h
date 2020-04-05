#pragma once

#include "DRComponentBase.h"
#include "DRComponentColor.h"
#include "DRComponentLight.h"
#include "DRComponentMovement.h"
#include "DRComponentScale.h"
#include "DRComponentTexture.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/logging/Log.h>
#include <carb/tokens/ITokens.h>

#include <omni/usd/Layers.h>

#include <functional>
#include <string>

namespace omni
{
namespace isaac
{
namespace dr
{

class DRManager
{

public:
    explicit DRManager(pxr::UsdStageWeakPtr stage, carb::tokens::ITokens* tokens);
    DRManager(const DRManager&) = delete;
    DRManager& operator=(const DRManager&) = delete;
    ~DRManager();
    void tick(const float dt = 0.0f);
    void onComponentAdd(const pxr::UsdPrim& prim);
    void onComponentChange(const pxr::UsdPrim& prim);
    void deleteAllComponents();
    void loadComponentFromUsd();

private:
    std::vector<std::unique_ptr<DRComponentBase>> mAllComponents;
    pxr::UsdStageWeakPtr mStage;
    carb::tokens::ITokens* mTokens;
    std::unordered_map<std::string, int> mComponentMap;
    omni::usd::Layers* mLayer = nullptr;
    std::string mDRLayerName = "";
    float mTimeElapsed = 0.0f;
    bool mDoOnce = false;
    std::string mRootLayerIdentifier = "";
    std::vector<std::string> mSupportedComponents{ "ColorComponent", "MovementComponent", "ScaleComponent",
                                                   "LightComponent", "TextureComponent" };
};
}
}
}
