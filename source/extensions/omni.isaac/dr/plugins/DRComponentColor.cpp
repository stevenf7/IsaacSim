// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentColor.h"

#include <boost/algorithm/string.hpp>
#include <carb/tokens/ITokens.h>
#include <carb/tokens/TokensUtils.h>

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

DRComponentColor::DRComponentColor(carb::tokens::ITokens* tokens) : DRComponentBase()
{
    mTokens = tokens;
    mRRange.push_back(0);
    mRRange.push_back(1);
    mGRange.push_back(0);
    mGRange.push_back(1);
    mBRange.push_back(0);
    mBRange.push_back(1);
    mDatasource =
        carb::getFramework()->acquireInterface<carb::datasource::IDataSource>("carb.datasource-omniclient.plugin");
    mConnection = carb::datasource::connectAndWait(
        carb::datasource::ConnectionDesc{ carb::tokens::resolveString(mTokens, "${kit}/../../library/mdl/Base/").c_str() },
        mDatasource);
}
DRComponentColor::~DRComponentColor()
{
    stop();
}
void DRComponentColor::initialize(const pxr::DrSchemaColorComponent& prim, pxr::UsdStageWeakPtr stage)
{
    DRComponentBase::initialize(prim, stage);
}
void DRComponentColor::onStart()
{
    CARB_LOG_INFO("DR Color Component Started");
    // Get DR layer and switch USD context
    auto layers = mStage->GetLayerStack();
    for (auto&& layer : layers)
    {
        if (layer->GetIdentifier().find(mDRLayerName) != std::string::npos)
            mColorLayer = layer;
    }
    if (mColorLayer)
    {
        pxr::UsdEditContext context(mStage, mColorLayer);
        carb::extras::Path urlPath(mOmniPBRMatPath.c_str());
        // Check for /Colors prim and if base OmniPBR material is loaded
        if (!omni::usd::UsdUtils::hasPrimAtPath(mStage, "/Colors"))
        {
            omni::usd::UsdUtils::createPrim(mStage, "/Colors", [](pxr::UsdStageWeakPtr mStage, const pxr::SdfPath& path) {
                return pxr::UsdGeomScope::Define(mStage, path).GetPrim();
            });
        }
        std::string colorCompMaterialPath = "/Colors/" + mCompName;
        if (!omni::usd::UsdUtils::hasPrimAtPath(mStage, colorCompMaterialPath))
        {
            omni::usd::UsdUtils::createPrim(
                mStage, colorCompMaterialPath.c_str(), [](pxr::UsdStageWeakPtr mStage, const pxr::SdfPath& path) {
                    return pxr::UsdGeomScope::Define(mStage, path).GetPrim();
                });
        }
        std::string colorMaterialPrimName =
            mStage->GetDefaultPrim().GetPath().GetString() + colorCompMaterialPath + "/OmniPBR";
        mColorMaterialPrim = mStage->DefinePrim(pxr::SdfPath(colorMaterialPrimName.c_str()), pxr::TfToken("Material"));
        auto shadeMaterialPrim = pxr::UsdShadeMaterial(mColorMaterialPrim);
        auto shaderMtlPath = mStage->DefinePrim(pxr::SdfPath(colorMaterialPrimName + "/Shader"), pxr::TfToken("Shader"));
        auto shadeShaderPrim = pxr::UsdShadeShader(shaderMtlPath);
        auto shaderOut = shadeShaderPrim.CreateOutput(pxr::TfToken("out"), pxr::SdfValueTypeNames->Token);

        shadeMaterialPrim.CreateSurfaceOutput(pxr::TfToken("mdl")).ConnectToSource(shaderOut);
        shadeMaterialPrim.CreateVolumeOutput(pxr::TfToken("mdl")).ConnectToSource(shaderOut);
        shadeMaterialPrim.CreateDisplacementOutput(pxr::TfToken("mdl")).ConnectToSource(shaderOut);
        shadeShaderPrim.GetImplementationSourceAttr().Set(pxr::UsdShadeTokens->sourceAsset);
        shadeShaderPrim.SetSourceAsset(pxr::SdfAssetPath("OmniPBR.mdl"), pxr::TfToken("mdl"));
        shadeShaderPrim.SetSourceAssetSubIdentifier(pxr::TfToken("OmniPBR"), pxr::TfToken("mdl"));
        mColorMaterialShade = shadeMaterialPrim;
    }
    pxr::UsdEditTarget editTarget(mStage->GetRootLayer());
    mStage->SetEditTarget(editTarget);
    onComponentChange();
}
void DRComponentColor::update()
{
    CARB_LOG_INFO("DR Color Component Updated");
    mAllPrims.clear();
    for (auto& path : mPaths)
    {
        pxr::UsdPrim prim = mStage->GetPrimAtPath(pxr::SdfPath(path.c_str()));
        if (prim)
            mAllPrims.push_back(prim);

        if (mIncludeChild && prim)
        {
            // Unbinding material for parent since strongerThanDescendants is used that will disable child material
            // binding
            mAllPrims.pop_back();
            pxr::UsdShadeMaterialBindingAPI materialBinding(prim);
            materialBinding.UnbindAllBindings();
            pxr::UsdPrimSubtreeRange range = prim.GetDescendants();
            for (pxr::UsdPrimSubtreeRange::iterator iter = range.begin(); iter != range.end(); ++iter)
            {
                pxr::UsdPrim prim = *iter;
                if (prim && prim.GetTypeName().GetString() == "Xform")
                    mAllPrims.push_back(prim);
            }
        }
    }

    mAllMaterialPrims.clear();
    unsigned int primIndex = 1;
    // Create material instances and binding it to each prim
    for (auto& prim : mAllPrims)
    {
        primIndex++;
        std::string mColorCompPathName = mStage->GetDefaultPrim().GetPath().GetString() + "/Colors/" + mCompName;
        std::string mCopyColorMaterialPrimName = mColorCompPathName + "/OmniPBR_" + std::to_string(primIndex);
        if (mColorMaterialPrim && !omni::usd::UsdUtils::hasPrimAtPath(mStage, mCopyColorMaterialPrimName, false))
        {
            pxr::UsdEditContext context(mStage, mColorLayer);
            omni::usd::UsdUtils::copyPrim(mColorMaterialPrim, nullptr, false, false);
            pxr::UsdEditTarget editTarget(mStage->GetRootLayer());
            mStage->SetEditTarget(editTarget);
        }
        auto mCopyColorMaterialPrim = mStage->GetPrimAtPath(pxr::SdfPath(mCopyColorMaterialPrimName.c_str()));
        mAllMaterialPrims.push_back(mCopyColorMaterialPrim);
        pxr::UsdShadeMaterial materialShade(mCopyColorMaterialPrim);
        pxr::UsdShadeMaterialBindingAPI materialBinding(prim);
        materialBinding.Bind(materialShade, pxr::UsdShadeTokens->strongerThanDescendants);
    }
}
void DRComponentColor::onComponentChange()
{
    pxr::GfVec3f firstColor, secondColor;
    mOmniPBRMatPath = carb::tokens::resolveString(mTokens, "${kit}/../../library/mdl/Base/OmniPBR.mdl");

    const pxr::DrSchemaColorComponent& colorPrim = (pxr::DrSchemaColorComponent)mPrim;
    colorPrim.GetCompNameAttr().Get(&mCompName);
    colorPrim.GetFirstColorAttr().Get(&firstColor);
    colorPrim.GetSecondColorAttr().Get(&secondColor);
    colorPrim.GetRoughnessAttr().Get(&mRoughnessRange);
    colorPrim.GetMetallicAttr().Get(&mMetallicRange);
    colorPrim.GetDurationAttr().Get(&mRandomizationDurationInterval);
    colorPrim.GetIncludeChildrenAttr().Get(&mIncludeChild);
    colorPrim.GetSeedAttr().Get(&mSeed);
    if (mCurrentSeed != mSeed)
    {
        mRandomGenerator.seed(mSeed);
        mCurrentSeed = mSeed;
    }

    mPaths.clear();
    pxr::UsdRelationship primPaths = colorPrim.GetPrimPathsRel();
    pxr::SdfPathVector targets;
    primPaths.GetTargets(&targets);
    for (auto target : targets)
        mPaths.push_back(target.GetString());

    mRRange[0] = firstColor[0];
    mRRange[1] = secondColor[0];
    mGRange[0] = firstColor[1];
    mGRange[1] = secondColor[1];
    mBRange[0] = firstColor[2];
    mBRange[1] = secondColor[2];
    update();
    CARB_LOG_INFO("Color Update: %s", mCompName.c_str());
}
void DRComponentColor::stop()
{
    CARB_LOG_INFO("DR Color Component Stopped");
    if (mStage && mColorLayer)
    {
        pxr::UsdEditContext context(mStage, mColorLayer);
        // Remove color material instances
        for (auto materialPrim : mAllMaterialPrims)
        {
            if (materialPrim)
                omni::usd::UsdUtils::removePrim(materialPrim);
        }
        // Remove base color material
        if (mColorMaterialPrim)
            omni::usd::UsdUtils::removePrim(mColorMaterialPrim);
        // Remove component level Color prim
        pxr::UsdPrim colorCompPrim =
            mStage->GetPrimAtPath(pxr::SdfPath(mStage->GetDefaultPrim().GetPath().GetString() + "/Colors/" + mCompName));
        if (colorCompPrim)
            omni::usd::UsdUtils::removePrim(colorCompPrim);
        // Remove top-level Color prim
        pxr::UsdPrim colorPrim =
            mStage->GetPrimAtPath(pxr::SdfPath(mStage->GetDefaultPrim().GetPath().GetString() + "/Colors"));
        if (colorPrim && colorPrim.GetChildren().empty())
            omni::usd::UsdUtils::removePrim(colorPrim);
    }
}
void DRComponentColor::tick()
{
    unsigned int primIndex = 0;
    for (auto& prim : mAllPrims)
    {
        auto materialShadePrim =
            mStage->GetPrimAtPath(pxr::SdfPath(mAllMaterialPrims[primIndex].GetPrimPath().GetString() + "/Shader"));
        pxr::UsdShadeMaterial materialShade(materialShadePrim);
        auto primColor = materialShade.GetInput(pxr::TfToken("diffuse_color_constant"));
        if (primColor)
        {
            // CARB_LOG_WARN("prim set color");
            float r = randomRangeFloat(mRRange[0], mRRange[1]);
            float g = randomRangeFloat(mGRange[0], mGRange[1]);
            float b = randomRangeFloat(mBRange[0], mBRange[1]);
            primColor.Set(pxr::GfVec3f(r, g, b));
        }
        auto primRoughness = materialShade.GetInput(pxr::TfToken("reflection_roughness_constant"));
        if (primRoughness)
        {
            primRoughness.Set(randomRangeFloat(mRoughnessRange[0], mRoughnessRange[1]));
        }
        auto primMetallic = materialShade.GetInput(pxr::TfToken("metallic_constant"));
        if (primMetallic)
        {
            primMetallic.Set(randomRangeFloat(mMetallicRange[0], mMetallicRange[1]));
        }
        primIndex++;
    }
}

}
}
}
