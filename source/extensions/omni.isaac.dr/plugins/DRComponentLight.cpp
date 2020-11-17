// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentLight.h"

#include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <drSchema/lightComponent.h>

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
void DRComponentLight::initialize(const pxr::DrSchemaLightComponent& prim, pxr::UsdStageWeakPtr stage)
{
    DRComponentBase::initialize(prim, stage);
}
void DRComponentLight::onStart()
{
    CARB_LOG_INFO("DR Light Component Started");
    onComponentChange();
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
    pxr::GfVec3f firstColor, secondColor;

    const pxr::DrSchemaLightComponent& lightPrim = (pxr::DrSchemaLightComponent)mPrim;
    lightPrim.GetCompNameAttr().Get(&mCompName);
    lightPrim.GetFirstColorAttr().Get(&firstColor);
    lightPrim.GetSecondColorAttr().Get(&secondColor);
    lightPrim.GetIntensityRangeAttr().Get(&mLiRange);
    lightPrim.GetTemperatureRangeAttr().Get(&mLtRange);
    lightPrim.GetEnableTemperatureAttr().Get(&mEnableColorTemperature);
    lightPrim.GetDurationAttr().Get(&mRandomizationDurationInterval);
    lightPrim.GetIncludeChildrenAttr().Get(&mIncludeChild);
    lightPrim.GetSeedAttr().Get(&mSeed);
    if (mCurrentSeed != mSeed)
    {
        mRandomGenerator.seed(mSeed);
        mCurrentSeed = mSeed;
    }

    mPaths.clear();
    pxr::UsdRelationship primPaths = lightPrim.GetPrimPathsRel();
    pxr::SdfPathVector targets;
    primPaths.GetTargets(&targets);
    for (auto target : targets)
        mPaths.push_back(target.GetString());
    mLrRange[0] = firstColor[0];
    mLrRange[1] = secondColor[0];
    mLgRange[0] = firstColor[1];
    mLgRange[1] = secondColor[1];
    mLbRange[0] = firstColor[2];
    mLbRange[1] = secondColor[2];
    update();
    CARB_LOG_INFO("Light Update: %s", mCompName.c_str());
}
void DRComponentLight::stop()
{
    CARB_LOG_INFO("DR Light Component Stopped");
}
void DRComponentLight::tick()
{
    for (auto& prim : mAllPrims)
    {
        if (prim)
        {
            // Randomized Light color parameters
            pxr::UsdAttribute primColor = prim.GetAttribute(pxr::TfToken("color"));
            if (primColor)
            {
                float r = randomRangeFloat(mLrRange[0], mLrRange[1]);
                float g = randomRangeFloat(mLgRange[0], mLgRange[1]);
                float b = randomRangeFloat(mLbRange[0], mLbRange[1]);
                pxr::GfVec3f usdColor(r, g, b);
                primColor.Set(usdColor);
            }

            // Randomized Light intensity parameters
            pxr::UsdAttribute primIntensity = prim.GetAttribute(pxr::TfToken("intensity"));
            if (primIntensity)
            {
                float i = randomRangeFloat(mLiRange[0], mLiRange[1]);
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
                    float t = randomRangeFloat(mLtRange[0], mLtRange[1]);
                    primColorTemperature.Set(t);
                }
            }
        }
    }
}

}
}
}
