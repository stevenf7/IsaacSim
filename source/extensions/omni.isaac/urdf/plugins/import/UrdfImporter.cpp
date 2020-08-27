// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include "UrdfImporter.h"

#include "../core/PathUtils.h"
#include "UrdfImporter.h"

// #include "../../GymJoint.h"
// #include "../../helpers.h"


#include "assimp/Importer.hpp"
#include "assimp/cfileio.h"
#include "assimp/cimport.h"
#include "assimp/postprocess.h"
#include "assimp/scene.h"

// clang-format off
#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>
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
#include <PhysxSchema/physxArticulationJointAPI.h>

#include "ImportHelpers.h"
//#define VERBOSE_URDF

namespace omni
{
namespace isaac
{
namespace urdf
{

using namespace carb::gym;


UrdfRobot UrdfImporter::createAsset()
{
    UrdfRobot robot;
    if (!parseUrdf(assetRoot_, urdfPath_, robot))
    {
        CARB_LOG_ERROR("Failed to parse URDF file '%s'", urdfPath_.c_str());
        return robot;
    }

    if (config.mergeFixedJoints)
    {
        collapseFixedJoints(robot);
    }
    return robot;
}


pxr::UsdPrim addMesh(pxr::UsdStageWeakPtr stage,
                     UrdfGeometry geometry,
                     std::string assetRoot,
                     std::string urdfPath,
                     std::string name,
                     UrdfOrigin origin,
                     const bool loadMaterials,
                     const float distanceScale)
{
    pxr::SdfPath path;
    if (geometry.type == UrdfGeometryType::MESH)
    {
        std::string meshUri = geometry.meshFilePath;
        std::string meshPath = resolveXrefPath(assetRoot, urdfPath, meshUri);

        // pxr::GfMatrix4d meshMat;
        if (meshPath.empty())
        {
            CARB_LOG_INFO("Failed to resolve mesh '%s'", meshUri.c_str());
            return pxr::UsdPrim(); // move to next shape
        }
        else
        {
            CARB_LOG_INFO("Found Mesh At: %s", meshPath.c_str());
            auto assimpScene = aiImportFile(meshPath.c_str(), aiProcess_GenSmoothNormals | aiProcess_GlobalScale);
            static auto sceneDeleter = [](const aiScene* scene) {
                if (scene)
                {
                    aiReleaseImport(scene);
                }
            };
            auto sceneRAII = std::shared_ptr<const aiScene>(assimpScene, sceneDeleter);
            // Add visuals
            path = SimpleImport(stage, name, sceneRAII.get(), loadMaterials);
        }
    }
    else if (geometry.type == UrdfGeometryType::SPHERE)
    {
        pxr::UsdGeomSphere gprim = pxr::UsdGeomSphere::Define(stage, pxr::SdfPath(name));
        pxr::VtVec3fArray extentArray(2);

        gprim.ComputeExtent(geometry.radius, &extentArray);
        gprim.GetExtentAttr().Set(extentArray);
        gprim.GetRadiusAttr().Set(double(geometry.radius));
        path = pxr::SdfPath(name);
    }
    else if (geometry.type == UrdfGeometryType::BOX)
    {
        pxr::UsdGeomCube gprim = pxr::UsdGeomCube::Define(stage, pxr::SdfPath(name));
        pxr::VtVec3fArray extentArray(2);
        extentArray[1] = pxr::GfVec3f(geometry.size_x * 0.5f, geometry.size_y * 0.5f, geometry.size_z * 0.5f);
        extentArray[0] = -extentArray[1];
        gprim.GetExtentAttr().Set(extentArray);
        gprim.GetSizeAttr().Set(1.0);
        path = pxr::SdfPath(name);
    }
    else if (geometry.type == UrdfGeometryType::CYLINDER)
    {
        pxr::UsdGeomCylinder gprim = pxr::UsdGeomCylinder::Define(stage, pxr::SdfPath(name));
        pxr::VtVec3fArray extentArray(2);
        gprim.ComputeExtent(geometry.length, geometry.radius, pxr::UsdGeomTokens->x, &extentArray);
        gprim.GetAxisAttr().Set(pxr::UsdGeomTokens->z);
        gprim.GetExtentAttr().Set(extentArray);
        gprim.GetHeightAttr().Set(double(geometry.length));
        gprim.GetRadiusAttr().Set(double(geometry.radius));
        path = pxr::SdfPath(name);
    }


    pxr::UsdPrim prim = stage->GetPrimAtPath(path);
    if (prim)
    {
        Transform transform = urdfOriginToTransform(origin);

        pxr::GfMatrix4d mat;
        mat.SetIdentity();
        mat.SetTranslateOnly(pxr::GfVec3d(transform.p.x, transform.p.y, transform.p.z));
        mat.SetRotateOnly(pxr::GfQuatd(transform.q.w, transform.q.x, transform.q.y, transform.q.z));

        pxr::GfMatrix4d scale;
        scale.SetIdentity();
        if (geometry.type == UrdfGeometryType::MESH)
        {
            scale.SetScale(distanceScale * pxr::GfVec3d(geometry.scale_x, geometry.scale_y, geometry.scale_z));
        }
        else if (geometry.type == UrdfGeometryType::BOX)
        {
            scale.SetScale(distanceScale * pxr::GfVec3d(geometry.size_x, geometry.size_y, geometry.size_z));
        }
        else
        {
            scale.SetScale(pxr::GfVec3d(distanceScale, distanceScale, distanceScale));
        }
        pxr::UsdGeomXformable gprim = pxr::UsdGeomXformable(prim);
        gprim.ClearXformOpOrder();
        pxr::UsdGeomXformOp trans = gprim.AddTransformOp();
        trans.Set(mat * scale, pxr::UsdTimeCode::Default());
    }
    return prim;
}

void UrdfImporter::addRigidBody(pxr::UsdStageWeakPtr stage,
                                const UrdfLink& link,
                                const Transform& poseBodyToWorld,
                                pxr::UsdGeomXform robotPrim,
                                const UrdfRobot& robot)
{
    std::string robotBasePath = robotPrim.GetPath().GetString() + "/";
    CARB_LOG_INFO("Add Rigid Body: %s", link.name.c_str());
    // Create Link Prim
    auto linkPrim = pxr::UsdGeomXform::Define(stage, pxr::SdfPath(robotBasePath + link.name));
    if (linkPrim)
    {
        Transform transform = poseBodyToWorld; // urdfOriginToTransform(link.inertial.origin);

        pxr::GfMatrix4d mat;
        mat.SetTranslateOnly(config.distanceScale * pxr::GfVec3d(transform.p.x, transform.p.y, transform.p.z));
        mat.SetRotateOnly(pxr::GfQuatd(transform.q.w, transform.q.x, transform.q.y, transform.q.z));
        pxr::GfMatrix4d scale;
        scale.SetIdentity();

        linkPrim.ClearXformOpOrder();
        pxr::UsdGeomXformOp trans = linkPrim.AddTransformOp();
        trans.Set(mat * scale, pxr::UsdTimeCode::Default());


        pxr::addRigidBody(stage, linkPrim.GetPath().GetString());

        pxr::PhysicsSchemaMassAPI massAPI = pxr::PhysicsSchemaMassAPI::Apply(linkPrim.GetPrim());
        if (link.inertial.hasMass)
        {
            massAPI.CreateMassAttr().Set(double(link.inertial.mass));
        }
        else
        {
            // scale from kg/m^2 to specified units
            massAPI.CreateDensityAttr().Set(double(config.density));
        }
        if (link.inertial.hasInertia)
        {
            // input is meters, but convert to kit units
            massAPI.CreateDiagonalInertiaAttr().Set(
                pxr::GfVec3d(link.inertial.inertia.ixx, link.inertial.inertia.iyy, link.inertial.inertia.izz) *
                config.distanceScale * config.distanceScale);
        }
    }
    else
    {
        CARB_LOG_ERROR("linkPrim %s not created", link.name.c_str());
        return;
    }

    // Add visuals
    for (size_t i = 0; i < link.visuals.size(); i++)
    {
        std::string meshName;
        if (link.visuals.size() > 1)
        {
            std::string name = "mesh_" + std::to_string(i);
            if (link.visuals[i].name.size() > 0)
            {
                name = link.visuals[i].name;
            }
            meshName = robotBasePath + link.name + "/visuals/" + name;
        }
        else
        {
            meshName = robotBasePath + link.name + "/visuals";
        }
        bool loadMaterial = true;

        auto mat = link.visuals[i].material;
        auto urdfMatIter = robot.materials.find(link.visuals[i].material.name);
        if (urdfMatIter != robot.materials.end())
        {
            mat = urdfMatIter->second;
        }

        auto& color = mat.color;
        if (color.r >= 0 && color.g >= 0 && color.b >= 0)
        {
            loadMaterial = false;
        }

        pxr::UsdPrim prim = addMesh(stage, link.visuals[i].geometry, assetRoot_, urdfPath_, meshName,
                                    link.visuals[i].origin, loadMaterial, config.distanceScale);

        if (loadMaterial == false)
        {
            // This Material was in the master list, reuse
            auto urdfMatIter = robot.materials.find(link.visuals[i].material.name);
            if (urdfMatIter != robot.materials.end())
            {
                std::string path = matPrimPaths[link.visuals[i].material.name];

                auto matPrim = stage->GetPrimAtPath(pxr::SdfPath(path));

                if (matPrim)
                {
                    auto shadePrim = pxr::UsdShadeMaterial(matPrim);
                    if (shadePrim)
                    {
                        pxr::UsdShadeMaterialBindingAPI mbi(prim);
                        mbi.Bind(shadePrim);
                    }
                }
            }
            else
            {
                auto& color = link.visuals[i].material.color;
                pxr::SdfPath shaderPath = prim.GetPath().AppendPath(pxr::SdfPath(
                    "Looks/" + MakeValidUSDIdentifier("material_" + std::to_string(color.r) + "_" +
                                                      std::to_string(color.g) + "_" + std::to_string(color.b))));
                pxr::UsdShadeMaterial matPrim = pxr::UsdShadeMaterial::Define(stage, shaderPath);
                if (matPrim)
                {
                    pxr::UsdShadeShader pbrShader =
                        pxr::UsdShadeShader::Define(stage, shaderPath.AppendPath(pxr::SdfPath("Shader")));
                    if (pbrShader)
                    {
                        pbrShader.CreateIdAttr(pxr::VtValue(pxr::UsdImagingTokens->UsdPreviewSurface));

                        pbrShader.CreateInput(pxr::TfToken("diffuseColor"), pxr::SdfValueTypeNames->Color3f)
                            .Set(pxr::GfVec3f(color.r, color.g, color.b));

                        auto output = matPrim.CreateSurfaceOutput();
                        output.ConnectToSource(pbrShader, pxr::TfToken("surface"));
                    }
                    else
                    {
                        CARB_LOG_WARN("Couldn't create shader at: %s", shaderPath.GetString().c_str());
                    }

                    pxr::UsdShadeMaterialBindingAPI mbi(prim);
                    mbi.Bind(matPrim);
                }
            }
        }
        if (!prim)
        {
            CARB_LOG_ERROR("Prim %s not created", meshName.c_str());
        }
    }
    // Add collisions
    for (size_t i = 0; i < link.collisions.size(); i++)
    {

        std::string meshName;
        if (link.collisions.size() > 1)
        {
            std::string name = "mesh_" + std::to_string(i);
            if (link.collisions[i].name.size() > 0)
            {
                name = link.collisions[i].name;
            }
            meshName = robotBasePath + link.name + "/collisions/" + name;
        }
        else
        {
            meshName = robotBasePath + link.name + "/collisions";
        }

        pxr::UsdPrim prim = addMesh(stage, link.collisions[i].geometry, assetRoot_, urdfPath_, meshName,
                                    link.collisions[i].origin, false, config.distanceScale);
        // Enable collisions on prim
        if (prim)
        {
            pxr::PhysicsSchemaCollisionAPI::Apply(prim);
            pxr::PhysxSchemaPhysxMeshCollisionAPI physxMeshAPI = pxr::PhysxSchemaPhysxMeshCollisionAPI::Apply(prim);
            if (link.collisions[i].geometry.type == UrdfGeometryType::SPHERE)
            {
                physxMeshAPI.CreatePhysxMeshCollisionApproximationAttr().Set(pxr::PhysxSchemaTokens.Get()->boundingSphere);
            }
            else if (link.collisions[i].geometry.type == UrdfGeometryType::BOX)
            {
                physxMeshAPI.CreatePhysxMeshCollisionApproximationAttr().Set(pxr::PhysxSchemaTokens.Get()->boundingCube);
            }
            else
            {
                physxMeshAPI.CreatePhysxMeshCollisionApproximationAttr().Set(pxr::PhysxSchemaTokens.Get()->convexHull);
            }
            pxr::UsdGeomMesh(prim).CreatePurposeAttr().Set(pxr::UsdGeomTokens->guide);
        }
        else
        {
            CARB_LOG_ERROR("Prim %s not created", meshName.c_str());
        }
    }
}

pxr::TfToken getAxisXYZ(const UrdfAxis& inAxis)
{
    if (inAxis.x != 0.0)
    {
        return pxr::TfToken("X");
    }
    else if (inAxis.y != 0.0)
    {
        return pxr::TfToken("Y");
    }
    else if (inAxis.z != 0.0)
    {
        return pxr::TfToken("Z");
    }
    return pxr::TfToken("X");
}

template <class T>
void AddSingleJoint(const UrdfJoint& joint,
                    pxr::UsdStageWeakPtr stage,
                    const pxr::SdfPath& jointPath,
                    pxr::PhysicsSchemaPhysicsJoint& jointPrimBase,
                    const float distanceScale)
{

    T jointPrim = T::Define(stage, pxr::SdfPath(jointPath));
    jointPrimBase = jointPrim;
    jointPrim.CreateAxisAttr().Set(pxr::TfToken("X"));
    jointPrim.CreateJointFrictionAttr().Set(joint.dynamics.friction);

    // Set the limits if the joint is anything except a continuous joint
    if (joint.type != UrdfJointType::CONTINUOUS)
    {
        float scale = 1.0f;
        if (joint.type == UrdfJointType::PRISMATIC)
        {
            scale = distanceScale;
        }
        jointPrim.CreateLowerLimitAttr().Set(scale * joint.limit.lower);
        jointPrim.CreateUpperLimitAttr().Set(scale * joint.limit.upper);
    }
    if (joint.drive.targetType != UrdfJointTargetType::NONE)
    {
        if (joint.type == UrdfJointType::PRISMATIC)
        {
            pxr::PhysicsSchemaDriveAPI driveAPI =
                pxr::PhysicsSchemaDriveAPI::Apply(jointPrim.GetPrim(), pxr::TfToken("linear"));
            // convert kg*m/s^2 to kg * cm /s^2
            driveAPI.CreateMaxForceAttr().Set(joint.limit.effort * distanceScale);
            driveAPI.CreateTargetAttr().Set(joint.drive.target);
            if (joint.drive.driveType == UrdfJointDriveType::FORCE)
                driveAPI.CreateTypeAttr().Set(pxr::TfToken("force"));
            else
            {
                driveAPI.CreateTypeAttr().Set(pxr::TfToken("acceleration"));
            }

            if (joint.drive.targetType == UrdfJointTargetType::POSITION)
                driveAPI.CreateTargetTypeAttr().Set(pxr::TfToken("position"));
            else
            {
                driveAPI.CreateTargetTypeAttr().Set(pxr::TfToken("velocity"));
            }

            driveAPI.CreateDampingAttr().Set(joint.dynamics.damping);
            driveAPI.CreateStiffnessAttr().Set(joint.dynamics.stiffness);
        }
        // continuous and revolute are identical except for setting limits
        else if (joint.type == UrdfJointType::REVOLUTE || joint.type == UrdfJointType::CONTINUOUS)
        {
            pxr::PhysicsSchemaDriveAPI driveAPI =
                pxr::PhysicsSchemaDriveAPI::Apply(jointPrim.GetPrim(), pxr::TfToken("angular"));
            // convert kg*m/s^2 * m to kg * cm /s^2 * cm
            driveAPI.CreateMaxForceAttr().Set(joint.limit.effort * distanceScale * distanceScale);
            driveAPI.CreateTargetAttr().Set(joint.drive.target);
            if (joint.drive.driveType == UrdfJointDriveType::FORCE)
                driveAPI.CreateTypeAttr().Set(pxr::TfToken("force"));
            else
            {
                driveAPI.CreateTypeAttr().Set(pxr::TfToken("acceleration"));
            }

            if (joint.drive.targetType == UrdfJointTargetType::POSITION)
                driveAPI.CreateTargetTypeAttr().Set(pxr::TfToken("position"));
            else
            {
                driveAPI.CreateTargetTypeAttr().Set(pxr::TfToken("velocity"));
            }
            driveAPI.CreateDampingAttr().Set(joint.dynamics.damping);
            driveAPI.CreateStiffnessAttr().Set(joint.dynamics.stiffness);
        }
    }
    auto artJointAPI = pxr::PhysxSchemaPhysxArticulationJointAPI::Apply(jointPrim.GetPrim());
    artJointAPI.CreatePhysxArticulationJointMaxJointVelocityAttr().Set(joint.limit.velocity);
    artJointAPI.CreatePhysxArticulationJointFrictionCoefficientAttr().Set(joint.dynamics.friction);
}


void UrdfImporter::addJoint(pxr::UsdStageWeakPtr stage,
                            pxr::UsdGeomXform robotPrim,
                            const UrdfJoint& joint,
                            const Transform& poseJointToParentBody)
{

    std::string parentLinkPath = robotPrim.GetPath().GetString() + "/" + joint.parentLinkName;
    std::string childLinkPath = robotPrim.GetPath().GetString() + "/" + joint.childLinkName;
    std::string jointPath = parentLinkPath + "/" + joint.name;

    if (!pxr::SdfPath::IsValidPathString(jointPath))
    {
        // jn->getName starts with a number which is not valid for usd path, so prefix it with "joint"
        jointPath = parentLinkPath + "/joint" + joint.name;
    }
    pxr::PhysicsSchemaPhysicsJoint jointPrim;
    if (joint.type == UrdfJointType::FIXED)
    {
        jointPrim = pxr::PhysicsSchemaFixedPhysicsJoint::Define(stage, pxr::SdfPath(jointPath));
    }
    else if (joint.type == UrdfJointType::PRISMATIC)
    {
        AddSingleJoint<pxr::PhysicsSchemaPrismaticPhysicsJoint>(
            joint, stage, pxr::SdfPath(jointPath), jointPrim, config.distanceScale);
    }
    // else if (joint.type == UrdfJointType::SPHERICAL)
    // {
    //     AddSingleJoint<PhysicsSchemaSphericalPhysicsJoint>(jn, stage, SdfPath(jointPath), jointPrim, skel,
    //     distanceScale);
    // }
    else if (joint.type == UrdfJointType::REVOLUTE || joint.type == UrdfJointType::CONTINUOUS)
    {
        AddSingleJoint<pxr::PhysicsSchemaRevolutePhysicsJoint>(
            joint, stage, pxr::SdfPath(jointPath), jointPrim, config.distanceScale);
    }


    pxr::SdfPathVector val0{ pxr::SdfPath(parentLinkPath) };
    pxr::SdfPathVector val1{ pxr::SdfPath(childLinkPath) };

    if (parentLinkPath != "")
    {
        jointPrim.CreateBody0Rel().SetTargets(val0);
    }

    pxr::GfVec3f localPos0 = config.distanceScale * pxr::GfVec3f(poseJointToParentBody.p.x, poseJointToParentBody.p.y,
                                                                 poseJointToParentBody.p.z);
    pxr::GfQuatf localRot0 = pxr::GfQuatf(
        poseJointToParentBody.q.w, poseJointToParentBody.q.x, poseJointToParentBody.q.y, poseJointToParentBody.q.z);
    pxr::GfVec3f localPos1 = config.distanceScale * pxr::GfVec3f(0, 0, 0);
    pxr::GfQuatf localRot1 = pxr::GfQuatf(1, 0, 0, 0);

    // Take the joint axis and cross it with X
    Vec3 rotAxis = -Cross(urdfAxisToVec(joint.axis), Vec3(1.0f, 0.0f, 0.0f));
    float d = Dot(rotAxis, rotAxis);
    if (d < 1e-5f)
    {
        // If the joint axis was itself X, then use a fixed rotation axis
        rotAxis = Vec3(0.0f, 1.0f, 0.0f);
    }
    else
    {
        // normalize the rotation axis
        rotAxis /= sqrtf(d);
    }

    Quat axisRot = QuatFromAxisAngle(rotAxis, acos(joint.axis.x));

    // printf("jointPath: %s [%f %f %f], [%f %f %f] [%f %f %f %f]\n", jointPath.c_str(), rotAxis.x, rotAxis.y,
    // rotAxis.z, joint.axis.x,
    //        joint.axis.y, joint.axis.z, axisRot.w, axisRot.x, axisRot.y, axisRot.z);
    // addPosition(jointPrim, localPos0);
    jointPrim.CreateLocalPos0Attr().Set(localPos0);
    jointPrim.CreateLocalRot0Attr().Set(localRot0 * pxr::GfQuatf(axisRot.w, axisRot.x, axisRot.y, axisRot.z));

    if (childLinkPath != "")
    {
        jointPrim.CreateBody1Rel().SetTargets(val1);
    }
    jointPrim.CreateLocalPos1Attr().Set(localPos1);
    jointPrim.CreateLocalRot1Attr().Set(localRot1 * pxr::GfQuatf(axisRot.w, axisRot.x, axisRot.y, axisRot.z));

    jointPrim.CreateBreakForceAttr().Set(FLT_MAX);
    jointPrim.CreateBreakTorqueAttr().Set(FLT_MAX);

    auto linkAPI = pxr::PhysicsSchemaArticulationJointAPI::Apply(stage->GetPrimAtPath(pxr::SdfPath(jointPath)));
    linkAPI.CreateArticulationTypeAttr().Set(pxr::TfToken("articulatedJoint"));
}
void UrdfImporter::addLinksAndJoints(pxr::UsdStageWeakPtr stage,
                                     const Transform& poseParentToWorld,
                                     const KinematicChain::Node* parentNode,
                                     const UrdfRobot& robot,
                                     pxr::UsdGeomXform robotPrim)
{
    const UrdfLink& urdfLink = robot.links.at(parentNode->linkName_);
    addRigidBody(stage, urdfLink, poseParentToWorld, robotPrim, robot);
    // Create root joint only once
    if (parentNode->parentJointName_ == "")
    {
        std::string rootJointPath = robotPrim.GetPath().GetString() + "/rootJoint";
        pxr::PhysicsSchemaPhysicsJoint rootJoint =
            pxr::PhysicsSchemaPhysicsJoint::Define(stage, pxr::SdfPath(rootJointPath));
        auto linkAPI = pxr::PhysicsSchemaArticulationJointAPI::Apply(stage->GetPrimAtPath(pxr::SdfPath(rootJointPath)));
        linkAPI.CreateArticulationTypeAttr().Set(pxr::TfToken("articulatedRoot"));

        pxr::SdfPathVector val0{ pxr::SdfPath(robotPrim.GetPath().GetString() + "/" + urdfLink.name) };
        rootJoint.CreateBody0Rel().SetTargets(val0);
    }

    if (!parentNode->childNodes_.empty())
    {
        for (const auto& childNode : parentNode->childNodes_)
        {
            const UrdfJoint urdfJoint = robot.joints.at(childNode->parentJointName_);
            const UrdfLink& childLink = robot.links.at(childNode->linkName_);
            // const UrdfLink& parentLink = robot.links.at(parentNode->linkName_);

            Transform poseJointToLink = urdfOriginToTransform(urdfJoint.origin);
            // According to URDF spec, the frame of a link coincides with its parent joint frame
            Transform poseLinkToWorld = poseParentToWorld * poseJointToLink;
            // if (!parentLink.softs.size() && !childLink.softs.size()) // rigid parent, rigid child
            {
                addRigidBody(stage, childLink, poseLinkToWorld, robotPrim, robot);
                addJoint(stage, robotPrim, urdfJoint, poseJointToLink);

                // RigidBodyTopo bodyTopo;
                // bodyTopo.bodyIndex = asset->bodyLookup.at(childNode->linkName_);
                // bodyTopo.parentIndex = asset->bodyLookup.at(parentNode->linkName_);
                // bodyTopo.jointIndex = asset->jointLookup.at(childNode->parentJointName_);
                // bodyTopo.jointSpecStart = asset->jointLookup.at(childNode->parentJointName_);
                // // URDF only has 1 DOF joints
                // bodyTopo.jointSpecCount = 1;
                // asset->rigidBodyHierarchy.push_back(bodyTopo);
            }

            // Recurse through the links children
            addLinksAndJoints(stage, poseLinkToWorld, childNode.get(), robot, robotPrim);
        }
    }
}

void UrdfImporter::addMaterials(pxr::UsdStageWeakPtr stage, const UrdfRobot& robot, const pxr::SdfPath& prefixPath)
{
    for (auto& mat : robot.materials)
    {
        auto& color = mat.second.color;
        auto& name = mat.second.name;

        if (color.r >= 0 && color.g >= 0 && color.b >= 0)
        {
            pxr::SdfPath shaderPath =
                prefixPath.AppendPath(pxr::SdfPath("Looks/" + MakeValidUSDIdentifier("material_" + name)));

            pxr::UsdShadeMaterial matPrim = pxr::UsdShadeMaterial::Define(stage, shaderPath);
            if (matPrim)
            {
                pxr::UsdShadeShader pbrShader =
                    pxr::UsdShadeShader::Define(stage, shaderPath.AppendPath(pxr::SdfPath("Shader")));
                if (pbrShader)
                {
                    pbrShader.CreateIdAttr(pxr::VtValue(pxr::UsdImagingTokens->UsdPreviewSurface));

                    pbrShader.CreateInput(pxr::TfToken("diffuseColor"), pxr::SdfValueTypeNames->Color3f)
                        .Set(pxr::GfVec3f(color.r, color.g, color.b));

                    auto output = matPrim.CreateSurfaceOutput();
                    output.ConnectToSource(pbrShader, pxr::TfToken("surface"));
                    matPrimPaths[name] = shaderPath.GetString();
                }
                else
                {
                    CARB_LOG_WARN("Couldn't create shader at: %s", shaderPath.GetString());
                }
            }
            else
            {
                CARB_LOG_WARN("Couldn't create material at: %s", shaderPath.GetString());
            }
        }
    }
}


std::string UrdfImporter::addToStage(pxr::UsdStageWeakPtr stage, const UrdfRobot& urdfRobot)
{
    if (config.createPhysicsScene)
    {
        // Create physics scene
        pxr::PhysicsSchemaPhysicsScene scene =
            pxr::PhysicsSchemaPhysicsScene::Define(stage, pxr::SdfPath("/physicsScene"));
        scene.CreateGravityAttr().Set(pxr::GfVec3f(0.0f, 0.0f, -9.80f * config.distanceScale));
        pxr::PhysxSchemaPhysxSceneAPI physxSceneAPI =
            pxr::PhysxSchemaPhysxSceneAPI::Apply(stage->GetPrimAtPath(pxr::SdfPath("/physicsScene")));
        physxSceneAPI.CreatePhysxSceneEnableCCDAttr().Set(true);
        physxSceneAPI.CreatePhysxSceneEnableStabilizationAttr().Set(true);
        physxSceneAPI.CreatePhysxSceneEnableGPUDynamicsAttr().Set(false);

        physxSceneAPI.CreatePhysxSceneBroadphaseTypeAttr().Set(pxr::TfToken("MBP"));
        physxSceneAPI.CreatePhysxSceneSolverTypeAttr().Set(pxr::TfToken("TGS"));
    }

    pxr::SdfPath primPath =
        pxr::SdfPath(GetNewSdfPathString(stage, "/" + pxr::TfMakeValidIdentifier(std::string(urdfRobot.name))));

    // // Remove the prim we are about to add in case it exists
    // if (stage->GetPrimAtPath(primPath))
    // {
    //     stage->RemovePrim(primPath);
    // }

    pxr::UsdGeomXform robotPrim = pxr::UsdGeomXform::Define(stage, primPath);
    pxr::PhysicsSchemaArticulationAPI physicsSchema = pxr::PhysicsSchemaArticulationAPI::Apply(robotPrim.GetPrim());

    physicsSchema.CreateFixBaseAttr().Set(config.fixBase);
    physicsSchema.CreateEnableSelfCollisionsAttr().Set(config.selfCollision);

    if (config.makeDefaultPrim)
    {
        stage->SetDefaultPrim(robotPrim.GetPrim());
    }


    KinematicChain chain;
    if (!chain.computeKinematicChain(urdfRobot))
    {
        return "";
    }

    addMaterials(stage, urdfRobot, primPath);

    addLinksAndJoints(stage, Transform(), chain.baseNode.get(), urdfRobot, robotPrim);

    return primPath.GetString();
}
}
}
}
