// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once


// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "../parse/UrdfParser.h"
#include "KinematicChain.h"
#include "MeshImporter.h"

#include <carb/logging/Log.h>

#include <omni/isaac/math/core/maths.h>
#include <omni/isaac/urdf/Urdf.h>
#include <omni/isaac/urdf/UrdfTypes.h>
#include <physicsSchemaTools/UsdTools.h>
#include <physxSchema/physxSceneAPI.h>
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

namespace omni
{
namespace isaac
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
    std::map<pxr::TfToken, std::string> materialsList;

public:
    UrdfImporter(const std::string& assetRoot, const std::string& urdfPath, const ImportConfig& options)
        : assetRoot_(assetRoot), urdfPath_(urdfPath), config(options)
    {
    }

    // Creates and populates a GymAsset
    UrdfRobot createAsset();

    std::string addToStage(pxr::UsdStageWeakPtr stage, const UrdfRobot& robot);


private:
    void buildInstanceableStage(pxr::UsdStageRefPtr stage,
                                const KinematicChain::Node* parentNode,
                                const std::string& robotBasePath,
                                const UrdfRobot& urdfRobot);
    void addInstanceableMeshes(pxr::UsdStageRefPtr stage,
                               const UrdfLink& link,
                               const std::string& robotBasePath,
                               const UrdfRobot& robot);
    void addRigidBody(pxr::UsdStageWeakPtr stage,
                      const UrdfLink& link,
                      const Transform& poseBodyToWorld,
                      pxr::UsdGeomXform robotPrim,
                      const UrdfRobot& robot);
    void addJoint(pxr::UsdStageWeakPtr stage,
                  pxr::UsdGeomXform robotPrim,
                  const UrdfJoint& joint,
                  const Transform& poseJointToParentBody);
    void addLinksAndJoints(pxr::UsdStageWeakPtr stage,
                           const Transform& poseParentToWorld,
                           const KinematicChain::Node* parentNode,
                           const UrdfRobot& robot,
                           pxr::UsdGeomXform robotPrim);
    void addMaterials(pxr::UsdStageWeakPtr stage, const UrdfRobot& robot, const pxr::SdfPath& prefixPath);
    pxr::UsdShadeMaterial addMaterial(pxr::UsdStageWeakPtr stage,
                                      const std::pair<std::string, UrdfMaterial>& mat,
                                      const pxr::SdfPath& prefixPath);
};
}
}
}
