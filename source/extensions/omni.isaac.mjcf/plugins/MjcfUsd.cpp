#pragma once

#include "MjcfUsd.h"

namespace omni
{
namespace isaac
{
namespace mjcf
{

void setStageMetadata(pxr::UsdStageWeakPtr stage, const omni::isaac::mjcf::ImportConfig config)
{
    if (config.createPhysicsScene)
    {
        pxr::UsdPhysicsScene scene = pxr::UsdPhysicsScene::Define(stage, pxr::SdfPath("/physicsScene"));
        scene.CreateGravityDirectionAttr().Set(pxr::GfVec3f(0.0f, 0.0f, -1.0));
        scene.CreateGravityMagnitudeAttr().Set(9.81f * config.distanceScale);

        pxr::PhysxSchemaPhysxSceneAPI physxSceneAPI =
            pxr::PhysxSchemaPhysxSceneAPI::Apply(stage->GetPrimAtPath(pxr::SdfPath("/physicsScene")));
        physxSceneAPI.CreateEnableCCDAttr().Set(true);
        physxSceneAPI.CreateEnableStabilizationAttr().Set(true);
        physxSceneAPI.CreateEnableGPUDynamicsAttr().Set(false);

        physxSceneAPI.CreateBroadphaseTypeAttr().Set(pxr::TfToken("MBP"));
        physxSceneAPI.CreateSolverTypeAttr().Set(pxr::TfToken("TGS"));
    }

    pxr::UsdGeomSetStageMetersPerUnit(stage, 1.0f / config.distanceScale);
    pxr::UsdGeomSetStageUpAxis(stage, pxr::TfToken("Z"));
}

void createRoot(pxr::UsdStageWeakPtr stage,
                Transform trans,
                const std::string rootPrimPath,
                const omni::isaac::mjcf::ImportConfig config)
{
    pxr::UsdGeomXform robotPrim = pxr::UsdGeomXform::Define(stage, pxr::SdfPath(rootPrimPath));

    if (config.makeDefaultPrim)
    {
        stage->SetDefaultPrim(robotPrim.GetPrim());
    }
}

void createFixedRoot(pxr::UsdStageWeakPtr stage, const std::string jointPath, const std::string bodyPath)
{
    pxr::UsdPhysicsFixedJoint rootJoint = pxr::UsdPhysicsFixedJoint::Define(stage, pxr::SdfPath(jointPath));
    pxr::SdfPathVector val1{ pxr::SdfPath(bodyPath) };
    rootJoint.CreateBody1Rel().SetTargets(val1);
}

void applyArticulationAPI(pxr::UsdStageWeakPtr stage,
                          pxr::UsdGeomXformable prim,
                          const omni::isaac::mjcf::ImportConfig config)
{
    pxr::UsdPhysicsArticulationRootAPI physicsSchema = pxr::UsdPhysicsArticulationRootAPI::Apply(prim.GetPrim());
    pxr::PhysxSchemaPhysxArticulationAPI physxSchema = pxr::PhysxSchemaPhysxArticulationAPI::Apply(prim.GetPrim());
    physxSchema.CreateEnabledSelfCollisionsAttr().Set(config.selfCollision);
}

// convert from internal Gym mesh to USD mesh
pxr::UsdGeomMesh createMesh(pxr::UsdStageWeakPtr stage, const pxr::SdfPath path, Mesh* mesh, float scale)
{
    std::vector<pxr::GfVec3f> points(mesh->m_positions.size());
    std::vector<pxr::GfVec3f> normals(mesh->m_normals.size());
    std::vector<int> indices(mesh->m_indices.size());
    std::vector<int> vertexCounts(mesh->GetNumFaces(), 3);
    for (size_t i = 0; i < mesh->m_positions.size(); i++)
    {
        Point3 p = scale * mesh->m_positions[i];
        points[i].Set(&p.x);
    }
    for (size_t i = 0; i < mesh->m_normals.size(); i++)
    {
        normals[i].Set(&mesh->m_normals[i].x);
    }
    for (size_t i = 0; i < mesh->m_indices.size(); i++)
    {
        indices[i] = mesh->m_indices[i];
    }

    return createMesh(stage, path, points, normals, indices, vertexCounts);
}

pxr::UsdGeomMesh createMesh(pxr::UsdStageWeakPtr stage,
                            const pxr::SdfPath path,
                            const std::vector<pxr::GfVec3f>& points,
                            const std::vector<pxr::GfVec3f>& normals,
                            const std::vector<int>& indices,
                            const std::vector<int>& vertexCounts)
{
    pxr::UsdGeomMesh mesh = pxr::UsdGeomMesh::Define(stage, path);
    // Fill in VtArrays
    pxr::VtArray<int> vertexCountsVt;
    vertexCountsVt.assign(vertexCounts.begin(), vertexCounts.end());
    pxr::VtArray<int> vertexIndicesVt;
    vertexIndicesVt.assign(indices.begin(), indices.end());
    pxr::VtArray<pxr::GfVec3f> pointArrayVt;
    pointArrayVt.assign(points.begin(), points.end());
    pxr::VtArray<pxr::GfVec3f> normalsVt;
    normalsVt.assign(normals.begin(), normals.end());
    mesh.CreateFaceVertexCountsAttr().Set(vertexCountsVt);
    mesh.CreateFaceVertexIndicesAttr().Set(vertexIndicesVt);
    mesh.CreatePointsAttr().Set(pointArrayVt);
    mesh.CreateDoubleSidedAttr().Set(true);
    mesh.CreateNormalsAttr().Set(normalsVt);

    return mesh;
}

pxr::UsdGeomXformable createBody(pxr::UsdStageWeakPtr stage,
                                 const std::string primPath,
                                 const Transform& trans,
                                 const ImportConfig& config)
{
    // translate the prim before xform is created automatically
    pxr::UsdGeomXform xform = pxr::UsdGeomXform::Define(stage, pxr::SdfPath(primPath));
    pxr::GfMatrix4d bodyMat;
    bodyMat.SetIdentity();
    bodyMat.SetTranslateOnly(config.distanceScale * pxr::GfVec3d(trans.p.x, trans.p.y, trans.p.z));
    bodyMat.SetRotateOnly(pxr::GfQuatd(trans.q.w, trans.q.x, trans.q.y, trans.q.z));
    pxr::UsdGeomXformable gprim = pxr::UsdGeomXformable(xform);
    gprim.ClearXformOpOrder();
    pxr::UsdGeomXformOp transOp = gprim.AddTransformOp();
    transOp.Set(bodyMat, pxr::UsdTimeCode::Default());

    return gprim;
}

void applyRigidBody(pxr::UsdGeomXformable bodyPrim, const MJCFBody* body, const ImportConfig& config)
{
    pxr::UsdPhysicsRigidBodyAPI physicsAPI = pxr::UsdPhysicsRigidBodyAPI::Apply(bodyPrim.GetPrim());
    pxr::PhysxSchemaPhysxRigidBodyAPI::Apply(bodyPrim.GetPrim());

    pxr::UsdPhysicsMassAPI massAPI = pxr::UsdPhysicsMassAPI::Apply(bodyPrim.GetPrim());
    // TODO: need to support override computation
    if (body->inertial && config.importInertiaTensor)
    {
        massAPI.CreateMassAttr().Set(body->inertial->mass);

        if (!config.overrideCoM)
        {
            massAPI.CreateCenterOfMassAttr().Set(
                config.distanceScale * pxr::GfVec3f(body->inertial->pos.x, body->inertial->pos.y, body->inertial->pos.z));
        }

        if (!config.overrideInertia)
        {
            massAPI.CreateDiagonalInertiaAttr().Set(
                config.distanceScale * config.distanceScale *
                pxr::GfVec3f(body->inertial->diaginertia.x, body->inertial->diaginertia.y, body->inertial->diaginertia.z));
        }
    }
    else
    {
        massAPI.CreateDensityAttr().Set(config.density / config.distanceScale / config.distanceScale /
                                        config.distanceScale);
    }
}

pxr::UsdPrim createPrimitiveGeom(pxr::UsdStageWeakPtr stage,
                                 const std::string geomPath,
                                 const MJCFGeom* geom,
                                 const std::map<std::string, MeshInfo>& simulationMeshCache,
                                 const ImportConfig& config)
{
    pxr::SdfPath path = pxr::SdfPath(geomPath);

    if (geom->type == MJCFGeom::SPHERE)
    {
        pxr::UsdGeomSphere spherePrim = pxr::UsdGeomSphere::Define(stage, path);
        pxr::VtVec3fArray extentArray(2);

        spherePrim.ComputeExtent(geom->size.x, &extentArray);
        spherePrim.GetRadiusAttr().Set(double(geom->size.x));
        spherePrim.GetExtentAttr().Set(extentArray);
    }
    else if (geom->type == MJCFGeom::ELLIPSOID)
    {
        pxr::UsdGeomSphere ellipsePrim = pxr::UsdGeomSphere::Define(stage, path);
        pxr::VtVec3fArray extentArray(2);

        ellipsePrim.ComputeExtent(geom->size.x, &extentArray);
        ellipsePrim.GetExtentAttr().Set(extentArray);
    }
    else if (geom->type == MJCFGeom::CAPSULE)
    {
        pxr::UsdGeomCapsule capsulePrim = pxr::UsdGeomCapsule::Define(stage, path);
        pxr::VtVec3fArray extentArray(4);
        pxr::TfToken axis = pxr::TfToken("X");
        float height;
        if (geom->hasFromTo)
        {
            Vec3 dif = geom->to - geom->from;
            height = Length(dif);
        }
        else
        {
            // half length
            height = 2.0f * geom->size.y;
        }

        capsulePrim.GetRadiusAttr().Set(double(geom->size.x));
        capsulePrim.GetHeightAttr().Set(double(height));
        capsulePrim.GetAxisAttr().Set(axis);
        capsulePrim.ComputeExtent(double(height), double(geom->size.x), axis, &extentArray);
        capsulePrim.GetExtentAttr().Set(extentArray);
    }
    else if (geom->type == MJCFGeom::CYLINDER)
    {
        pxr::UsdGeomCylinder cylinderPrim = pxr::UsdGeomCylinder::Define(stage, path);
        pxr::VtVec3fArray extentArray(2);
        float height;
        if (geom->hasFromTo)
        {
            Vec3 dif = geom->to - geom->from;
            height = Length(dif);
        }
        else
        {
            height = 2.0f * geom->size.y;
        }
        pxr::TfToken axis = pxr::TfToken("X");
        cylinderPrim.ComputeExtent(double(height), double(geom->size.x), axis, &extentArray);
        cylinderPrim.GetAxisAttr().Set(pxr::UsdGeomTokens->z);
        cylinderPrim.GetExtentAttr().Set(extentArray);
        cylinderPrim.GetHeightAttr().Set(double(height));
        cylinderPrim.GetRadiusAttr().Set(double(geom->size.x));
    }
    else if (geom->type == MJCFGeom::BOX)
    {
        pxr::UsdGeomCube boxPrim = pxr::UsdGeomCube::Define(stage, path);
        pxr::VtVec3fArray extentArray(2);
        extentArray[1] = pxr::GfVec3f(geom->size.x, geom->size.y, geom->size.z);
        extentArray[0] = -extentArray[1];
        boxPrim.GetExtentAttr().Set(extentArray);
    }
    else if (geom->type == MJCFGeom::MESH)
    {
        MeshInfo meshInfo = simulationMeshCache.find(geom->mesh)->second;
        createMesh(stage, path, meshInfo.mesh, config.distanceScale);
    }

    pxr::UsdPrim prim = stage->GetPrimAtPath(path);
    if (prim)
    {
        // set the transformations first
        pxr::GfMatrix4d mat;
        mat.SetIdentity();
        mat.SetTranslateOnly(pxr::GfVec3d(geom->pos.x, geom->pos.y, geom->pos.z));
        mat.SetRotateOnly(pxr::GfQuatd(geom->quat.w, geom->quat.x, geom->quat.y, geom->quat.z));

        pxr::GfMatrix4d scale;
        scale.SetIdentity();
        scale.SetScale(pxr::GfVec3d(config.distanceScale, config.distanceScale, config.distanceScale));
        if (geom->type == MJCFGeom::ELLIPSOID)
        {
            scale.SetScale(config.distanceScale * pxr::GfVec3d(geom->size.x, geom->size.y, geom->size.z));
        }
        else if (geom->type == MJCFGeom::CAPSULE)
        {
            Vec3 cen;
            Quat q;

            if (geom->hasFromTo)
            {
                Vec3 diff = geom->to - geom->from;
                diff = Normalize(diff);
                Vec3 rotVec = Cross(Vec3(1.0f, 0.0f, 0.0f), diff);
                if (Length(rotVec) < 1e-5)
                {
                    rotVec = Vec3(0.0f, 1.0f, 0.0f); // default rotation about y-axis
                }
                else
                {
                    rotVec = Normalize(rotVec); // z axis
                }

                float angle = acos(diff.x);
                cen = 0.5f * (geom->from + geom->to);
                q = QuatFromAxisAngle(rotVec, angle);
            }
            else
            {
                cen = geom->pos;
                q = geom->quat * QuatFromAxisAngle(Vec3(0.0f, 1.0f, 0.0f), -kPi * 0.5f);
            }

            mat.SetTranslateOnly(config.distanceScale * pxr::GfVec3d(cen.x, cen.y, cen.z));
            mat.SetRotateOnly(pxr::GfQuatd(q.w, q.x, q.y, q.z));
        }
        else if (geom->type == MJCFGeom::CYLINDER)
        {
            Vec3 cen;
            Quat q;
            float hlen;
            if (geom->hasFromTo)
            {
                cen = 0.5f * (geom->from + geom->to);
                Vec3 axis = geom->to - geom->from;
                hlen = 0.5f * Length(axis);
                q = GetRotationQuat(Vec3(0.0f, 0.0f, 1.0f), Normalize(axis));
            }
            else
            {
                cen = geom->pos;
                q = geom->quat;
                hlen = geom->size.y;
            }

            mat.SetRotateOnly(pxr::GfQuatd(q.w, q.x, q.y, q.z));
            mat.SetTranslateOnly(pxr::GfVec3d(cen.x, cen.y, cen.z));
        }
        else if (geom->type == MJCFGeom::BOX)
        {
            Vec3 s = geom->size;
            Vec3 cen = geom->pos;
            Quat q = geom->quat;
            scale.SetScale(config.distanceScale * pxr::GfVec3d(s.x, s.y, s.z));
            mat.SetTranslateOnly(config.distanceScale * pxr::GfVec3d(cen.x, cen.y, cen.z));
            mat.SetRotateOnly(pxr::GfQuatd(q.w, q.x, q.y, q.z));
        }
        else if (geom->type == MJCFGeom::MESH)
        {
            Vec3 cen = geom->pos;
            Quat q = geom->quat;
            scale.SetIdentity();
            mat.SetTranslateOnly(config.distanceScale * pxr::GfVec3d(cen.x, cen.y, cen.z));
            mat.SetRotateOnly(pxr::GfQuatd(q.w, q.x, q.y, q.z));
        }

        pxr::UsdGeomXformable gprim = pxr::UsdGeomXformable(prim);
        gprim.ClearXformOpOrder();
        pxr::UsdGeomXformOp transOp = gprim.AddTransformOp();
        transOp.Set(scale * mat, pxr::UsdTimeCode::Default());
    }

    return prim;
}

void applyCollisionGeom(pxr::UsdStageWeakPtr stage, pxr::UsdPrim prim, const MJCFGeom* geom)
{
    pxr::UsdPhysicsCollisionAPI::Apply(prim);
    pxr::UsdPhysicsMeshCollisionAPI physicsMeshAPI = pxr::UsdPhysicsMeshCollisionAPI::Apply(prim);
    if (geom->type == MJCFGeom::SPHERE)
    {
        physicsMeshAPI.CreateApproximationAttr().Set(pxr::UsdPhysicsTokens.Get()->boundingSphere);
    }
    else if (geom->type == MJCFGeom::BOX)
    {
        physicsMeshAPI.CreateApproximationAttr().Set(pxr::UsdPhysicsTokens.Get()->boundingCube);
    }
    else
    {
        physicsMeshAPI.CreateApproximationAttr().Set(pxr::UsdPhysicsTokens.Get()->convexHull);
    }
    pxr::UsdGeomMesh(prim).CreatePurposeAttr().Set(pxr::UsdGeomTokens->guide);
}

pxr::UsdPhysicsJoint createFixedJoint(pxr::UsdStageWeakPtr stage,
                                      const std::string jointPath,
                                      const Transform& poseJointToParentBody,
                                      const Transform& poseJointToChildBody,
                                      const std::string parentBodyPath,
                                      const std::string bodyPath,
                                      const ImportConfig& config)
{
    pxr::UsdPhysicsJoint jointPrim = pxr::UsdPhysicsFixedJoint::Define(stage, pxr::SdfPath(jointPath));

    pxr::GfVec3f localPos0 = config.distanceScale * pxr::GfVec3f(poseJointToParentBody.p.x, poseJointToParentBody.p.y,
                                                                 poseJointToParentBody.p.z);
    pxr::GfQuatf localRot0 = pxr::GfQuatf(
        poseJointToParentBody.q.w, poseJointToParentBody.q.x, poseJointToParentBody.q.y, poseJointToParentBody.q.z);
    pxr::GfVec3f localPos1 = config.distanceScale *
                             pxr::GfVec3f(poseJointToChildBody.p.x, poseJointToChildBody.p.y, poseJointToChildBody.p.z);
    pxr::GfQuatf localRot1 = pxr::GfQuatf(
        poseJointToChildBody.q.w, poseJointToChildBody.q.x, poseJointToChildBody.q.y, poseJointToChildBody.q.z);

    /*    printf(
            "localpos0: [%f %f %f] localrot0: [%f %f %f %f] localpos1: [%f %f %f] localrot1: [%f %f %f %f]\n",
            localPos0[0], localPos0[1], localPos0[2],
            localRot0.GetReal(), localRot0.GetImaginary()[0], localRot0.GetImaginary()[1], localRot0.GetImaginary()[2],
            localPos1[0], localPos1[1], localPos1[2],
            localRot1.GetReal(), localRot1.GetImaginary()[0], localRot1.GetImaginary()[1],
       localRot1.GetImaginary()[2]);*/

    pxr::SdfPathVector val0{ pxr::SdfPath(parentBodyPath) };
    pxr::SdfPathVector val1{ pxr::SdfPath(bodyPath) };

    jointPrim.CreateBody0Rel().SetTargets(val0);
    jointPrim.CreateLocalPos0Attr().Set(localPos0);
    jointPrim.CreateLocalRot0Attr().Set(localRot0);

    jointPrim.CreateBody1Rel().SetTargets(val1);
    jointPrim.CreateLocalPos1Attr().Set(localPos1);
    jointPrim.CreateLocalRot1Attr().Set(localRot1);

    jointPrim.CreateBreakForceAttr().Set(FLT_MAX);
    jointPrim.CreateBreakTorqueAttr().Set(FLT_MAX);

    return jointPrim;
}

pxr::UsdPhysicsJoint createD6Joint(pxr::UsdStageWeakPtr stage,
                                   const std::string jointPath,
                                   const Transform& poseJointToParentBody,
                                   const Transform& poseJointToChildBody,
                                   const std::string parentBodyPath,
                                   const std::string bodyPath,
                                   const ImportConfig& config)
{
    pxr::UsdPhysicsJoint jointPrim = pxr::UsdPhysicsJoint::Define(stage, pxr::SdfPath(jointPath));

    pxr::GfVec3f localPos0 = config.distanceScale * pxr::GfVec3f(poseJointToParentBody.p.x, poseJointToParentBody.p.y,
                                                                 poseJointToParentBody.p.z);
    pxr::GfQuatf localRot0 = pxr::GfQuatf(
        poseJointToParentBody.q.w, poseJointToParentBody.q.x, poseJointToParentBody.q.y, poseJointToParentBody.q.z);
    pxr::GfVec3f localPos1 = config.distanceScale *
                             pxr::GfVec3f(poseJointToChildBody.p.x, poseJointToChildBody.p.y, poseJointToChildBody.p.z);
    pxr::GfQuatf localRot1 = pxr::GfQuatf(
        poseJointToChildBody.q.w, poseJointToChildBody.q.x, poseJointToChildBody.q.y, poseJointToChildBody.q.z);


    pxr::SdfPathVector val0{ pxr::SdfPath(parentBodyPath) };
    pxr::SdfPathVector val1{ pxr::SdfPath(bodyPath) };

    jointPrim.CreateBody0Rel().SetTargets(val0);
    jointPrim.CreateLocalPos0Attr().Set(localPos0);
    jointPrim.CreateLocalRot0Attr().Set(localRot0);

    jointPrim.CreateBody1Rel().SetTargets(val1);
    jointPrim.CreateLocalPos1Attr().Set(localPos1);
    jointPrim.CreateLocalRot1Attr().Set(localRot1);

    jointPrim.CreateBreakForceAttr().Set(FLT_MAX);
    jointPrim.CreateBreakTorqueAttr().Set(FLT_MAX);

    return jointPrim;
}

void initPhysicsJoint(pxr::UsdPhysicsJoint& jointPrim,
                      const Transform& poseJointToParentBody,
                      const Transform& poseJointToChildBody,
                      const std::string parentBodyPath,
                      const std::string bodyPath,
                      const float& distanceScale)
{
    pxr::GfVec3f localPos0 =
        distanceScale * pxr::GfVec3f(poseJointToParentBody.p.x, poseJointToParentBody.p.y, poseJointToParentBody.p.z);
    pxr::GfQuatf localRot0 = pxr::GfQuatf(
        poseJointToParentBody.q.w, poseJointToParentBody.q.x, poseJointToParentBody.q.y, poseJointToParentBody.q.z);
    pxr::GfVec3f localPos1 =
        distanceScale * pxr::GfVec3f(poseJointToChildBody.p.x, poseJointToChildBody.p.y, poseJointToChildBody.p.z);
    pxr::GfQuatf localRot1 = pxr::GfQuatf(
        poseJointToChildBody.q.w, poseJointToChildBody.q.x, poseJointToChildBody.q.y, poseJointToChildBody.q.z);

    pxr::SdfPathVector val0{ pxr::SdfPath(parentBodyPath) };
    pxr::SdfPathVector val1{ pxr::SdfPath(bodyPath) };

    jointPrim.CreateBody0Rel().SetTargets(val0);
    jointPrim.CreateLocalPos0Attr().Set(localPos0);
    jointPrim.CreateLocalRot0Attr().Set(localRot0);

    jointPrim.CreateBody1Rel().SetTargets(val1);
    jointPrim.CreateLocalPos1Attr().Set(localPos1);
    jointPrim.CreateLocalRot1Attr().Set(localRot1);

    jointPrim.CreateBreakForceAttr().Set(FLT_MAX);
    jointPrim.CreateBreakTorqueAttr().Set(FLT_MAX);
}

void applyPhysxJoint(pxr::UsdPhysicsJoint& jointPrim, const MJCFJoint* joint)
{
    pxr::PhysxSchemaPhysxJointAPI physxJoint = pxr::PhysxSchemaPhysxJointAPI::Apply(jointPrim.GetPrim());
    physxJoint.CreateArmatureAttr().Set(joint->armature);
}

void applyJointLimits(pxr::UsdPhysicsJoint jointPrim,
                      const MJCFJoint* joint,
                      const MJCFActuator* actuator,
                      const int* axisMap,
                      const int jointIdx,
                      const int numJoints,
                      const ImportConfig& config)
{
    // enable limits if set
    JointAxis axisHinge[3] = { eJointAxisTwist, eJointAxisSwing1, eJointAxisSwing2 };
    JointAxis axisSlide[3] = { eJointAxisX, eJointAxisY, eJointAxisZ };
    std::string d6Axes[6] = { "transX", "transY", "transZ", "rotX", "rotY", "rotZ" };
    int axis = -1;
    std::string limitAttr = "";

    // assume we can only have one of slide or hinge per d6 joint
    if (joint->type == MJCFJoint::SLIDE)
    {
        // lock all rotation axes
        for (int i = 3; i < 6; ++i)
        {
            pxr::UsdPhysicsLimitAPI limitAPI =
                pxr::UsdPhysicsLimitAPI::Apply(jointPrim.GetPrim(), pxr::TfToken(d6Axes[i]));
            limitAPI.CreateLowAttr().Set(1.0f);
            limitAPI.CreateHighAttr().Set(-1.0f);
        }

        axis = int(axisSlide[axisMap[jointIdx]]);

        if (joint->limited)
        {
            pxr::UsdPhysicsLimitAPI limitAPI =
                pxr::UsdPhysicsLimitAPI::Apply(jointPrim.GetPrim(), pxr::TfToken(d6Axes[axis]));
            limitAPI.CreateLowAttr().Set(config.distanceScale * joint->range.x);
            limitAPI.CreateHighAttr().Set(config.distanceScale * joint->range.y);
        }
        pxr::PhysxSchemaPhysxLimitAPI physxLimitAPI =
            pxr::PhysxSchemaPhysxLimitAPI::Apply(jointPrim.GetPrim(), pxr::TfToken(d6Axes[axis]));
        pxr::PhysxSchemaJointStateAPI::Apply(jointPrim.GetPrim(), pxr::TfToken("linear"));
        physxLimitAPI.CreateStiffnessAttr().Set(joint->stiffness);
        physxLimitAPI.CreateDampingAttr().Set(joint->damping);
    }
    else if (joint->type == MJCFJoint::HINGE)
    {
        // lock all translation axes
        for (int i = 0; i < 3; ++i)
        {
            pxr::UsdPhysicsLimitAPI limitAPI =
                pxr::UsdPhysicsLimitAPI::Apply(jointPrim.GetPrim(), pxr::TfToken(d6Axes[i]));
            limitAPI.CreateLowAttr().Set(1.0f);
            limitAPI.CreateHighAttr().Set(-1.0f);
        }
        // TODO: locking all axes at the beginning doesn't work?
        if (numJoints == 1)
        {
            pxr::UsdPhysicsLimitAPI limitAPI =
                pxr::UsdPhysicsLimitAPI::Apply(jointPrim.GetPrim(), pxr::TfToken(d6Axes[axisHinge[axisMap[1]]]));
            limitAPI.CreateLowAttr().Set(1.0f);
            limitAPI.CreateHighAttr().Set(-1.0f);
            limitAPI = pxr::UsdPhysicsLimitAPI::Apply(jointPrim.GetPrim(), pxr::TfToken(d6Axes[axisHinge[axisMap[2]]]));
            limitAPI.CreateLowAttr().Set(1.0f);
            limitAPI.CreateHighAttr().Set(-1.0f);
        }
        else if (numJoints == 2)
        {
            pxr::UsdPhysicsLimitAPI limitAPI =
                pxr::UsdPhysicsLimitAPI::Apply(jointPrim.GetPrim(), pxr::TfToken(d6Axes[axisHinge[axisMap[2]]]));
            limitAPI.CreateLowAttr().Set(1.0f);
            limitAPI.CreateHighAttr().Set(-1.0f);
        }

        axis = int(axisHinge[axisMap[jointIdx]]);

        if (joint->limited)
        {
            pxr::UsdPhysicsLimitAPI limitAPI =
                pxr::UsdPhysicsLimitAPI::Apply(jointPrim.GetPrim(), pxr::TfToken(d6Axes[axis]));
            limitAPI.CreateLowAttr().Set(joint->range.x * 180 / kPi);
            limitAPI.CreateHighAttr().Set(joint->range.y * 180 / kPi);
            pxr::PhysxSchemaPhysxLimitAPI physxLimitAPI =
                pxr::PhysxSchemaPhysxLimitAPI::Apply(jointPrim.GetPrim(), pxr::TfToken(d6Axes[axis]));
            physxLimitAPI.CreateStiffnessAttr().Set(joint->stiffness);
            physxLimitAPI.CreateDampingAttr().Set(joint->damping);
        }
        pxr::PhysxSchemaJointStateAPI::Apply(jointPrim.GetPrim(), pxr::TfToken("angular"));
    }

    jointPrim.GetPrim()
        .CreateAttribute(pxr::TfToken("mjcf:" + d6Axes[axis] + ":name"), pxr::SdfValueTypeNames->Token)
        .Set(pxr::TfToken(SanitizeUsdName(joint->name)));

    createJointDrives(jointPrim, joint, actuator, d6Axes[axis], config);
}

void createJointDrives(pxr::UsdPhysicsJoint jointPrim,
                       const MJCFJoint* joint,
                       const MJCFActuator* actuator,
                       const std::string axis,
                       const ImportConfig& config)
{
    pxr::UsdPhysicsDriveAPI driveAPI = pxr::UsdPhysicsDriveAPI::Apply(jointPrim.GetPrim(), pxr::TfToken(axis));

    driveAPI = pxr::UsdPhysicsDriveAPI::Apply(jointPrim.GetPrim(), pxr::TfToken(axis));
    driveAPI.CreateTypeAttr().Set(pxr::TfToken("force")); // TODO: when will this be acceleration?

    driveAPI.CreateDampingAttr().Set(joint->damping);
    driveAPI.CreateStiffnessAttr().Set(joint->stiffness);

    if (actuator)
    {
        MJCFActuator::Type actuatorType = actuator->type;
        if (actuatorType == MJCFActuator::MOTOR)
        {
            // nothing special?
        }
        else if (actuatorType == MJCFActuator::POSITION)
        {
            driveAPI.CreateStiffnessAttr().Set(actuator->kp);
        }
        else if (actuatorType == MJCFActuator::VELOCITY)
        {
            driveAPI.CreateStiffnessAttr().Set(actuator->kv);
        }
    }

    // TODO: add armature case
}
}
}
}
