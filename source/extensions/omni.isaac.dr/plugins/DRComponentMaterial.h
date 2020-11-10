#pragma once

#include "DRComponentBase.h"

#include <carb/datasource/IDataSource.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <drSchema/baseComponent.h>
#include <drSchema/materialComponent.h>

#include <functional>
#include <random>
#include <unordered_map>


namespace omni
{
namespace isaac
{
namespace dr
{

class DRComponentMaterial : public DRComponentBase<pxr::DrSchemaBaseComponent>
{
public:
    DRComponentMaterial();
    ~DRComponentMaterial();
    virtual void initialize(const pxr::DrSchemaMaterialComponent& prim, pxr::UsdStageWeakPtr stage);
    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();

private:
    void update();
    void stop();

    std::vector<std::string> mPaths, mMaterialList, mGroupClassList, mLoadedMaterialPaths;
    std::vector<pxr::UsdPrim> mMaterialPrims, mAllPrims;
    std::vector<pxr::UsdShadeMaterial> mMaterialShades;
    std::unordered_map<std::string, std::string> mPrimClassMap;
    std::unordered_map<std::string, int> mClassMaterialMap;
    std::unordered_map<std::string, pxr::UsdShadeMaterialBindingAPI> mPrimMaterialBindingsMap;
    bool mIsIgnore, mIsGrouping;
    pxr::SdfLayerHandle mMaterialLayer;
    carb::datasource::IDataSource* mDatasource;
    carb::datasource::Connection* mConnection;
};
}
}
}
