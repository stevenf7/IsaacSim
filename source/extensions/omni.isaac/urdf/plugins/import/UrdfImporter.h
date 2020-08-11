// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once


// clang-format off
#include "UsdPCH.h"
// clang-format on

#include <PhysicsSchema/articulationAPI.h>
#include <PhysicsSchema/articulationJointAPI.h>
#include <PhysicsSchema/collisionAPI.h>
#include <PhysicsSchema/driveAPI.h>
#include <PhysicsSchema/physicsJoint.h>
#include <PhysicsSchema/limitAPI.h>
#include <PhysicsSchema/massAPI.h>
#include <PhysicsSchema/physicsScene.h>
#include <PhysicsSchema/fixedPhysicsJoint.h>
#include <PhysicsSchema/prismaticPhysicsJoint.h>
#include <PhysicsSchema/revolutePhysicsJoint.h>
#include <PhysicsSchema/sphericalPhysicsJoint.h>
#include <PhysicsSchemaTools/UsdTools.h>

#include <PhysxSchema/physxMeshCollisionAPI.h>
#include <PhysxSchema/physxSceneAPI.h>


#include "../parse/UrdfParser.h"
#include "KinematicChain.h"
#include <omni/isaac/urdf/UrdfTypes.h>
#include "../core/maths.h"
#include "MeshImporter.h"
#include <carb/logging/Log.h>

namespace omni
{
namespace isaac
{
namespace urdf
{
struct GymAssetOptions
{
    // TODO: Refactor to SwitchMeshesCoordinateSystem or something similar (also :shouldn't this be for both visual and
    // collision meshes?)
    bool flipVisualAttachments = false; //!< Switch Meshes from Z-up left-handed system to Y-up Right-handed coordinate
                                        //!< system.
    bool fixBaseLink = false; //!< Set Asset base to a fixed placement upon import.


    float density = 1000.f; //!< Default density parameter used for calculating mass and inertia tensor when no mass and
                            //!< inertia data are provided, in $kg/m^3$.

    // Angular damping and max angular velocity parameters for rigid bodies
    float angularDamping = 0.75f; //!< Angular velocity damping for rigid bodies
    float maxAngularVelocity = 60.f; //!< Maximum angular velocity for rigid bodies. In $rad/s$.

    // Linear damping and linear velocity parameters for rigid bodies
    float linearDamping = 0.0f; //!< Linear velocity damping for rigid bodies.
    float maxLinearVelocity = 1000.0f; //!< Maximum Linear velocity for rigid bodies. In $m/s$.

    float armature = 0.0f; //!< Additional moment of inertia caused by the armature of the motors.

    float thickness = 0.01f; //!< Thickness of the collision shapes. Sets how far objects should come to rest from the
                             //!< surface of this body

    // TODO Reconcile

    // Collisions
    bool replaceCylinderWithCapsule = false; //!< flag to replace Cylinders with capsules for additional performance.

    // Cylinder mesh
    int slicesPerCylinder = 20; //!< Number of faces on generated cylinder mesh, excluding top and bottom.

    // Joints
    int defaultDofDriveMode = 0; //!< Default mode used to actuate Asset joints. See GymDofDriveModeFlags.

    // Mesh parameters
    bool useObj = true; //!< Flag used to indicate if the mesh used should be loaded from an obj file.

    // Merge links that are connected by fixed joints
    bool collapseFixedJoints = false; //!< Merge links that are connected by fixed joints.

    bool disableGravity = false; //!< Disables gravity for asset.

    float minParticleMass = 0.0001f; //!< Minimum mass for particles in soft bodies, in Kg
};


class UrdfImporter
{
private:
    std::string assetRoot_;
    std::string urdfPath_;
    const GymAssetOptions options_;

public:
    UrdfImporter(const std::string& assetRoot, const std::string& urdfPath, const GymAssetOptions& options)
        : assetRoot_(assetRoot), urdfPath_(urdfPath), options_(options)
    {
    }

    // Creates and populates a GymAsset
    UrdfRobot createAsset();

    void addToStage(pxr::UsdStageWeakPtr stage, const UrdfRobot& robot);


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
};
}
}
}
