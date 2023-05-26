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

// clang-format off
#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>
// clang-format on

#include "MjcfTypes.h"
#include "MjcfUtils.h"

#include <omni/isaac/math/core/maths.h>
#include <omni/isaac/mjcf/mjcf.h>
#include <physxSchema/jointStateAPI.h>
#include <physxSchema/physxArticulationAPI.h>
#include <physxSchema/physxJointAPI.h>
#include <physxSchema/physxLimitAPI.h>
#include <physxSchema/physxRigidBodyAPI.h>
#include <physxSchema/physxSceneAPI.h>
#include <physxSchema/physxTendonAttachmentAPI.h>
#include <physxSchema/physxTendonAttachmentLeafAPI.h>
#include <physxSchema/physxTendonAttachmentRootAPI.h>
#include <physxSchema/physxTendonAxisAPI.h>
#include <physxSchema/physxTendonAxisRootAPI.h>
#include <physxSchema/plane.h>
#include <usdPhysics/articulationRootAPI.h>
#include <usdPhysics/collisionAPI.h>
#include <usdPhysics/driveAPI.h>
#include <usdPhysics/filteredPairsAPI.h>
#include <usdPhysics/fixedJoint.h>
#include <usdPhysics/joint.h>
#include <usdPhysics/limitAPI.h>
#include <usdPhysics/massAPI.h>
#include <usdPhysics/meshCollisionAPI.h>
#include <usdPhysics/prismaticJoint.h>
#include <usdPhysics/revoluteJoint.h>
#include <usdPhysics/rigidBodyAPI.h>
#include <usdPhysics/scene.h>

#include <map>
#include <vector>

namespace omni
{
namespace isaac
{
namespace mjcf
{
pxr::SdfPath getNextFreePath(pxr::UsdStageWeakPtr stage, const pxr::SdfPath& primPath);

void setStageMetadata(pxr::UsdStageWeakPtr stage, const omni::isaac::mjcf::ImportConfig config);
void createRoot(pxr::UsdStageWeakPtr stage,
                Transform trans,
                const std::string rootPrimPath,
                const omni::isaac::mjcf::ImportConfig config);
void createFixedRoot(pxr::UsdStageWeakPtr stage, const std::string jointPath, const std::string bodyPath);
void applyArticulationAPI(pxr::UsdStageWeakPtr stage,
                          pxr::UsdGeomXformable prim,
                          const omni::isaac::mjcf::ImportConfig config);
pxr::UsdGeomMesh createMesh(
    pxr::UsdStageWeakPtr stage, const pxr::SdfPath path, Mesh* mesh, float scale, bool importMaterials, bool instanceable);
pxr::UsdGeomMesh createMesh(pxr::UsdStageWeakPtr stage,
                            const pxr::SdfPath path,
                            const std::vector<pxr::GfVec3f>& points,
                            const std::vector<pxr::GfVec3f>& normals,
                            const std::vector<int>& indices,
                            const std::vector<int>& vertexCounts);
void createAndBindMaterial(pxr::UsdStageWeakPtr stage,
                           pxr::UsdPrim prim,
                           MJCFMaterial* material,
                           MJCFTexture* texture,
                           Vec4& color,
                           bool colorOnly);
pxr::UsdGeomXformable createBody(pxr::UsdStageWeakPtr stage,
                                 const std::string primPath,
                                 const Transform& trans,
                                 const ImportConfig& config);
void applyRigidBody(pxr::UsdGeomXformable bodyPrim, const MJCFBody* body, const ImportConfig& config);
pxr::UsdPrim createPrimitiveGeom(pxr::UsdStageWeakPtr stage,
                                 const std::string geomPath,
                                 const MJCFGeom* geom,
                                 const std::map<std::string, MeshInfo>& simulationMeshCache,
                                 const ImportConfig& config,
                                 bool importMaterials,
                                 const std::string rootPrimPath,
                                 bool collisionGeom);
pxr::UsdPrim createPrimitiveGeom(pxr::UsdStageWeakPtr stage,
                                 const std::string geomPath,
                                 const MJCFSite* site,
                                 const ImportConfig& config,
                                 bool importMaterials);
void applyCollisionGeom(pxr::UsdStageWeakPtr stage, pxr::UsdPrim prim, const MJCFGeom* geom);
pxr::UsdPhysicsJoint createFixedJoint(pxr::UsdStageWeakPtr stage,
                                      const std::string jointPath,
                                      const Transform& poseJointToParentBody,
                                      const Transform& poseJointToChildBody,
                                      const std::string parentBodyPath,
                                      const std::string bodyPath,
                                      const ImportConfig& config);
pxr::UsdPhysicsJoint createD6Joint(pxr::UsdStageWeakPtr stage,
                                   const std::string jointPath,
                                   const Transform& poseJointToParentBody,
                                   const Transform& poseJointToChildBody,
                                   const std::string parentBodyPath,
                                   const std::string bodyPath,
                                   const ImportConfig& config);
void initPhysicsJoint(pxr::UsdPhysicsJoint& jointPrim,
                      const Transform& poseJointToParentBody,
                      const Transform& poseJointToChildBody,
                      const std::string parentBodyPath,
                      const std::string bodyPath,
                      const float& distanceScale);
void applyPhysxJoint(pxr::UsdPhysicsJoint& jointPrim, const MJCFJoint* joint);
void applyJointLimits(pxr::UsdPhysicsJoint jointPrim,
                      const MJCFJoint* joint,
                      const MJCFActuator* actuator,
                      const int* axisMap,
                      const int jointIdx,
                      const int numJoints,
                      const ImportConfig& config);
void createJointDrives(pxr::UsdPhysicsJoint jointPrim,
                       const MJCFJoint* joint,
                       const MJCFActuator* actuator,
                       const std::string axis,
                       const ImportConfig& config);

}
}
}
