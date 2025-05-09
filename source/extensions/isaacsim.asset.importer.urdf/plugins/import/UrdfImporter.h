// SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#pragma once


// clang-format off
#include "../UsdPCH.h"
// clang-format on

#include "../Urdf.h"
#include "../UrdfTypes.h"
#include "../math/core/maths.h"
#include "../parse/UrdfParser.h"
#include "KinematicChain.h"
#include "MeshImporter.h"

#include <carb/logging/Log.h>

#include <pxr/usd/usdPhysics/articulationRootAPI.h>
#include <pxr/usd/usdPhysics/collisionAPI.h>
#include <pxr/usd/usdPhysics/driveAPI.h>
#include <pxr/usd/usdPhysics/fixedJoint.h>
#include <pxr/usd/usdPhysics/joint.h>
#include <pxr/usd/usdPhysics/limitAPI.h>
#include <pxr/usd/usdPhysics/massAPI.h>
#include <pxr/usd/usdPhysics/prismaticJoint.h>
#include <pxr/usd/usdPhysics/revoluteJoint.h>
#include <pxr/usd/usdPhysics/scene.h>
#include <pxr/usd/usdPhysics/sphericalJoint.h>

namespace isaacsim
{
namespace asset
{
namespace importer
{
namespace urdf
{
class UrdfImporter
{
private:
    std::string assetRoot_;
    std::string urdfPath_;
    const ImportConfig config;
    std::map<std::string, std::string> matPrimPaths;
    std::map<pxr::TfToken, pxr::SdfPath> meshPaths;
    std::map<pxr::TfToken, pxr::SdfPath> materialPaths;

public:
    UrdfImporter(const std::string& assetRoot, const std::string& urdfPath, const ImportConfig& options)
        : assetRoot_(assetRoot), urdfPath_(urdfPath), config(options)
    {
    }

    // Creates and populates a GymAsset
    UrdfRobot createAsset();

    std::string addToStage(std::unordered_map<std::string, pxr::UsdStageRefPtr>,
                           const UrdfRobot& robot,
                           const bool getArticulationRoot);


private:
    void addRigidBody(std::unordered_map<std::string, pxr::UsdStageRefPtr>,
                      const UrdfLink& link,
                      const Transform& poseBodyToWorld,
                      pxr::UsdGeomXform robotPrim,
                      const UrdfRobot& robot);
    void addJoint(std::unordered_map<std::string, pxr::UsdStageRefPtr>,
                  pxr::UsdGeomXform robotPrim,
                  const UrdfJoint& joint,
                  const Transform& poseJointToParentBody);
    void addLoopJoints(std::unordered_map<std::string, pxr::UsdStageRefPtr> stages,
                       pxr::UsdGeomXform robotPrim,
                       const UrdfRobot& robot,
                       const ImportConfig& config);
    void addLinksAndJoints(std::unordered_map<std::string, pxr::UsdStageRefPtr>,
                           const Transform& poseParentToWorld,
                           const KinematicChain::Node* parentNode,
                           const UrdfRobot& robot,
                           pxr::UsdGeomXform robotPrim);
    void addMergedChildren(std::unordered_map<std::string, pxr::UsdStageRefPtr> stages,
                           const UrdfLink& link,
                           const pxr::UsdPrim& parentPrim,
                           const UrdfRobot& robot);
    void addMaterials(pxr::UsdStageWeakPtr stage, const UrdfRobot& robot, const pxr::SdfPath& prefixPath);
    pxr::UsdShadeMaterial addMaterial(pxr::UsdStageWeakPtr stage,
                                      const std::pair<std::string, UrdfMaterial>& mat,
                                      const pxr::SdfPath& prefixPath);
};
}
}
}
}
