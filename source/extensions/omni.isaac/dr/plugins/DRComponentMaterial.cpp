// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentMaterial.h"

#include <AudioSchema/sound.h>
#include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/InterfaceUtils.h>
#include <carb/filesystem/IFileSystem.h>
#include <DrSchema/materialComponent.h>

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

DRComponentMaterial::DRComponentMaterial() : DRComponentBase()
{
    mDatasource = carb::getFramework()->acquireInterface<carb::datasource::IDataSource>("omni.connection.plugin");
    mConnection = omni::kit::getLatestConnection(omni::kit::getConnectionHub());
    mIsIgnore = false;
    mIsGrouping = false;
}
DRComponentMaterial::~DRComponentMaterial()
{
    stop();
}
void DRComponentMaterial::initialize(const pxr::DrSchemaMaterialComponent& prim, pxr::UsdStageWeakPtr stage)
{
    DRComponentBase::initialize(prim, stage);
}
void DRComponentMaterial::onStart()
{
    CARB_LOG_INFO("DR Material Component Started");
    // Get DR layer and switch USD context
    auto layers = mStage->GetLayerStack();
    for (auto&& layer : layers)
    {
        if (layer->GetIdentifier().find(mDRLayerName) != std::string::npos)
            mMaterialLayer = layer;
    }
    onComponentChange();
}
void DRComponentMaterial::update()
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
    if (mMaterialLayer)
    {
        mMaterialPrims.clear();
        mMaterialShades.clear();
        pxr::UsdEditContext context(mStage, mMaterialLayer);
        for (std::string& url : mMaterialList)
        {
            std::string mdlDataSourcePath = url.substr(std::strlen("omni:"));
            carb::extras::Path urlPath(url.c_str());
            if (!omni::usd::UsdUtils::hasPrimAtPath(mStage, "/Materials"))
            {
                omni::usd::UsdUtils::createPrim(
                    mStage, "/Materials", [](pxr::UsdStageWeakPtr mStage, const pxr::SdfPath& path) {
                        return pxr::UsdGeomScope::Define(mStage, path).GetPrim();
                    });
            }
            std::string materialPrimPath = "/Materials/" + urlPath.getStem();
            if (!omni::usd::UsdUtils::hasPrimAtPath(mStage, materialPrimPath))
            {
                omni::usd::AssetUtils::createPrimFromAssetPath(
                    mStage, url.c_str(), materialPrimPath.c_str(), mdlDataSourcePath.c_str(), mDatasource, mConnection);
            }
            auto materialPrim = mStage->GetPrimAtPath(
                pxr::SdfPath((mStage->GetDefaultPrim().GetPath().GetString() + materialPrimPath).c_str()));
            mMaterialPrims.push_back(materialPrim);
            pxr::UsdShadeMaterial material(materialPrim);
            mMaterialShades.push_back(material);
        }
    }
    pxr::UsdEditTarget editTarget(mStage->GetRootLayer());
    mStage->SetEditTarget(editTarget);
}
void DRComponentMaterial::onComponentChange()
{
    std::string materialList, ignoredClass, groupedClass;

    const pxr::DrSchemaMaterialComponent& materialPrim = (pxr::DrSchemaMaterialComponent)mPrim;
    materialPrim.GetCompNameAttr().Get(&mCompName);
    materialPrim.GetMaterialListAttr().Get(&materialList);
    materialPrim.GetIgnoredClassAttr().Get(&ignoredClass);
    materialPrim.GetGroupedClassAttr().Get(&groupedClass);
    materialPrim.GetDurationAttr().Get(&mRandomizationDurationInterval);
    materialPrim.GetIncludeChildrenAttr().Get(&mIncludeChild);

    mPaths.clear();
    pxr::UsdRelationship primPaths = materialPrim.GetPrimPathsRel();
    pxr::SdfPathVector targets;
    primPaths.GetTargets(&targets);
    for (auto target : targets)
        mPaths.push_back(target.GetString());
    if (materialList != "")
        boost::split(mMaterialList, materialList, [](char c) { return c == ','; });
    if (ignoredClass != "")
        boost::split(mIgnoreClassList, ignoredClass, [](char c) { return c == ','; });
    if (groupedClass != "")
        boost::split(mGroupClassList, groupedClass, [](char c) { return c == ','; });
    update();
    CARB_LOG_INFO("Material Update: %s", mCompName.c_str());
}
void DRComponentMaterial::stop()
{
    CARB_LOG_INFO("DR Material Component Stopped");
    if (mStage && mMaterialLayer)
    {
        pxr::UsdEditContext context(mStage, mMaterialLayer);
        for (pxr::UsdPrim& materialPrim : mMaterialPrims)
        {
            if (materialPrim)
                omni::usd::UsdUtils::removePrim(materialPrim);
        }
        pxr::UsdPrim materialPrim =
            mStage->GetPrimAtPath(pxr::SdfPath(mStage->GetDefaultPrim().GetPath().GetString() + "/Materials"));
        if (materialPrim)
            if (materialPrim.GetChildren().empty())
                omni::usd::UsdUtils::removePrim(materialPrim);

        mPrimClassMap.clear();
        mPrimMaterialBindingsMap.clear();
        mClassMaterialMap.clear();
        mMaterialPrims.clear();
        mMaterialShades.clear();
        mAllPrims.clear();
    }
}
void DRComponentMaterial::tick()
{
    for (auto& primMaterialBinding : mPrimMaterialBindingsMap)
    {
        if (mMaterialList.size() == 0 || mMaterialShades.size() == 0)
            return;
        int randVal = int(randomRange(0.0f, mMaterialList.size() * 1.0f));
        pxr::UsdShadeMaterialBindingAPI materialBinding = primMaterialBinding.second;
        // Check for classes to be grouped
        if (mIsGrouping && mPrimClassMap.find(primMaterialBinding.first) != mPrimClassMap.end())
        {
            std::string className = mPrimClassMap[primMaterialBinding.first];
            if (mClassMaterialMap.find(className) == mClassMaterialMap.end())
                mClassMaterialMap[className] = randVal;
            else
                randVal = mClassMaterialMap[className];
        }
        materialBinding.Bind(mMaterialShades[randVal], pxr::UsdShadeTokens->strongerThanDescendants);
    }
    mClassMaterialMap.clear();
}
}
}
}
