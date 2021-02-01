// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
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

#include "DRComponentVisibility.h"

#include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/InterfaceUtils.h>
#include <carb/filesystem/IFileSystem.h>
#include <drSchema/visibilityComponent.h>

#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

namespace omni
{
namespace isaac
{
namespace dr
{

DRComponentVisibility::DRComponentVisibility() : DRComponentBase()
{
}
DRComponentVisibility::~DRComponentVisibility()
{
    stop();
}
void DRComponentVisibility::initialize(const pxr::DrSchemaVisibilityComponent& prim, pxr::UsdStageWeakPtr stage)
{
    DRComponentBase::initialize(prim, stage);
}
void DRComponentVisibility::onStart()
{
    CARB_LOG_INFO("DR Visibility Component Started");
    onComponentChange();
}
void DRComponentVisibility::update()
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
void DRComponentVisibility::onComponentChange()
{
    const pxr::DrSchemaVisibilityComponent& visibilityPrim = (pxr::DrSchemaVisibilityComponent)mPrim;
    visibilityPrim.GetCompNameAttr().Get(&mCompName);
    visibilityPrim.GetNumVisibleRangeAttr().Get(&mNumVisibleRange);
    visibilityPrim.GetDurationAttr().Get(&mRandomizationDurationInterval);
    visibilityPrim.GetIncludeChildrenAttr().Get(&mIncludeChild);
    visibilityPrim.GetSeedAttr().Get(&mSeed);
    if (mCurrentSeed != mSeed)
    {
        mRandomGenerator.seed(mSeed);
        mCurrentSeed = mSeed;
    }

    mPaths.clear();
    pxr::UsdRelationship primPaths = visibilityPrim.GetPrimPathsRel();
    pxr::SdfPathVector targets;
    primPaths.GetTargets(&targets);
    for (auto target : targets)
        mPaths.push_back(target.GetString());

    update();
    CARB_LOG_INFO("Visibility Update: %s", mCompName.c_str());
}
void DRComponentVisibility::stop()
{
    CARB_LOG_INFO("DR Visibility Component Stopped");
}
void DRComponentVisibility::tick()
{
    int numVisible = randomRangeInt(mNumVisibleRange[0], mNumVisibleRange[1]);
    if (mNumVisibleRange[0] > mNumVisibleRange[1])
        numVisible = randomRangeInt(mNumVisibleRange[1], mNumVisibleRange[0]);
    int countVisible = 0;

    auto rng = std::default_random_engine{};
    std::shuffle(mAllPrims.begin(), mAllPrims.end(), rng);

    for (auto& prim : mAllPrims)
    {
        if (prim)
        {
            if (countVisible < numVisible)
            {
                omni::usd::UsdUtils::setPrimVisibility(prim, true);
                countVisible++;
            }
            else
                omni::usd::UsdUtils::setPrimVisibility(prim, false);
        }
    }
}

}
}
}
