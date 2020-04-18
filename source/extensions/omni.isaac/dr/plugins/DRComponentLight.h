#pragma once

#include "DRComponentBase.h"

#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <DrSchema/baseComponent.h>
#include <DrSchema/lightComponent.h>

#include <functional>
#include <random>


namespace omni
{
namespace isaac
{
namespace dr
{

class DRComponentLight : public DRComponentBase<pxr::DrSchemaBaseComponent>
{
public:
    DRComponentLight();
    ~DRComponentLight();
    virtual void initialize(const pxr::DrSchemaLightComponent& prim, pxr::UsdStageRefPtr stage);
    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();

private:
    void update();
    void stop();

    std::vector<std::string> mPaths;
    std::vector<float> mLrRange, mLgRange, mLbRange;
    pxr::GfVec2f mLiRange, mLtRange;
    bool mEnableColorTemperature;
    std::vector<pxr::UsdPrim> mAllPrims;
};
}
}
}
