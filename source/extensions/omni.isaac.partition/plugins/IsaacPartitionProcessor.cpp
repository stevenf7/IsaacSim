// Copyright (c) 2018-2022, NVIDIA CORPORATION.  All rights reserved.
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

#include "IsaacPartitionProcessor.h"

using namespace carb;
using namespace omni;
using namespace isaac;
using namespace pxr;

namespace omni
{
namespace isaac
{
namespace
{
const std::string kShaderType{ "Shader" };
const std::string kMaterialType{ "Material" };

std::vector<UsdShadeMaterial> getMaterialBinding(const UsdPrim& usdPrim)
{
    std::vector<UsdShadeMaterial> materials{};

    if (const auto& materialBindingAPI = UsdShadeMaterialBindingAPI(usdPrim))
    {
        if (UsdShadeMaterial const& material = materialBindingAPI.ComputeBoundMaterial())
        {
            if (material && material.GetPrim())
            {
                materials.push_back(material);

                while (material.HasBaseMaterial())
                {
                    materials.push_back(material.GetBaseMaterial());
                }
            }
        }
    }
    else
    {
        // handle material through a direct binding rel search
        std::vector<UsdPrim> prims{};
        prims.push_back(usdPrim);

        for (const auto& material : UsdShadeMaterialBindingAPI::ComputeBoundMaterials(prims))
        {
            if (material && material.GetPrim())
            {
                materials.push_back(material);

                while (material.HasBaseMaterial())
                {
                    materials.push_back(material.GetBaseMaterial());
                }
            }
        }
    }

    return materials;
}

std::string removeExtension(std::string path)
{
    if (auto const lst = path.find_last_of('.'))
    {
        if (lst != std::string::npos)
        {
            path = path.erase(lst, path.size());
        }
    }

    return path;
}

std::string removePath(std::string path)
{
    do
    {
        for (const auto c : std::array<char, 2>{ '/', '\\' })
        {
            if (auto const lst = path.find_last_of(c))
            {
                if (lst != std::string::npos)
                {
                    path = path.erase(0, lst + 1);
                }
            }
        }
    } while (path.back() == '/' || path.back() == '\\');


    return path;
}

std::string getUsdObjectName(std::string path)
{
    return removeExtension(removePath(path));
}

class FrustumCulling
{
public:
    FrustumCulling() = delete;
    ~FrustumCulling() = default;

    FrustumCulling(const UsdStageRefPtr& stage, const std::string& camName)
    {
        if (stage != nullptr)
        {
            UsdGeomCamera camPrim{};

            // find the camera
            const UsdGeomCamera usdCamOrg(stage->GetPrimAtPath(SdfPath(camName)));
            if (usdCamOrg)
            {
                camPrim = usdCamOrg;
                mCamCamera = usdCamOrg.GetCamera(UsdTimeCode::Default());
                mCamFrustum = mCamCamera.GetFrustum();
            }
            else
            {
                if (auto primRange = stage->TraverseAll())
                {
                    for (auto iter = primRange.begin(); iter != primRange.end(); ++iter)
                    {
                        if (UsdPrim prim = *iter)
                        {
                            if (prim && prim.GetName() == camName)
                            {
                                const UsdGeomCamera usdCam(prim);
                                if (usdCam)
                                {
                                    camPrim = usdCam;
                                    mCamCamera = usdCam.GetCamera(UsdTimeCode::Default());
                                    mCamFrustum = mCamCamera.GetFrustum();
                                    break;
                                }
                            }
                        }
                    }
                }
            }

            // build and sort PrimNodes
            if (camPrim)
            {
                UsdGeomBBoxCache cacheBBox(UsdTimeCode::Default(), { UsdGeomTokens->default_ }, true, true);

                const auto viewPoint = mCamFrustum.ComputeLookAtPoint();

                const auto& primRange = stage->TraverseAll();
                for (auto iter = primRange.begin(); iter != primRange.end(); ++iter)
                {
                    if (const UsdPrim& prim = *iter)
                    {
                        UsdGeomMesh usdMesh(prim);
                        if (usdMesh)
                        {
                            const auto& primBounds = cacheBBox.ComputeWorldBound(usdMesh.GetPrim());
                            if (mCamFrustum.Intersects(primBounds))
                            {
                                mVisiblePrims.insert(prim.GetPrimPath());
                            }
                        }
                    }
                }
            }
        }
    }

