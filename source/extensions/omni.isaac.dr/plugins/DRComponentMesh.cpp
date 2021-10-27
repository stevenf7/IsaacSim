// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
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

#include "DRComponentMesh.h"

#include <carb/Framework.h>
#include <carb/InterfaceUtils.h>
#include <carb/Types.h>
#include <carb/filesystem/IFileSystem.h>

#include <boost/algorithm/string.hpp>
#include <drSchema/scaleComponent.h>

namespace omni
{
namespace isaac
{
namespace dr
{

DRComponentMesh::DRComponentMesh() : DRComponentBase()
{
}
DRComponentMesh::~DRComponentMesh()
{
    stop();
}
void DRComponentMesh::initialize(const pxr::DrSchemaMeshComponent& prim, pxr::UsdStageWeakPtr stage)
{
    DRComponentBase::initialize(prim, stage);
}
void DRComponentMesh::onStart()
{
    CARB_LOG_INFO("DR Mesh Component Started");
    onComponentChange();
    update();
}
void DRComponentMesh::update()
{

    unsigned int numMesh = randomRangeInt(mNumMeshRange[0], mNumMeshRange[1]);
    // CARB_LOG_WARN("Num Meshes: %d", numMesh);
    if (numMesh <= 0)
        return;

    for (unsigned int i = 0; i < mMeshList.size(); i++)
    {
        // Load main mesh
        carb::extras::Path urlPath(mMeshList[i].c_str());
        std::string meshPrimPath = mParentPrimPath.GetString() + "/mesh_" + urlPath.getStem().getString();
        // CARB_LOG_WARN("Loading main mesh: %s", meshPrimPath.c_str());
        if (!omni::usd::UsdUtils::hasPrimAtPath(mStage, meshPrimPath))
        {
            std::string mUsdAsset = mMeshList[i];
            carb::extras::Path mUsdAssetPath(mUsdAsset);
            std::string warningMsg;
            auto prim = omni::usd::UsdUtils::createExternalRefNodeAtPath(
                mStage, mUsdAsset.c_str(), meshPrimPath.c_str(), warningMsg, false);
            mMeshPrims.push_back(prim);
            mCopiedMeshPrims[meshPrimPath] = {};
        }
        // Make new mesh copies
        if (numMesh > mCopiedMeshPrims[meshPrimPath].size() + 1)
        {
            for (unsigned int meshId = 1; meshId < numMesh; meshId++)
            {
                std::string copyMeshPrimPath = meshPrimPath + "_" + std::to_string(meshId + 1);
                if (!omni::usd::UsdUtils::hasPrimAtPath(mStage, copyMeshPrimPath))
                {
                    auto newPrim = omni::usd::UsdUtils::copyPrim(mMeshPrims[i], nullptr, false, false);
                    // CARB_LOG_WARN("Adding : %s", newPrim.GetPrimPath().GetString().c_str());
                    mCopiedMeshPrims[meshPrimPath].push_back(newPrim);
                }
                else
                {
                    auto newPrim = mStage->GetPrimAtPath(pxr::SdfPath(copyMeshPrimPath));
                    if (!omni::usd::UsdUtils::isPrimVisible(newPrim))
                    {
                        // CARB_LOG_WARN("Setting visibility to true : %s", copyMeshPrimPath.c_str());
                        omni::usd::UsdUtils::setPrimVisibility(newPrim, true);
                        mCopiedMeshPrims[meshPrimPath].push_back(newPrim);
                    }
                }
            }
        }
        // Or make the extra ones invisible
        else if (numMesh < mCopiedMeshPrims[meshPrimPath].size() + 1)
        {
            size_t numMeshDelete = mCopiedMeshPrims[meshPrimPath].size() + 1 - numMesh;
            for (size_t idx = 1; idx <= numMeshDelete; idx++)
            {
                auto newPrim = mCopiedMeshPrims[meshPrimPath].back();
                // CARB_LOG_WARN("Setting visibility to false : %s", newPrim.GetPrimPath().GetString().c_str());
                omni::usd::UsdUtils::setPrimVisibility(newPrim, false);
                mCopiedMeshPrims[meshPrimPath].pop_back();
            }
        }
    }
}
void DRComponentMesh::onComponentChange()
{
    std::string meshList;

    const pxr::DrSchemaMeshComponent& meshPrim = (pxr::DrSchemaMeshComponent)mPrim;
    meshPrim.GetCompNameAttr().Get(&mCompName);
    meshPrim.GetMeshListAttr().Get(&meshList);
    meshPrim.GetNumMeshRangeAttr().Get(&mNumMeshRange);
    meshPrim.GetDurationAttr().Get(&mRandomizationDurationInterval);
    meshPrim.GetSeedAttr().Get(&mSeed);

    pxr::SdfPathVector targets;
    meshPrim.GetParentPrimRel().GetTargets(&targets);
    if (targets.size() > 0)
    {
        mParentPrimPath = targets[0];
    }
    else
    {
        mParentPrimPath = mPrim.GetPath();
        CARB_LOG_WARN("ParentPrimRel should be specified. using %s by default", mParentPrimPath.GetString().c_str());
    }
    mParentPrim = mStage->GetPrimAtPath(mParentPrimPath);
    if (mCurrentSeed != mSeed)
    {
        mRandomGenerator.seed(mSeed);
        mCurrentSeed = mSeed;
    }

    if (meshList != "")
        boost::split(mMeshList, meshList, [](char c) { return c == ','; });


    CARB_LOG_INFO("Mesh Update: %s", mCompName.c_str());
}
void DRComponentMesh::stop()
{
    CARB_LOG_INFO("DR Mesh Component Stopped");
    if (mStage)
    {
        // Remove copied mesh instances
        for (auto copiedMeshPrims : mCopiedMeshPrims)
        {
            if (!copiedMeshPrims.second.empty())
                for (auto copiedMeshPrim : copiedMeshPrims.second)
                    omni::usd::UsdUtils::removePrim(copiedMeshPrim);
        }
        // Remove base mesh
        for (auto baseMeshPrim : mMeshPrims)
        {
            if (baseMeshPrim)
                omni::usd::UsdUtils::removePrim(baseMeshPrim);
        }
        // Remove component level Mesh prim
        pxr::UsdPrim meshCompPrim = mStage->GetPrimAtPath(pxr::SdfPath(appendPathToDrScope(mCompName)));
        if (meshCompPrim)
            omni::usd::UsdUtils::removePrim(meshCompPrim);
    }

    mMeshPrims.clear();
    mCopiedMeshPrims.clear();
    mAllPrims.clear();
}
void DRComponentMesh::tick()
{
}

}
}
}
