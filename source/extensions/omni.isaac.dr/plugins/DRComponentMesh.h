// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "DRComponentBase.h"

#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <drSchema/baseComponent.h>
#include <drSchema/meshComponent.h>

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

    std::vector<std::string> mPaths, mMeshList;
    std::vector<pxr::UsdPrim> mMeshPrims;
    std::unordered_map<std::string, std::vector<pxr::UsdPrim>> mCopiedMeshPrims;
    pxr::GfVec2i mNumMeshRange;
    std::vector<pxr::UsdPrim> mAllPrims;

    pxr::SdfPath mParentPrimPath;
    pxr::UsdPrim mParentPrim;
};

}
}
}
