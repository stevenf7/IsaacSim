// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
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

#include <omni/isaac/urdf/Urdf.h>
#include <omni/isaac/urdf/UrdfTypes.h>
#include <omni/isaac/urdf/core/maths.h>
#include <physicsSchemaTools/UsdTools.h>
#include <physxSchema/physxSceneAPI.h>
#include <usdPhysics/articulationRootAPI.h>
#include <usdPhysics/collisionAPI.h>
#include <usdPhysics/driveAPI.h>
#include <usdPhysics/fixedJoint.h>
#include <usdPhysics/joint.h>
#include <usdPhysics/limitAPI.h>
#include <usdPhysics/massAPI.h>
#include <usdPhysics/prismaticJoint.h>
#include <usdPhysics/revoluteJoint.h>
#include <usdPhysics/scene.h>
#include <usdPhysics/sphericalJoint.h>

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

public:
    UrdfImporter(const std::string& assetRoot, const std::string& urdfPath, const ImportConfig& options)
        : assetRoot_(assetRoot), urdfPath_(urdfPath), config(options)
    {
    }

    // Creates and populates a GymAsset
    UrdfRobot createAsset();

    std::string addToStage(pxr::UsdStageWeakPtr stage, const UrdfRobot& robot);


private:
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
};
}
}
}
