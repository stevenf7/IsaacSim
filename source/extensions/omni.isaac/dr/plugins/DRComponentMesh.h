#pragma once

#include "DRComponentBase.h"

#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <DrSchema/baseComponent.h>
#include <DrSchema/meshComponent.h>

#include <functional>
#include <random>


namespace omni
{
namespace isaac
{
namespace dr
{

class DRComponentMesh : public DRComponentBase<pxr::DrSchemaBaseComponent>
{
public:
    DRComponentMesh();
    ~DRComponentMesh();
    virtual void initialize(const pxr::DrSchemaMeshComponent& prim, pxr::UsdStageWeakPtr stage);
    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();

private:
    void update();
    void stop();

    std::vector<std::string> mPaths, mMeshList;
    std::vector<pxr::UsdPrim> mMeshPrims;
    std::unordered_map<std::string, std::vector<pxr::UsdPrim>> mCopiedMeshPrims;
    pxr::GfVec2i mNumMeshRange;
    std::vector<pxr::UsdPrim> mAllPrims;
    pxr::SdfLayerHandle mMeshLayer;
};

}
}
}
