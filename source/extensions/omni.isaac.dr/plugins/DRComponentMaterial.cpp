// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentMaterial.h"

#include <boost/algorithm/string.hpp>

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
    mDatasource =
        carb::getFramework()->acquireInterface<carb::datasource::IDataSource>("carb.datasource-omniclient.plugin");
    mConnection = carb::datasource::connectAndWait(carb::datasource::ConnectionDesc{ "" }, mDatasource);
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
    onComponentChange();
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
        auto primType = prim.GetTypeName().GetString();
        if (prim && (primType == "Mesh" || primType == "Xform"))
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
    mMaterialPrims.clear();
    mMaterialShades.clear();
    if (mLoadedMaterialPaths.size() > 0)
    {
        for (std::string& materialPath : mLoadedMaterialPaths)
        {
            auto materialPrim = mStage->GetPrimAtPath(pxr::SdfPath(materialPath.c_str()));
            pxr::UsdShadeMaterial material(materialPrim);
            mMaterialShades.push_back(material);
        }
    }
    if (mMaterialLayer)
    {
        pxr::UsdEditContext context(mStage, mMaterialLayer);
        for (std::string& url : mMaterialList)
        {
            std::string mdlDataSourcePath = url;
            carb::extras::Path urlPath(url.c_str());
            if (!omni::usd::UsdUtils::hasPrimAtPath(mStage, "/DR"))
            {
                omni::usd::UsdUtils::createPrim(mStage, "/DR", [](pxr::UsdStageWeakPtr mStage, const pxr::SdfPath& path) {
                    return pxr::UsdGeomScope::Define(mStage, path).GetPrim();
                });
            }
            std::string materialPrimPath = "/DR/" + urlPath.getStem();
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
    materialPrim.GetSeedAttr().Get(&mSeed);
    if (mCurrentSeed != mSeed)
    {
        mRandomGenerator.seed(mSeed);
        mCurrentSeed = mSeed;
    }

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
    mLoadedMaterialPaths.clear();
    pxr::UsdRelationship loadedMaterialPrimPaths = materialPrim.GetLoadedMaterialPrimPathsRel();
    pxr::SdfPathVector materialTargets;
    loadedMaterialPrimPaths.GetTargets(&materialTargets);
    for (auto target : materialTargets)
        mLoadedMaterialPaths.push_back(target.GetString());
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
            mStage->GetPrimAtPath(pxr::SdfPath(mStage->GetDefaultPrim().GetPath().GetString() + "/DR"));
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
        if (mMaterialShades.size() == 0)
            return;
        int randVal = int(randomRangeFloat(0.0f, mMaterialShades.size() * 1.0f));
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
