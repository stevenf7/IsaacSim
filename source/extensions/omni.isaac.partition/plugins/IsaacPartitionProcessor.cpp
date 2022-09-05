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

#include <carb/profiler/Profile.h>


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

bool removePrim(const UsdPrim& prim)
{
    const auto stage{ prim.GetStage() };

    if (stage->HasDefaultPrim() && stage->GetDefaultPrim() == prim)
    {
        return false;
    }

    if (stage->GetPseudoRoot() == prim)
    {
        return false;
    }

    bool ret{ false };
    const auto primStack = prim.GetPrimStack();
    for (auto& primSpec : primStack)
    {
        const auto layer = primSpec->GetLayer();

        SdfBatchNamespaceEdit nsEdits;
        nsEdits.Add(SdfNamespaceEdit::Remove(primSpec->GetPath()));
        ret |= layer->Apply(nsEdits);
    }

    if (!ret)
    {
        stage->RemovePrim(prim.GetPrimPath());
    }

    return ret;
}


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

std::string cleanPath(std::string path)
{
    for (const auto& c : std::array<std::string, 2>{ "//", "\\\\" })
    {
        auto const fst = path.find(c);
        auto const lst = path.find(c, fst + 1);

        if (lst != std::string::npos && fst != std::string::npos && lst != fst)
        {
            path = path.erase(lst, 1);
        }
    }

    return path;
}

std::string removeExtension(std::string path)
{
    auto const ext = path.find_last_of('.');
    if (ext != std::string::npos)
    {
        path = path.erase(ext, path.size());
    }

    return path;
}

std::string getExtension(std::string path)
{
    auto const lst = path.find_last_of('.');
    if (lst != std::string::npos)
    {
        path = path.erase(0, lst);
    }

    return path;
}

std::string removePath(std::string path)
{
    for (const auto c : std::array<char, 2>{ '/', '\\' })
    {
        auto const lst = path.find_last_of(c);
        if (lst != std::string::npos)
        {
            path = path.erase(0, lst + 1);
        }
    }

    path = cleanPath(path);

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

    bool isVisible(const SdfPath& path) const
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
        mExportFileName = cleanPath(filePath);
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

    // Export the partitioned stage and sub-layers.
    {
        originalStage->Export(getExportFileName());

        for (const auto& cameraPath : mCameras)
        {
            originalStage->Export(getPartitionFileName(cameraPath), false);
        }
    }

    std::set<SdfPath> removeInMain{};

    // For each camera, remove primitives that are not within the view frustum.
    for (size_t cameraIndex = 0; cameraIndex < mCameras.size(); ++cameraIndex)
    {
        const auto& cameraPath = mCameras[cameraIndex];
        const auto& camera = getUsdObjectName(cameraPath);
        const std::string subStageName = getPartitionFileName(camera);

        auto subStage = UsdStage::Open(subStageName);
        if (subStage)
        {
            FrustumCulling const vc(subStage, cameraPath);
            if (vc)
            {
                std::set<SdfPath> keptPrims{};
                std::set<SdfPath> keptMaterials{};

                std::set<SdfPath> removedPrims;
                std::set<SdfPath> removedMaterials;

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
                                // Keep prims from the current sublayer and remove them in main stage.
                                keptPrims.insert(path);
                                removeInMain.insert(path);

                                // Keep parent xform(s)
                                for (auto primParent = prim.GetParent();
                                     primParent && primParent != subStage->GetPseudoRoot() &&
                                     primParent != subStage->GetDefaultPrim();
                                     primParent = primParent.GetParent())
                                {
                                    if (UsdGeomXform(primParent))
                                    {
                                        keptPrims.insert(primParent.GetPrimPath());
                                        removeInMain.insert(primParent.GetPrimPath());
                                    }
                                }

                                // keep mats
                                for (const auto& materials : getMaterialBinding(prim))
                                {
                                    keptMaterials.insert(materials.GetPath());
                                    removeInMain.insert(materials.GetPath());
                                }
                            }
                            else
                            {
                                removedPrims.insert(path);

                                // keep parent xform(s)
                                for (auto primParent = prim.GetParent();
                                     primParent && primParent != subStage->GetPseudoRoot() &&
                                     primParent != subStage->GetDefaultPrim();
                                     primParent = primParent.GetParent())
                                {
                                    if (UsdGeomXform(primParent))
                                    {
                                        removedPrims.insert(primParent.GetPath());
                                    }
                                }

                                // keep mats
                                for (const auto& material : getMaterialBinding(prim))
                                {
                                    removedMaterials.insert(material.GetPath());
                                }
                            }
                        }
                        else
                        {
                            // Remove all additional materials.
                            for (const auto& material : getMaterialBinding(prim))
                            {
                                removedMaterials.insert(material.GetPath());
                            }
                        }
                    }
                }

                for (const auto& material : removedMaterials)
                {
                    if (keptMaterials.find(material) == keptMaterials.end())
                    {
                        if (const auto& prim = subStage->GetPrimAtPath(material))
                        {
                            if (prim.GetTypeName() == kShaderType || prim.GetTypeName() == kMaterialType)
                            {
                                removePrim(prim);
                            }
                        }
                    }
                }

                for (const auto& unused : removedPrims)
                {
                    if (keptPrims.find(unused) == keptPrims.end())
                    {
                        if (const auto& prim = subStage->GetPrimAtPath(unused))
                        {
                            removePrim(prim);
                        }
                    }
                }

                //
                subStage->Save();
            }
        }
    }

    // remove prims from the main stage and add sub layers.
    auto const& mainStageName{ getExportFileName() };
    if (auto mainStage = UsdStage::Open(mainStageName))
    {
        for (auto const& primPath : removeInMain)
        {
            auto const& prim = mainStage->GetPrimAtPath(primPath);
            if (prim)
            {
                if (UsdGeomXform(prim) || UsdGeomMesh(prim))
                {
                    removePrim(prim);
                }
            }
        }

        // save to store the current prims.
        mainStage->Save();

        // add layers after save.
        const auto rootLayer = mainStage->GetRootLayer();
        for (const auto& cameraPath : mCameras)
        {
            rootLayer->InsertSubLayerPath(getPartitionFileName(cameraPath));
            mainStage->SaveSessionLayers();
        }

        // save the results.
        mainStage->Save();
    }
}

std::string IsaacPartitionProcessor::getPartitionFileName(const std::string& partition) const
{
    return removeExtension(getExportFileName()) + "_" + getUsdObjectName(partition) + getExportExtension();
}

std::string IsaacPartitionProcessor::getExportFileName() const
{
    return mExportFileName;
}

std::string IsaacPartitionProcessor::getExportExtension() const
{
    return getExtension(mExportFileName);
}
}
}