    const std::set<SdfPath>& getPrims() const
    {
        return mVisiblePrims;
    }

    bool isVisible(const SdfPath& path)
    {
        return mVisiblePrims.find(path) != mVisiblePrims.end();
    }

    operator bool() const
    {
        return !mVisiblePrims.empty();
    }

    std::set<SdfPath> mVisiblePrims{};
    GfCamera mCamCamera{};
    GfFrustum mCamFrustum{};
};
} // namespace

void IsaacPartitionProcessor::setExportPath(const char* filePath)
{
    mExportFileName.clear();

    if (filePath != nullptr)
    {
        mExportFileName = std::string{ filePath };
    }
}

const char* IsaacPartitionProcessor::getExportPath()
{
    return mExportFileName.c_str();
}

void IsaacPartitionProcessor::clearCameras()
{
    mCameras.clear();
}

void IsaacPartitionProcessor::addCameraPath(const char* cameraPath)
{
    if (cameraPath != nullptr)
    {
        mCameras.emplace_back(cameraPath);
    }
}

size_t IsaacPartitionProcessor::numCameraPaths()
{
    return mCameras.size();
}

const char* IsaacPartitionProcessor::getCameraPath(size_t index)
{
    return index >= 0 && index < mCameras.size() ? mCameras[index].c_str() : "";
}

void IsaacPartitionProcessor::saveToUsd()
{
    CARB_PROFILE_ZONE(0, "PartitionProcessor::saveToUsd");

    if (mStageId == 0)
        return;

    auto originalStage = UsdUtilsStageCache::Get().Find(UsdStageCache::Id::FromLongInt(mStageId));
    if (!originalStage)
        return;

    // 1. copy the stage for each desired camera
    // 2. remove prims from each desired stage
    // 3. remove unused materials and other cameras
    // 4. keep list of removed prims to remove from the main stage

    // get final stage name.
    {
        originalStage->Export(getExportFileName(), false);

        for (const auto& cameraPath : mCameras)
        {
            originalStage->Export(getPartitionFileName(getUsdObjectName(cameraPath)), false);
        }
    }

    std::set<SdfPath> removeFromMain;

    for (size_t cameraIndex = 0; cameraIndex < mCameras.size(); ++cameraIndex)
    {
        const auto& cameraPath = mCameras[cameraIndex];
        const auto& camera = getUsdObjectName(cameraPath);

        const std::string subStageName = getPartitionFileName(camera);
        auto subStage = UsdStage::Open(subStageName);
        if (subStage)
        {
            std::set<SdfPath> keptPrims;
            std::set<SdfPath> prunedPrims;
            std::set<SdfPath> usedMaterials;
            std::set<SdfPath> removeMaterials;

            FrustumCulling vc(subStage, cameraPath);
            if (vc)
            {
                // check partitions vs geom
                const auto& primRange = subStage->TraverseAll();
                for (auto iter = primRange.begin(); iter != primRange.end(); ++iter)
                {
                    if (const auto& prim = *iter)
                    {
                        const auto& path = prim.GetPrimPath();
                        UsdGeomMesh usdMesh(prim);
                        if (usdMesh)
                        {
                            if (vc.isVisible(path))
                            {
                                // if we keep them here, we need to remove the prim from the main stage.
                                keptPrims.insert(path);
                                removeFromMain.insert(path);

                                // keep parent xform(s)
                                for (auto primParent = prim.GetParent();
                                     primParent && primParent != subStage->GetPseudoRoot() &&
                                     primParent != subStage->GetDefaultPrim();
                                     primParent = primParent.GetParent())
                                {
                                    if (UsdGeomXform(primParent))
                                    {
                                        keptPrims.insert(primParent.GetPrimPath());
                                    }
                                }

                                // keep mats
                                for (const auto& material : getMaterialBinding(prim))
                                {
                                    usedMaterials.insert(material.GetPath());
                                }
                            }
                            else
                            {
                                removeMaterials.insert(path);
                                prunedPrims.insert(path);

                                // keep parent xform(s)
                                for (auto primParent = prim.GetParent();
                                     primParent && primParent != subStage->GetPseudoRoot() &&
                                     primParent != subStage->GetDefaultPrim();
                                     primParent = primParent.GetParent())
                                {
                                    if (UsdGeomXform(primParent))
                                    {
                                        const auto& parentPath = primParent.GetPrimPath();
                                        removeMaterials.insert(parentPath);
                                        prunedPrims.insert(parentPath);
                                    }
                                }
                            }
                        }
                        else
                        {
                            removeMaterials.insert(path);
                        }
                    }
                }

                // dump all unused materials
                for (const auto& removed : removeMaterials)
                {
                    // remove prims that are stored in other layers.
                    if (const auto& prim = subStage->GetPrimAtPath(removed))
                    {
                        for (const auto& unusedMaterial : getMaterialBinding(prim))
                        {
                            // if not in used list, remove the mat.
                            const auto& materialPath = unusedMaterial.GetPath();
                            if (usedMaterials.find(materialPath) == usedMaterials.end())
                            {
                                subStage->RemovePrim(materialPath);
                            }
                        }

                        if (prim.GetTypeName() == kShaderType || prim.GetTypeName() == kMaterialType)
                        {
                            // if not in used list, remove the mat.
                            const auto& materialPath = prim.GetPath();
                            if (usedMaterials.find(materialPath) == usedMaterials.end())
                            {
                                subStage->RemovePrim(materialPath);
                            }
                        }
                    }
                }
            }

            // iterate over all prims and remove unused.
            for (const auto& unused : prunedPrims)
            {
                // xforms can be in the used and unused lists.  used list is stronger.
                if (keptPrims.find(unused) == keptPrims.end())
                {
                    // remove prims that are stored in other layers.
                    if (const auto& prim = subStage->GetPrimAtPath(unused))
                    {
                        subStage->RemovePrim(unused);
                    }
                }
            }

            //
            subStage->Save();
        }
    }

    // remove prims from the main stage and add sub layers.
    if (auto mainStage = UsdStage::Open(getExportFileName()))
    {
        // remove prims that are stored in other layers.
        for (const auto& removed : removeFromMain)
        {
            if (const UsdPrim& prim = mainStage->GetPrimAtPath(removed))
            {
                mainStage->RemovePrim(removed);
            }
        }

        // add layers
        const auto rootLayer = mainStage->GetRootLayer();
        for (const auto& cameraPath : mCameras)
        {
            rootLayer->InsertSubLayerPath(getPartitionFileName(getUsdObjectName(cameraPath)));
        }

        mainStage->Save();
    }
}

std::string IsaacPartitionProcessor::getPartitionFileName(const std::string& partition) const
{
    return removeExtension(getExportFileName()) + "_" + partition + "." + getExportExtension();
}

std::string IsaacPartitionProcessor::getExportFileName() const
{
    return mExportFileName.empty() ? getStageBaseFileName() : mExportFileName;
}

std::string IsaacPartitionProcessor::getExportExtension() const
{
    return std::string{ "usd" };
}

std::string IsaacPartitionProcessor::getStageBaseFileName() const
{
    std::string name{};

    if (mStageId == 0)
        return name;

    if (const pxr::UsdStagePtr stage = UsdUtilsStageCache::Get().Find(UsdStageCache::Id::FromLongInt(mStageId)))
    {
        if (const auto layer = stage->GetRootLayer())
        {
            name = layer->GetDisplayName();
        }
    }

    return name;
}
}
}
