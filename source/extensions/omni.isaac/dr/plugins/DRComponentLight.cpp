// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentLight.h"

#include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/Types.h>

namespace omni
{
namespace isaac
{
namespace dr
{

DRComponentLight::DRComponentLight() : DRComponentBase()
{
    mLrRange.push_back(1);
    mLrRange.push_back(1);
    mLgRange.push_back(1);
    mLgRange.push_back(1);
    mLbRange.push_back(1);
    mLbRange.push_back(1);
    mEnableColorTemperature = false;
}
DRComponentLight::~DRComponentLight()
{
    stop();
}
void DRComponentLight::onStart()
{
    CARB_LOG_INFO("DR Light Component Started");
}
void DRComponentLight::update()
{
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
                mAllPrims.push_back(prim);
            }
        }
    }
}
void DRComponentLight::onComponentChange()
{
    std::string primPaths;
    pxr::GfVec3f firstColor, secondColor;

    mPrim.GetAttribute(pxr::TfToken("compName")).Get(&mCompName);
    mPrim.GetAttribute(pxr::TfToken("primPaths")).Get(&primPaths);
    mPrim.GetAttribute(pxr::TfToken("firstColor")).Get(&firstColor);
    mPrim.GetAttribute(pxr::TfToken("secondColor")).Get(&secondColor);
    mPrim.GetAttribute(pxr::TfToken("intensityRange")).Get(&mLiRange);
    mPrim.GetAttribute(pxr::TfToken("temperatureRange")).Get(&mLtRange);
    mPrim.GetAttribute(pxr::TfToken("enableTemperature")).Get(&mEnableColorTemperature);
    mPrim.GetAttribute(pxr::TfToken("duration")).Get(&mRandomizationDurationInterval);
    mPrim.GetAttribute(pxr::TfToken("includeChildren")).Get(&mIncludeChild);

    boost::split(mPaths, primPaths, [](char c) { return c == ','; });
    mLrRange[0] = firstColor[0];
    mLrRange[1] = secondColor[0];
    mLgRange[0] = firstColor[1];
    mLgRange[1] = secondColor[1];
    mLbRange[0] = firstColor[2];
    mLbRange[1] = secondColor[2];
    update();
    CARB_LOG_WARN("Light Update: %s", mCompName.c_str());
}
void DRComponentLight::stop()
{
    CARB_LOG_INFO("DR Light Component Stopped");
}
void DRComponentLight::tick(const float dt)
{
    for (auto& prim : mAllPrims)
    {
        if (prim)
        {
            // Randomized Light color parameters
            pxr::UsdAttribute primColor = prim.GetAttribute(pxr::TfToken("color"));
            if (primColor)
            {
                float r = randomRange(mLrRange[0], mLrRange[1]);
                float g = randomRange(mLgRange[0], mLgRange[1]);
                float b = randomRange(mLbRange[0], mLbRange[1]);
                pxr::GfVec3f usdColor(r, g, b);
                primColor.Set(usdColor);
            }

            // Randomized Light intensity parameters
            pxr::UsdAttribute primIntensity = prim.GetAttribute(pxr::TfToken("intensity"));
            if (primIntensity)
            {
                float i = randomRange(mLiRange[0], mLiRange[1]);
                primIntensity.Set(i);
            }

            // Randomized Light color temperature parameters
            pxr::UsdAttribute primEnableColorTemperature = prim.GetAttribute(pxr::TfToken("enableColorTemperature"));
            if (primEnableColorTemperature)
                primEnableColorTemperature.Set(mEnableColorTemperature);
            if (mEnableColorTemperature)
            {
                pxr::UsdAttribute primColorTemperature = prim.GetAttribute(pxr::TfToken("colorTemperature"));
                if (primColorTemperature)
                {
                    float t = randomRange(mLtRange[0], mLtRange[1]);
                    primColorTemperature.Set(t);
                }
            }
        }
    }
}

}
}
}
