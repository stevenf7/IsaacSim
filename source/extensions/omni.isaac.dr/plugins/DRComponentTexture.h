// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "DRComponentBase.h"

#include <carb/datasource/IDataSource.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>
#include <carb/tokens/ITokens.h>

#include <drSchema/baseComponent.h>
#include <drSchema/textureComponent.h>

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
    DRComponentTexture(carb::tokens::ITokens* tokens);
    ~DRComponentTexture();
    virtual void initialize(const pxr::DrSchemaTextureComponent& prim, pxr::UsdStageWeakPtr stage);
    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();

private:
    void update();
    void stop();

    std::string mOmniPBRMatPath;
    std::vector<std::string> mPaths, mTextureList, mGroupClassList;
    std::vector<pxr::UsdPrim> mMaterialPrims, mAllPrims;
    std::vector<pxr::UsdShadeMaterial> mMaterialShades;
    std::unordered_map<std::string, std::string> mPrimClassMap;
    std::unordered_map<std::string, int> mClassTextureMap;
    std::unordered_map<std::string, pxr::UsdShadeMaterialBindingAPI> mPrimMaterialBindingsMap;
    bool mIsIgnore, mIsGrouping, mDoOnce, mEnableProjectUVW;
    pxr::UsdShadeMaterial mTextureMaterialShade;
    pxr::UsdPrim mTextureMaterialPrim;
    carb::tokens::ITokens* mTokens;
    carb::datasource::IDataSource* mDatasource;
    carb::datasource::Connection* mConnection;
};
}
}
}
