// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentMesh.h"

#include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/InterfaceUtils.h>
#include <carb/filesystem/IFileSystem.h>
#include <DrSchema/scaleComponent.h>

#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

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
    // Get DR layer and switch USD context
    auto layers = mStage->GetLayerStack();
    for (auto&& layer : layers)
    {
        if (layer->GetIdentifier().find(mDRLayerName) != std::string::npos)
            mMeshLayer = layer;
    }
    if (mMeshLayer)
    {
        pxr::UsdEditContext context(mStage, mMeshLayer);
        // Check for /Meshes prim and if base OmniPBR material is loaded
        if (!omni::usd::UsdUtils::hasPrimAtPath(mStage, "/Meshes"))
        {
            omni::usd::UsdUtils::createPrim(mStage, "/Meshes", [](pxr::UsdStageWeakPtr mStage, const pxr::SdfPath& path) {
                return pxr::UsdGeomScope::Define(mStage, path).GetPrim();
            });
        }
        std::string meshCompPath = "/Meshes/" + mCompName;
        if (!omni::usd::UsdUtils::hasPrimAtPath(mStage, meshCompPath))
        {
            omni::usd::UsdUtils::createPrim(
                mStage, meshCompPath.c_str(), [](pxr::UsdStageWeakPtr mStage, const pxr::SdfPath& path) {
                    return pxr::UsdGeomScope::Define(mStage, path).GetPrim();
                });
        }
    }
    pxr::UsdEditTarget editTarget(mStage->GetRootLayer());
    mStage->SetEditTarget(editTarget);
    onComponentChange();
}
void DRComponentMesh::update()
{
    if (mMeshLayer)
    {
        pxr::UsdEditContext context(mStage, mMeshLayer);
        unsigned int numMesh = randomRangeInt(mNumMeshRange[0], mNumMeshRange[1]);
        // CARB_LOG_WARN("Num Meshes: %d", numMesh);
        if (numMesh <= 0)
            return;

        for (unsigned int i = 0; i < mMeshList.size(); i++)
        {
            // Load main mesh
            carb::extras::Path urlPath(mMeshList[i].c_str());
            std::string meshPrimPath = "/Meshes/" + mCompName + "/mesh_" + urlPath.getStem().getString();
            // CARB_LOG_WARN("Loading main mesh: %s", meshPrimPath.c_str());
            if (!omni::usd::UsdUtils::hasPrimAtPath(mStage, meshPrimPath))
            {
                std::string mUsdAsset = mMeshList[i];
                carb::extras::Path mUsdAssetPath(mUsdAsset);
                std::string warningMsg;
                auto prim = omni::usd::UsdUtils::createExternalRefNodeAtPath(
                    mStage, mUsdAsset.c_str(), meshPrimPath.c_str(), warningMsg);
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
                        auto newPrim = mStage->GetPrimAtPath(
                            pxr::SdfPath(mStage->GetDefaultPrim().GetPath().GetString() + copyMeshPrimPath));
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
                unsigned int numMeshDelete = mCopiedMeshPrims[meshPrimPath].size() + 1 - numMesh;
                for (unsigned int idx = 1; idx <= numMeshDelete; idx++)
                {
                    auto newPrim = mCopiedMeshPrims[meshPrimPath].back();
                    // CARB_LOG_WARN("Setting visibility to false : %s", newPrim.GetPrimPath().GetString().c_str());
                    omni::usd::UsdUtils::setPrimVisibility(newPrim, false);
                    mCopiedMeshPrims[meshPrimPath].pop_back();
                }
            }
        }
        pxr::UsdEditTarget editTarget(mStage->GetRootLayer());
        mStage->SetEditTarget(editTarget);
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
    meshPrim.GetIncludeChildrenAttr().Get(&mIncludeChild);

    if (meshList != "")
        boost::split(mMeshList, meshList, [](char c) { return c == ','; });

    update();
    CARB_LOG_INFO("Mesh Update: %s", mCompName.c_str());
}
void DRComponentMesh::stop()
{
    CARB_LOG_INFO("DR Mesh Component Stopped");
    if (mStage && mMeshLayer)
    {
        pxr::UsdEditContext context(mStage, mMeshLayer);
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
        pxr::UsdPrim meshCompPrim =
            mStage->GetPrimAtPath(pxr::SdfPath(mStage->GetDefaultPrim().GetPath().GetString() + "/Meshes/" + mCompName));
        if (meshCompPrim)
            omni::usd::UsdUtils::removePrim(meshCompPrim);
        // Remove top-level Mesh prim
        pxr::UsdPrim meshPrim =
            mStage->GetPrimAtPath(pxr::SdfPath(mStage->GetDefaultPrim().GetPath().GetString() + "/Meshes"));
        if (meshPrim && meshPrim.GetChildren().empty())
            omni::usd::UsdUtils::removePrim(meshPrim);
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
