// Copyright (c) 2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentAttribute.h"

#include <carb/Framework.h>
#include <carb/InterfaceUtils.h>
#include <carb/Types.h>

#include <boost/algorithm/string.hpp>
#include <drSchema/attributeComponent.h>

namespace omni
{
namespace isaac
{
namespace dr
{

DRComponentAttribute::DRComponentAttribute() : DRComponentBase()
{
}
DRComponentAttribute::~DRComponentAttribute()
{
    stop();
}
void DRComponentAttribute::initialize(const pxr::DrSchemaAttributeComponent& prim, pxr::UsdStageWeakPtr stage)
{
    DRComponentBase::initialize(prim, stage);
}
void DRComponentAttribute::onStart()
{
    CARB_LOG_INFO("DR Attribute Component Started");
    onComponentChange();
}
void DRComponentAttribute::update()
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
    mAllAttributeParamsMap.clear();
    getCustomDataAsDictionary(mStage, mPrim.GetPath());
}
void DRComponentAttribute::onComponentChange()
{
    const pxr::DrSchemaAttributeComponent& attributePrim = (pxr::DrSchemaAttributeComponent)mPrim;
    attributePrim.GetCompNameAttr().Get(&mCompName);
    attributePrim.GetDurationAttr().Get(&mRandomizationDurationInterval);
    attributePrim.GetIncludeChildrenAttr().Get(&mIncludeChild);
    attributePrim.GetSeedAttr().Get(&mSeed);
    if (mCurrentSeed != mSeed)
    {
        mRandomGenerator.seed(mSeed);
        mCurrentSeed = mSeed;
    }

    mPaths.clear();
    pxr::UsdRelationship primPaths = attributePrim.GetPrimPathsRel();
    pxr::SdfPathVector targets;
    primPaths.GetTargets(&targets);
    for (auto target : targets)
        mPaths.push_back(target.GetString());

    update();
    CARB_LOG_INFO("Attribute Update: %s", mCompName.c_str());
}
void DRComponentAttribute::stop()
{
    CARB_LOG_INFO("DR Attribute Component Stopped");
}
void DRComponentAttribute::tick()
{
    for (auto& prim : mAllPrims)
    {
        if (prim)
        {
            // Randomized attribute parameters
            for (auto itr = mAllAttributeParamsMap.begin(); itr != mAllAttributeParamsMap.end(); itr++)
            {
                std::unordered_map<std::string, std::string> attributeParamMap = itr->second;
                std::string attributeName = attributeParamMap["name"];
                std::string distribution = attributeParamMap["distribution"];
                std::map<std::string, float> distributionParams;
                getDistributionParams(attributeParamMap, distributionParams);


                auto primVariantSets = prim.GetVariantSets();
                if (primVariantSets.HasVariantSet(attributeName))
                {
                    std::vector<std::string> variantNamesList;
                    std::string variantNames = attributeParamMap["variantNames"];
                    if (variantNames != "")
                        boost::split(variantNamesList, variantNames, [](char c) { return c == ','; });
                    auto primVariantSet = primVariantSets.GetVariantSet(attributeName);
                    if (variantNamesList.size() == 0)
                        variantNamesList = primVariantSet.GetVariantNames();
                    primVariantSet.SetVariantSelection(
                        variantNamesList[randomRangeInt(0, static_cast<int>(variantNamesList.size()) - 1)]);
                }
                else
                {
                    pxr::UsdAttribute attr = prim.GetAttribute(pxr::TfToken(attributeName.c_str()));
                    std::string attrTypeName = attr.GetTypeName().GetAsToken().GetString();
                    float index1 = randomFloat(distribution, distributionParams);
                    float index2 = randomFloat(distribution, distributionParams);
                    float index3 = randomFloat(distribution, distributionParams);
                    if (attrTypeName.find("3") != std::string::npos)
                    {
                        if (attrTypeName.find("3d") != std::string::npos ||
                            attrTypeName.find("double3") != std::string::npos)
                            attr.Set(pxr::GfVec3d(index1, index2, index3));
                        else if (attrTypeName.find("3f") != std::string::npos ||
                                 attrTypeName.find("float3") != std::string::npos)
                            attr.Set(pxr::GfVec3f(index1, index2, index3));
                    }
                    else if (attrTypeName.find("2") != std::string::npos)
                    {
                        if (attrTypeName.find("2d") != std::string::npos ||
                            attrTypeName.find("double2") != std::string::npos)
                            attr.Set(pxr::GfVec2d(index1, index2));
                        else if (attrTypeName.find("2f") != std::string::npos ||
                                 attrTypeName.find("float2") != std::string::npos)
                            attr.Set(pxr::GfVec2f(index1, index2));
                    }
                    else
                    {
                        attr.Set(index1);
                    }
                }
            }
        }
    }
}

}
}
}
