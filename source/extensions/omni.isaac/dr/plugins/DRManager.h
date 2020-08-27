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
#include "plugins/core/ComponentManager.h"

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

class DRManager : public utils::ComponentManager, public pxr::TfWeakBase
{

public:
    DRManager();
    ~DRManager();
    void initialize(pxr::UsdStageWeakPtr stage, carb::tokens::ITokens* tokens);
    void tick(double dt);
    void initComponents();
    void onComponentAdd(const pxr::UsdPrim& prim);
    void onComponentChange(const pxr::UsdPrim& prim);
    void onComponentRemove(const pxr::SdfPath& primPath);
    void deleteAllComponents();
    void loadComponentFromUsd();
    void tickManual();

private:
    void handlePrimChanged(const class pxr::UsdNotice::ObjectsChanged& objectsChanged);

    std::unordered_map<std::string, std::unique_ptr<DRComponentBase<pxr::DrSchemaBaseComponent>>> mAllComponents;
    carb::tokens::ITokens* mTokens;
    pxr::TfNotice::Key mNoticeListener;
    omni::usd::Layers* mLayer = nullptr;
    std::string mDRLayerName = "";
    double mTimeElapsed = 0.0f;
    bool mDoOnce = false, mPrimDeleted = false;
    std::string mRootLayerIdentifier = "";
};
}
}
}
