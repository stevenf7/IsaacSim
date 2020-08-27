#pragma once

#include "DRComponentBase.h"

#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <DrSchema/baseComponent.h>
#include <DrSchema/visibilityComponent.h>

#include <functional>
#include <random>


namespace omni
{
namespace isaac
{
namespace dr
{

class DRComponentVisibility : public DRComponentBase<pxr::DrSchemaBaseComponent>
{
public:
    DRComponentVisibility();
    ~DRComponentVisibility();
    virtual void initialize(const pxr::DrSchemaVisibilityComponent& prim, pxr::UsdStageWeakPtr stage);
    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();

private:
    void update();
    void stop();

    std::vector<std::string> mPaths;
    pxr::GfVec2i mNumVisibleRange;
    std::vector<pxr::UsdPrim> mAllPrims;
};

}
}
}
