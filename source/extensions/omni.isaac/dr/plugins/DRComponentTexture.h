#pragma once

#include "DRComponentBase.h"

#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <DrSchema/baseComponent.h>
#include <DrSchema/textureComponent.h>

#include <functional>
#include <random>
#include <unordered_map>


namespace omni
{
namespace isaac
{
namespace dr
{

class DRComponentTexture : public DRComponentBase<pxr::DrSchemaBaseComponent>
{
public:
    DRComponentTexture();
    ~DRComponentTexture();
    virtual void initialize(const pxr::DrSchemaTextureComponent& prim, pxr::UsdStageRefPtr stage);
    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();

private:
    void update();
    void stop();

    std::vector<std::string> mPaths, mTextureList, mGroupClassList;
    std::vector<pxr::UsdPrim> mMaterialPrims, mAllPrims;
    std::vector<pxr::UsdShadeMaterial> mMaterialShades;
    std::unordered_map<std::string, std::string> mPrimClassMap;
    std::unordered_map<std::string, int> mClassTextureMap;
    std::unordered_map<std::string, pxr::UsdShadeMaterialBindingAPI> mPrimMaterialBindingsMap;
    bool mIsIgnore, mIsGrouping;
    pxr::SdfLayerHandle mTextureLayer;
};
}
}
}
