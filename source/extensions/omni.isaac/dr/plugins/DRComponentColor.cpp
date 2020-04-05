// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentColor.h"

#include <AudioSchema/sound.h>
#include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/tokens/ITokens.h>
#include <carb/tokens/TokensUtils.h>
#include <carb/Types.h>
#include <carb/InterfaceUtils.h>

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
}
DRComponentColor::~DRComponentColor()
{
    stop();
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
        if (!omni::usd::UsdUtils::hasPrimAtPath(mStage, "/Colors"))
        {
            omni::usd::UsdUtils::createPrim(mStage, "/Colors", [](pxr::UsdStageWeakPtr mStage, const pxr::SdfPath& path) {
                return pxr::UsdGeomScope::Define(mStage, path).GetPrim();
            });
        }
        mColorMaterialPrim = omni::usd::AssetUtils::createPrimFromAssetPath(
            mStage, mOmniPBRMatPath.c_str(), ("/Colors/" + urlPath.getStem()).getStringBuffer());

        pxr::UsdShadeMaterial materialShade(mColorMaterialPrim);
        mColorMaterialShade = materialShade;
    }
    pxr::UsdEditTarget editTarget(mStage->GetRootLayer());
    mStage->SetEditTarget(editTarget);
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
            pxr::UsdPrimSubtreeRange range = prim.GetDescendants();
            for (pxr::UsdPrimSubtreeRange::iterator iter = range.begin(); iter != range.end(); ++iter)
            {
                pxr::UsdPrim prim = *iter;
                if (prim && prim.GetTypeName().GetString() == "Xform")
                    mAllPrims.push_back(prim);
            }
        }
    }

    for (auto& prim : mAllPrims)
    {
        pxr::UsdShadeMaterialBindingAPI materialBinding(prim);
        materialBinding.Bind(mColorMaterialShade, pxr::UsdShadeTokens->strongerThanDescendants);
    }
}
void DRComponentColor::onComponentChange()
{
    std::string primPaths;
    pxr::GfVec3f firstColor, secondColor;
    mOmniPBRMatPath = carb::tokens::resolveString(mTokens, "${kit}/../../library/mdl/Base/OmniPBR.mdl");

    mPrim.GetAttribute(pxr::TfToken("compName")).Get(&mCompName);
    mPrim.GetAttribute(pxr::TfToken("primPaths")).Get(&primPaths);
    mPrim.GetAttribute(pxr::TfToken("firstColor")).Get(&firstColor);
    mPrim.GetAttribute(pxr::TfToken("secondColor")).Get(&secondColor);
    mPrim.GetAttribute(pxr::TfToken("duration")).Get(&mRandomizationDurationInterval);
    mPrim.GetAttribute(pxr::TfToken("includeChildren")).Get(&mIncludeChild);

    boost::split(mPaths, primPaths, [](char c) { return c == ','; });
    mRRange[0] = firstColor[0];
    mRRange[1] = secondColor[0];
    mGRange[0] = firstColor[1];
    mGRange[1] = secondColor[1];
    mBRange[0] = firstColor[2];
    mBRange[1] = secondColor[2];
    update();
    CARB_LOG_WARN("Color Update: %s", mCompName.c_str());
}
void DRComponentColor::stop()
{
    CARB_LOG_INFO("DR Color Component Stopped");
    if (mStage && mColorLayer)
    {
        pxr::UsdEditContext context(mStage, mColorLayer);
        if (mColorMaterialPrim)
            omni::usd::UsdUtils::removePrim(mColorMaterialPrim);
        pxr::UsdPrim colorPrim =
            mStage->GetPrimAtPath(pxr::SdfPath(mStage->GetDefaultPrim().GetPath().GetString() + "/Colors"));
        if (colorPrim)
            if (colorPrim.GetChildren().empty())
                omni::usd::UsdUtils::removePrim(colorPrim);
    }
}
void DRComponentColor::tick(const float dt)
{
    for (auto& prim : mAllPrims)
    {
        if (mColorMaterialPrim.HasAttribute(pxr::TfToken("inputs:diffuse_color_constant")))
        {
            pxr::VtValue value;
            // CARB_LOG_WARN("prim with color: %s", prim.GetPrimPath().GetString().c_str());
            pxr::UsdAttribute primColor = mColorMaterialPrim.GetAttribute(pxr::TfToken("inputs:diffuse_color_constant"));
            if (primColor)
            {
                // CARB_LOG_WARN("prim set color");
                float r = randomRange(mRRange[0], mRRange[1]);
                float g = randomRange(mGRange[0], mGRange[1]);
                float b = randomRange(mBRange[0], mBRange[1]);
                pxr::GfVec3f usdColor{ pxr::GfVec3f(r, g, b) };
                primColor.Set(usdColor);
            }
        }
    }
}

}
}
}
