#pragma once


#include "DRComponentBase.h"

#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>
#include <carb/tokens/ITokens.h>

#include <DrSchema/baseComponent.h>
#include <DrSchema/colorComponent.h>

#include <functional>
#include <random>


namespace omni
{
namespace isaac
{
namespace dr
{

class DRComponentColor : public DRComponentBase<pxr::DrSchemaBaseComponent>
{
public:
    DRComponentColor(carb::tokens::ITokens* tokens);
    ~DRComponentColor();
    virtual void initialize(const pxr::DrSchemaColorComponent& prim, pxr::UsdStageRefPtr stage);
    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();

private:
    void update();
    void stop();

    std::string mOmniPBRMatPath;
    std::vector<std::string> mPaths;
    std::vector<float> mRRange, mGRange, mBRange;
    std::vector<pxr::UsdPrim> mAllPrims;
    pxr::SdfLayerHandle mColorLayer;
    pxr::UsdShadeMaterial mColorMaterialShade;
    pxr::UsdPrim mColorMaterialPrim;
    carb::tokens::ITokens* mTokens;
};

}
}
}
