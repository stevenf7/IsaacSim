// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentTexture.h"

#include <AudioSchema/sound.h>
#include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/InterfaceUtils.h>
#include <carb/filesystem/IFileSystem.h>
#include <DrSchema/textureComponent.h>

#include <omni/kit/KitUtils.h>
#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/AssetUtils.h>
#include <omni/usd/UsdUtils.h>

namespace omni
{
namespace isaac
{
namespace dr
{

DRComponentTexture::DRComponentTexture() : DRComponentBase()
{
    mDatasource = carb::getFramework()->acquireInterface<carb::datasource::IDataSource>("omni.connection.plugin");
    mConnection = omni::kit::getLatestConnection(omni::kit::getConnectionHub());
    mIsIgnore = false;
    mIsGrouping = false;
}
DRComponentTexture::~DRComponentTexture()
{
    stop();
}
void DRComponentTexture::initialize(const pxr::DrSchemaTextureComponent& prim, pxr::UsdStageRefPtr stage)
{
    DRComponentBase::initialize(prim, stage);
}
void DRComponentTexture::onStart()
{
    CARB_LOG_INFO("DR Texture Component Started");
    // Get DR layer and switch USD context
    auto layers = mStage->GetLayerStack();
    for (auto&& layer : layers)
    {
        if (layer->GetIdentifier().find(mDRLayerName) != std::string::npos)
            mTextureLayer = layer;
    }
}
void DRComponentTexture::update()
{
    if (mGroupClassList.size() > 0)
        mIsGrouping = true;
    if (mIgnoreClassList.size() > 0)
        mIsIgnore = true;

    mAllPrims.clear();
    for (auto& path : mPaths)
    {
        pxr::UsdPrim prim = mStage->GetPrimAtPath(pxr::SdfPath(path.c_str()));
        // Check for classes to be ignored
        if (mIsIgnore && prim && !ignoreClass(prim.GetPath().GetString(), mGroupClassList))
            mAllPrims.push_back(prim);
        if (!mIsIgnore && prim)
            mAllPrims.push_back(prim);

        if (mIncludeChild && prim)
        {
            pxr::UsdPrimSubtreeRange range = prim.GetDescendants();
            for (pxr::UsdPrimSubtreeRange::iterator iter = range.begin(); iter != range.end(); ++iter)
            {
                pxr::UsdPrim prim = *iter;
                // Check for classes to be ignored
                if (mIsIgnore && prim && !ignoreClass(prim.GetPath().GetString(), mGroupClassList))
                    mAllPrims.push_back(prim);
                if (!mIsIgnore && prim)
                    mAllPrims.push_back(prim);
            }
        }
    }

    mPrimMaterialBindingsMap.clear();
    mPrimClassMap.clear();
    for (auto& prim : mAllPrims)
    {
        if (prim && prim.GetTypeName().GetString() == "Mesh")
        {
            pxr::UsdShadeMaterialBindingAPI materialBinding(prim);
            mPrimMaterialBindingsMap.insert(std::make_pair(prim.GetPath().GetString(), materialBinding));
            // Check for classes to be grouped
            if (mIsGrouping)
            {
                for (std::string& groupClass : mGroupClassList)
                {
                    if (prim.GetPath().GetString().find(groupClass) != std::string::npos)
                    {
                        mPrimClassMap.insert(std::make_pair(prim.GetPath().GetString(), groupClass));
                    }
                }
            }
        }
    }
    if (mTextureLayer)
    {
        mMaterialPrims.clear();
        mMaterialShades.clear();
        pxr::UsdEditContext context(mStage, mTextureLayer);
        for (std::string& url : mTextureList)
        {
            std::string mdlDataSourcePath = url.substr(std::strlen("omni:"));
            carb::extras::Path urlPath(url.c_str());
            if (!omni::usd::UsdUtils::hasPrimAtPath(mStage, "/Textures"))
            {
                omni::usd::UsdUtils::createPrim(
                    mStage, "/Textures", [](pxr::UsdStageWeakPtr mStage, const pxr::SdfPath& path) {
                        return pxr::UsdGeomScope::Define(mStage, path).GetPrim();
                    });
            }
            auto materialPrim = omni::usd::AssetUtils::createPrimFromAssetPath(
                mStage, url.c_str(), ("/Textures/" + urlPath.getStem()).getStringBuffer(), mdlDataSourcePath.c_str(),
                mDatasource, mConnection);
            mMaterialPrims.push_back(materialPrim);

            pxr::UsdShadeMaterial material(materialPrim);
            mMaterialShades.push_back(material);
        }
    }
    pxr::UsdEditTarget editTarget(mStage->GetRootLayer());
    mStage->SetEditTarget(editTarget);
}
void DRComponentTexture::onComponentChange()
{
    std::string textureList, ignoredClass, groupedClass;

    const pxr::DrSchemaTextureComponent& texturePrim = (pxr::DrSchemaTextureComponent)mPrim;
    texturePrim.GetCompNameAttr().Get(&mCompName);
    texturePrim.GetTextureListAttr().Get(&textureList);
    texturePrim.GetIgnoredClassAttr().Get(&ignoredClass);
    texturePrim.GetGroupedClassAttr().Get(&groupedClass);
    texturePrim.GetDurationAttr().Get(&mRandomizationDurationInterval);
    texturePrim.GetIncludeChildrenAttr().Get(&mIncludeChild);

    mPaths.clear();
    pxr::UsdRelationship primPaths = texturePrim.GetPrimPathsRel();
    pxr::SdfPathVector targets;
    primPaths.GetTargets(&targets);
    for (auto target : targets)
        mPaths.push_back(target.GetString());
    if (textureList != "")
        boost::split(mTextureList, textureList, [](char c) { return c == ','; });
    if (ignoredClass != "")
        boost::split(mIgnoreClassList, ignoredClass, [](char c) { return c == ','; });
    if (groupedClass != "")
        boost::split(mGroupClassList, groupedClass, [](char c) { return c == ','; });
    update();
    CARB_LOG_INFO("Texture Update: %s", mCompName.c_str());
}
void DRComponentTexture::stop()
{
    CARB_LOG_INFO("DR Texture Component Stopped");
    if (mStage && mTextureLayer)
    {
        pxr::UsdEditContext context(mStage, mTextureLayer);
        for (pxr::UsdPrim& materialPrim : mMaterialPrims)
        {
            if (materialPrim)
                omni::usd::UsdUtils::removePrim(materialPrim);
        }
        pxr::UsdPrim texturePrim =
            mStage->GetPrimAtPath(pxr::SdfPath(mStage->GetDefaultPrim().GetPath().GetString() + "/Textures"));
        if (texturePrim)
            if (texturePrim.GetChildren().empty())
                omni::usd::UsdUtils::removePrim(texturePrim);

        mPrimClassMap.clear();
        mPrimMaterialBindingsMap.clear();
        mClassTextureMap.clear();
        mMaterialPrims.clear();
        mMaterialShades.clear();
        mAllPrims.clear();
    }
}
void DRComponentTexture::tick()
{
    for (auto& primMaterialBinding : mPrimMaterialBindingsMap)
    {
        if (mTextureList.size() == 0)
            return;
        int randVal = int(randomRange(0.0f, mTextureList.size() * 1.0f));
        pxr::UsdShadeMaterialBindingAPI materialBinding = primMaterialBinding.second;
        // Check for classes to be grouped
        if (mIsGrouping && mPrimClassMap.find(primMaterialBinding.first) != mPrimClassMap.end())
        {
            std::string className = mPrimClassMap[primMaterialBinding.first];
            if (mClassTextureMap.find(className) == mClassTextureMap.end())
                mClassTextureMap[className] = randVal;
            else
                randVal = mClassTextureMap[className];
        }
        materialBinding.Bind(mMaterialShades[randVal], pxr::UsdShadeTokens->strongerThanDescendants);
    }
    mClassTextureMap.clear();
}
}
}
}
