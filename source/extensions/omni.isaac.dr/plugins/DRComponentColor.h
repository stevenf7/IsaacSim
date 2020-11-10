#pragma once


#include "DRComponentBase.h"

#include <carb/datasource/IDataSource.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>
#include <carb/tokens/ITokens.h>

#include <drSchema/baseComponent.h>
#include <drSchema/colorComponent.h>

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
    virtual void initialize(const pxr::DrSchemaColorComponent& prim, pxr::UsdStageWeakPtr stage);
    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();

private:
    void update();
    void stop();

    std::string mOmniPBRMatPath;
    std::vector<std::string> mPaths;
    std::vector<float> mRRange, mGRange, mBRange;
    pxr::GfVec2f mRoughnessRange, mMetallicRange;
    std::vector<pxr::UsdPrim> mAllPrims, mAllMaterialPrims;
    pxr::SdfLayerHandle mColorLayer;
    pxr::UsdShadeMaterial mColorMaterialShade;
    pxr::UsdPrim mColorMaterialPrim;
    carb::tokens::ITokens* mTokens;
    carb::datasource::IDataSource* mDatasource;
    carb::datasource::Connection* mConnection;
};

}
}
}
