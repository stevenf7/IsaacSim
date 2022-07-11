#pragma once

#include "MjcfImporter.h"

namespace omni
{
namespace isaac
{
namespace mjcf
{

MJCFImporter::MJCFImporter(const std::string fullPath)
{
    defaultClassName = "main";

    std::string filePath = fullPath;
    char relPathBuffer[2048];
    MakeRelativePath(filePath.c_str(), "", relPathBuffer);
    baseDirPath = std::string(relPathBuffer);

    tinyxml2::XMLDocument doc;
    tinyxml2::XMLElement* root = LoadFile(doc, filePath);
    if (!root)
    {
        return;
    }

    {
        tinyxml2::XMLDocument includeDoc;
        tinyxml2::XMLElement* includeRoot = LoadInclude(includeDoc, root->FirstChildElement("include"), baseDirPath);
        if (includeRoot)
        {
            LoadGlobals(includeRoot, defaultClassName, baseDirPath, bodies, actuators, tendons, contacts, compiler,
                        classes, simulationMeshCache, jointToActuatorIdx);
        }
    }

    LoadGlobals(root, defaultClassName, baseDirPath, bodies, actuators, tendons, contacts, compiler, classes,
                simulationMeshCache, jointToActuatorIdx);


    for (int i = 0; i < int(bodies.size()); ++i)
    {
        populateBodyLookup(bodies[i]);
    }

    computeKinematicHierarchy();


    if (!createContactGraph())
    {
        CARB_LOG_ERROR(
            "*** Could not create contact graph to compute collision groups! Are contacts specified properly?\n");
    }


    // if we got here, we win
    this->isLoaded = true;
}

MJCFImporter::~MJCFImporter()
{
    for (int i = 0; i < (int)bodies.size(); i++)
    {
        delete bodies[i];
    }
}

void MJCFImporter::populateBodyLookup(MJCFBody* body)
{
    nameToBody[body->name] = body;
    for (MJCFGeom* geom : body->geoms)
    {
        // not a visual geom
        if (!(geom->contype == 0 && geom->conaffinity == 0))
        {
            geomNameToIdx[geom->name] = int(collisionGeoms.size());
            collisionGeoms.push_back(geom);
        }
    }

    for (MJCFBody* childBody : body->bodies)
    {
        populateBodyLookup(childBody);
    }
}

bool MJCFImporter::AddPhysicsEntities(pxr::UsdStageWeakPtr stage,
                                      const Transform trans,
                                      const std::string& rootPrimPath,
                                      const ImportConfig& config)
{

    this->createBodyForFixedJoint = config.createBodyForFixedJoint;

    setStageMetadata(stage, config);

    createRoot(stage, trans, rootPrimPath, config);

    std::string instanceableUSDPath = config.instanceableMeshUsdPath;
    if (config.makeInstanceable)
    {
        pxr::UsdStageRefPtr instanceableMeshStage = pxr::UsdStage::CreateInMemory();
        setStageMetadata(instanceableMeshStage, config);
        for (int i = 0; i < (int)bodies.size(); i++)
        {
            CreateInstanceableMeshes(instanceableMeshStage, bodies[i], rootPrimPath, true, config);
        }
        instanceableMeshStage->Export(instanceableUSDPath);
    }

    for (int i = 0; i < (int)bodies.size(); i++)
    {
        CreatePhysicsBodyAndJoint(stage, bodies[i], rootPrimPath, trans, true, rootPrimPath, config, instanceableUSDPath);
    }

    // adding collision filtering pairs
    for (int i = 0; i < (int)contactGraph.size(); i++)
    {
        std::string& primPath = nameToUsdCollisionPrim[contactGraph[i].name];
        pxr::UsdPhysicsFilteredPairsAPI filteredPairsAPI =
            pxr::UsdPhysicsFilteredPairsAPI::Apply(stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        std::set<int> neighborhood = contactGraph[i].adjacentNodes;
        neighborhood.insert(i);
        for (int j = 0; j < (int)contactGraph.size(); j++)
        {
            if (neighborhood.find(j) == neighborhood.end())
            {
                std::string& filteredPrimPath = nameToUsdCollisionPrim[contactGraph[j].name];
                filteredPairsAPI.CreateFilteredPairsRel().AddTarget(pxr::SdfPath(filteredPrimPath));
            }
        }
    }

    // adding tendons
    for (const auto& t : tendons)
    {
        if (t.type == MJCFTendon::FIXED)
        {
            // setting the joint with the lowest kinematic hierarchy number as the TendonAxisRoot
            if (t.fixedJoints.size() != 0)
            {
                MJCFTendon::FixedJoint rootJoint = t.fixedJoints[0];
                for (int i = 0; i < (int)t.fixedJoints.size(); i++)
                {
                    if (jointToKinematicHierarchy[t.fixedJoints[i].joint] < jointToKinematicHierarchy[rootJoint.joint])
                    {
                        rootJoint = t.fixedJoints[i];
                    }
                }

                // adding the TendonAxisRoot api to the root joint
                pxr::VtArray<float> coef = { rootJoint.coef };
                if (revoluteJointsMap.find(rootJoint.joint) != revoluteJointsMap.end())
                {
                    pxr::UsdPhysicsRevoluteJoint rootJointPrim = revoluteJointsMap[rootJoint.joint];
                    pxr::PhysxSchemaPhysxTendonAxisRootAPI rootAPI = pxr::PhysxSchemaPhysxTendonAxisRootAPI::Apply(
                        rootJointPrim.GetPrim(), pxr::TfToken(SanitizeUsdName(t.name)));
                    if (t.limited)
                    {
                        rootAPI.CreateLowerLimitAttr().Set(t.range[0]);
                        rootAPI.CreateUpperLimitAttr().Set(t.range[1]);
                    }
                    if (t.springlength >= 0)
                    {
                        rootAPI.CreateRestLengthAttr().Set(t.springlength);
                    }
                    rootAPI.CreateStiffnessAttr().Set(t.stiffness);
                    rootAPI.CreateDampingAttr().Set(t.damping);
                    rootAPI.CreateGearingAttr().Set(coef);
                }
                else if (prismaticJointsMap.find(rootJoint.joint) != prismaticJointsMap.end())
                {
                    pxr::UsdPhysicsPrismaticJoint rootJointPrim = prismaticJointsMap[rootJoint.joint];
                    pxr::PhysxSchemaPhysxTendonAxisRootAPI rootAPI = pxr::PhysxSchemaPhysxTendonAxisRootAPI::Apply(
                        rootJointPrim.GetPrim(), pxr::TfToken(SanitizeUsdName(t.name)));
                    if (t.limited)
                    {
                        rootAPI.CreateLowerLimitAttr().Set(t.range[0]);
                        rootAPI.CreateUpperLimitAttr().Set(t.range[1]);
                    }
                    rootAPI.CreateStiffnessAttr().Set(t.stiffness);
                    rootAPI.CreateDampingAttr().Set(t.damping);
                    rootAPI.CreateGearingAttr().Set(coef);
                }
                else
                {
                    CARB_LOG_ERROR(
                        "Joint %s required for tendon %s cannot be found", rootJoint.joint.c_str(), t.name.c_str());
                }

                // adding TendonAxis api to the other joints in the tendon
                for (int i = 0; i < (int)t.fixedJoints.size(); i++)
                {
                    if (t.fixedJoints[i].joint != rootJoint.joint)
                    {
                        MJCFTendon::FixedJoint childJoint = t.fixedJoints[i];
                        pxr::VtArray<float> coef = { childJoint.coef };
                        if (revoluteJointsMap.find(childJoint.joint) != revoluteJointsMap.end())
                        {
                            pxr::UsdPhysicsRevoluteJoint childJointPrim = revoluteJointsMap[childJoint.joint];
                            pxr::PhysxSchemaPhysxTendonAxisAPI axisAPI = pxr::PhysxSchemaPhysxTendonAxisAPI::Apply(
                                childJointPrim.GetPrim(), pxr::TfToken(SanitizeUsdName(t.name)));
                            axisAPI.CreateGearingAttr().Set(coef);
                        }
                        else if (prismaticJointsMap.find(childJoint.joint) != prismaticJointsMap.end())
                        {
                            pxr::UsdPhysicsPrismaticJoint childJointPrim = prismaticJointsMap[childJoint.joint];
                            pxr::PhysxSchemaPhysxTendonAxisAPI axisAPI = pxr::PhysxSchemaPhysxTendonAxisAPI::Apply(
                                childJointPrim.GetPrim(), pxr::TfToken(SanitizeUsdName(t.name)));
                            axisAPI.CreateGearingAttr().Set(coef);
                        }
                        else
                        {
                            CARB_LOG_ERROR("Joint %s required for tendon %s cannot be found", childJoint.joint.c_str(),
                                           t.name.c_str());
                        }
                    }
                }
            }
            else
            {
                CARB_LOG_ERROR("%s cannot be added since it has no specified joints to attach to.", t.name.c_str());
            }
        }
        else
        {
            CARB_LOG_ERROR("%s is not a fixed tendom. Only fixed tendons are currently supported.", t.name.c_str());
        }
    }


    return true;
}

void MJCFImporter::CreateInstanceableMeshes(pxr::UsdStageRefPtr stage,
                                            MJCFBody* body,
                                            const std::string rootPrimPath,
                                            const bool isRoot,
                                            const ImportConfig& config)
{

    if ((!createBodyForFixedJoint) && ((body->joints.size() == 0) && (!isRoot)))
    {
        CARB_LOG_WARN("RigidBodySpec with no joint will have no geometry for now, to avoid instability of fixed joint!");
    }
    else
    {
        if (!body->inertial && body->geoms.size() == 0)
        {
            CARB_LOG_WARN("*** Neither inertial nor geometries where specified for %s", body->name.c_str());
            return;
        }

        std::string bodyPath = rootPrimPath + "/" + SanitizeUsdName(body->name);

        // Add collision geoms first to detect whether visuals are available
        for (int i = 0; i < (int)body->geoms.size(); i++)
        {
            bool isVisual = body->geoms[i]->contype == 0 && body->geoms[i]->conaffinity == 0;
            if (isVisual)
            {
                body->hasVisual = true;
            }
            else
            {
                std::string geomPath = bodyPath + "/collisions/" + SanitizeUsdName(body->geoms[i]->name);
                pxr::UsdPrim prim = createPrimitiveGeom(stage, geomPath, body->geoms[i], simulationMeshCache, config);

                // enable collisions on prim
                if (prim)
                {
                    applyCollisionGeom(stage, prim, body->geoms[i]);
                    nameToUsdCollisionPrim[body->geoms[i]->name] = bodyPath;
                }
                else
                {
                    CARB_LOG_ERROR("Collision geom %s could not be created", body->geoms[i]->name.c_str());
                }
            }
        }

        // Add visual geoms
        for (int i = 0; i < (int)body->geoms.size(); i++)
        {
            bool isVisual = body->geoms[i]->contype == 0 && body->geoms[i]->conaffinity == 0;
            if (isVisual || !body->hasVisual)
            {
                std::string geomPath = bodyPath + "/visuals/" + SanitizeUsdName(body->geoms[i]->name);
                pxr::UsdPrim prim = createPrimitiveGeom(stage, geomPath, body->geoms[i], simulationMeshCache, config);
            }
        }

        // Recursively create children's bodies
        for (int i = 0; i < (int)body->bodies.size(); i++)
        {
            CreateInstanceableMeshes(stage, body->bodies[i], rootPrimPath, false, config);
        }
    }
}


void MJCFImporter::CreatePhysicsBodyAndJoint(pxr::UsdStageWeakPtr stage,
                                             MJCFBody* body,
                                             const std::string rootPrimPath,
                                             const Transform trans,
                                             const bool isRoot,
                                             const std::string parentBodyPath,
                                             const ImportConfig& config,
                                             const std::string instanceableUsdPath)
{
    Transform myTrans;
    if (isRoot)
    {
        // ignore root link mjcf translation
        myTrans = trans * Transform(Vec3(0.0f), body->quat);
    }
    else
    {
        myTrans = trans * Transform(body->pos, body->quat);
    }

    if ((!createBodyForFixedJoint) && ((body->joints.size() == 0) && (!isRoot)))
    {
        CARB_LOG_WARN("RigidBodySpec with no joint will have no geometry for now, to avoid instability of fixed joint!");
    }
    else
    {
        if (!body->inertial && body->geoms.size() == 0)
        {
            CARB_LOG_WARN("*** Neither inertial nor geometries where specified for %s", body->name.c_str());
            return;
        }

        std::string bodyPath = rootPrimPath + "/" + SanitizeUsdName(body->name);
        pxr::UsdGeomXformable bodyPrim = createBody(stage, bodyPath, myTrans, config);

        // Add Rigid Body
        if (bodyPrim)
        {
            applyRigidBody(bodyPrim, body, config);
        }
        else
        {
            CARB_LOG_ERROR("Body prim %s could not created", body->name.c_str());
            return;
        }

        if (isRoot && config.fixBase)
        {
            pxr::UsdGeomXform rootPrim = pxr::UsdGeomXform::Define(stage, pxr::SdfPath(rootPrimPath));
            createFixedRoot(stage, rootPrimPath + "/joints/rootJoint", rootPrimPath + "/" + SanitizeUsdName(body->name));
            applyArticulationAPI(stage, rootPrim, config);
        }
        else if (isRoot)
        {
            applyArticulationAPI(stage, bodyPrim, config);
        }

        // Add collision geoms first to detect whether visuals are available
        bool hasCollisionGeoms = false;
        for (int i = 0; i < (int)body->geoms.size(); i++)
        {
            bool isVisual = body->geoms[i]->contype == 0 && body->geoms[i]->conaffinity == 0;
            if (isVisual)
            {
                body->hasVisual = true;
            }
            else
            {
                if (!config.makeInstanceable)
                {
                    std::string geomPath = bodyPath + "/collisions/" + SanitizeUsdName(body->geoms[i]->name);
                    pxr::UsdPrim prim = createPrimitiveGeom(stage, geomPath, body->geoms[i], simulationMeshCache, config);

                    // enable collisions on prim
                    if (prim)
                    {
                        applyCollisionGeom(stage, prim, body->geoms[i]);

                        nameToUsdCollisionPrim[body->geoms[i]->name] = bodyPath;
                    }
                    else
                    {
                        CARB_LOG_ERROR("Collision geom %s could not created", body->geoms[i]->name.c_str());
                    }
                }
                hasCollisionGeoms = true;
            }
        }
        if (config.makeInstanceable && hasCollisionGeoms)
        {
            // make main collisions prim instanceable and reference meshes
            pxr::SdfPath collisionsPath = pxr::SdfPath(bodyPath + "/collisions");
            pxr::UsdPrim collisionsPrim = stage->DefinePrim(collisionsPath);
            collisionsPrim.GetReferences().AddReference(instanceableUsdPath, collisionsPath);
            collisionsPrim.SetInstanceable(true);
        }

        // Add visual geoms
        bool hasVisualGeoms = false;
        for (int i = 0; i < (int)body->geoms.size(); i++)
        {
            bool isVisual = body->geoms[i]->contype == 0 && body->geoms[i]->conaffinity == 0;
            if (isVisual || !body->hasVisual)
            {
                if (!config.makeInstanceable)
                {
                    std::string geomPath = bodyPath + "/visuals/" + SanitizeUsdName(body->geoms[i]->name);
                    pxr::UsdPrim prim = createPrimitiveGeom(stage, geomPath, body->geoms[i], simulationMeshCache, config);
                }
                hasVisualGeoms = true;
            }
        }
        if (config.makeInstanceable && hasVisualGeoms)
        {
            // make main visuals prim instanceable and reference meshes
            pxr::SdfPath visualsPath = pxr::SdfPath(bodyPath + "/visuals");
            pxr::UsdPrim visualsPrim = stage->DefinePrim(visualsPath);
            visualsPrim.GetReferences().AddReference(instanceableUsdPath, visualsPath);
            visualsPrim.SetInstanceable(true);
        }

        // Add joints
        // Create joint linked to parent
        if (!isRoot)
        {
            Transform origin; // JointSpec transform
            if (body->joints.size() > 0)
            {
                origin.p = body->joints[0]->pos; // Origin at last joint (deepest)
            }
            else
            {
                origin.p = Vec3(0.0f, 0.0f, 0.0f);
            }

            // Compute joint frame and map joint axes to D6 axes
            int axisMap[3] = { 0, 1, 2 };
            computeJointFrame(origin, axisMap, body);

            origin = myTrans * origin;

            Transform ptran = trans;
            Transform mtran = myTrans;

            Transform ppose = (Inverse(ptran)) * origin;
            Transform cpose = (Inverse(mtran)) * origin;

            std::string jointPath = rootPrimPath + "/joints/" + SanitizeUsdName(body->name);
            // pxr::UsdPhysicsJoint jointPrim;

            int numJoints = (int)body->joints.size();
            if (numJoints == 0)
            {
                Transform poseJointToParentBody = Transform(body->pos, body->quat);
                Transform poseJointToChildBody = Transform();
                pxr::UsdPhysicsJoint jointPrim = createFixedJoint(
                    stage, jointPath, poseJointToParentBody, poseJointToChildBody, parentBodyPath, bodyPath, config);
            }
            else if (numJoints == 1)
            {
                Transform poseJointToParentBody = Transform(ppose.p, ppose.q);
                Transform poseJointToChildBody = Transform(cpose.p, cpose.q);
                MJCFJoint* joint = body->joints.front();
                std::string jointPath = rootPrimPath + "/joints/" + SanitizeUsdName(joint->name);

                if (joint->type == MJCFJoint::HINGE)
                {
                    pxr::UsdPhysicsRevoluteJoint jointPrim =
                        pxr::UsdPhysicsRevoluteJoint::Define(stage, pxr::SdfPath(jointPath));
                    initPhysicsJoint(jointPrim, poseJointToParentBody, poseJointToChildBody, parentBodyPath, bodyPath,
                                     config.distanceScale);

                    // joint was aligned such that its hinge axis is aligned with local x-axis.
                    jointPrim.CreateAxisAttr().Set(pxr::UsdPhysicsTokens->x);

                    if (joint->limited)
                    {
                        jointPrim.CreateLowerLimitAttr().Set(joint->range.x * 180 / kPi);
                        jointPrim.CreateUpperLimitAttr().Set(joint->range.y * 180 / kPi);
                    }

                    pxr::PhysxSchemaPhysxLimitAPI physxLimitAPI = pxr::PhysxSchemaPhysxLimitAPI::Apply(
                        jointPrim.GetPrim(), pxr::TfToken(pxr::UsdPhysicsTokens->x));
                    physxLimitAPI.CreateStiffnessAttr().Set(joint->stiffness);
                    physxLimitAPI.CreateDampingAttr().Set(joint->damping);

                    revoluteJointsMap[joint->name] = jointPrim;
                }
                else if (joint->type == MJCFJoint::SLIDE)
                {
                    pxr::UsdPhysicsPrismaticJoint jointPrim =
                        pxr::UsdPhysicsPrismaticJoint::Define(stage, pxr::SdfPath(jointPath));
                    initPhysicsJoint(jointPrim, poseJointToParentBody, poseJointToChildBody, parentBodyPath, bodyPath,
                                     config.distanceScale);

                    // joint was aligned such that its hinge axis is aligned with local x-axis.
                    jointPrim.CreateAxisAttr().Set(pxr::UsdPhysicsTokens->x);

                    if (joint->limited)
                    {
                        jointPrim.CreateLowerLimitAttr().Set(config.distanceScale * joint->range.x);
                        jointPrim.CreateUpperLimitAttr().Set(config.distanceScale * joint->range.y);
                    }

                    pxr::PhysxSchemaPhysxLimitAPI physxLimitAPI = pxr::PhysxSchemaPhysxLimitAPI::Apply(
                        jointPrim.GetPrim(), pxr::TfToken(pxr::UsdPhysicsTokens->x));
                    physxLimitAPI.CreateStiffnessAttr().Set(joint->stiffness);
                    physxLimitAPI.CreateDampingAttr().Set(joint->damping);

                    prismaticJointsMap[joint->name] = jointPrim;
                }
                else
                {
                    CARB_LOG_WARN("*** Only hinge and slide joints are supported by MJCF importer");
                }
            }
            else
            {
                Transform poseJointToParentBody = Transform(ppose.p, ppose.q);
                Transform poseJointToChildBody = Transform(cpose.p, cpose.q);
                pxr::UsdPhysicsJoint jointPrim = createD6Joint(
                    stage, jointPath, poseJointToParentBody, poseJointToChildBody, parentBodyPath, bodyPath, config);

                // TODO: this needs to be updated to support all joint types and combinations
                // Set joint limits
                for (int jid = 0; jid < (int)body->joints.size(); jid++)
                {
                    // All locked
                    for (int k = 0; k < 6; ++k)
                    {
                        body->joints[jid]->velocityLimits[k] = 100.f;
                    }

                    if (body->joints[jid]->type != MJCFJoint::HINGE && body->joints[jid]->type != MJCFJoint::SLIDE)
                    {
                        CARB_LOG_WARN("*** Only hinge and slide joints are supported by MJCF importer");
                        continue;
                    }

                    if (body->joints[jid]->ref != 0.0f)
                    {
                        CARB_LOG_WARN("Don't know how to deal with joint with ref != 0 yet");
                    }

                    // actuators - TODO: how do we set this part? what do we need to set?
                    auto actuatorIterator = jointToActuatorIdx.find(body->joints[jid]->name);
                    int actuatorIdx = actuatorIterator != jointToActuatorIdx.end() ? actuatorIterator->second : -1;
                    MJCFActuator* actuator = nullptr;
                    if (actuatorIdx != -1)
                    {
                        actuatorIdx = actuatorIterator->second;
                        actuator = &(actuators[actuatorIdx]);
                    }

                    applyJointLimits(jointPrim, body->joints[jid], actuator, axisMap, jid, numJoints, config);
                }
            }
        }

        // Recursively create children's bodies
        for (int i = 0; i < (int)body->bodies.size(); i++)
        {
            CreatePhysicsBodyAndJoint(
                stage, body->bodies[i], rootPrimPath, myTrans, false, bodyPath, config, instanceableUsdPath);
        }
    }
}

void MJCFImporter::computeJointFrame(Transform& origin, int* axisMap, const MJCFBody* body)
{
    if (body->joints.size() == 0)
    {
        origin.q = Quat();
    }
    else
    {
        if (body->joints.size() == 1)
        {
            // align D6 x-axis with the given axis
            origin.q = GetRotationQuat({ 1.0f, 0.0f, 0.0f }, body->joints[0]->axis);
        }
        else if (body->joints.size() == 2)
        {
            Quat Q = GetRotationQuat(body->joints[0]->axis, { 1.0f, 0.0f, 0.0f });
            Vec3 a = { 1.0f, 0.0f, 0.0f };
            Vec3 b = Normalize(Rotate(Q, body->joints[1]->axis));

            if (fabs(Dot(a, b)) > 1e-4f)
            {
                CARB_LOG_WARN("*** Non-othogonal joint axes are not supported");
                // exit(0);
            }

            // map third axis to D6 y- or z-axis and compute third axis accordingly
            Vec3 c;
            if (std::fabs(Dot(b, { 0.0f, 1.0f, 0.0f })) > std::fabs(Dot(b, { 0.0f, 0.0f, 1.0f })))
            {
                axisMap[1] = 1;
                c = Normalize(Cross(body->joints[0]->axis, body->joints[1]->axis));
                Matrix33 M(Normalize(body->joints[0]->axis), Normalize(body->joints[1]->axis), c);
                origin.q = Quat(M);
            }
            else
            {
                axisMap[1] = 2;
                axisMap[2] = 1;
                c = Normalize(Cross(body->joints[1]->axis, body->joints[0]->axis));
                Matrix33 M(Normalize(body->joints[0]->axis), c, Normalize(body->joints[1]->axis));
                origin.q = Quat(M);
            }
        }
        else if (body->joints.size() == 3)
        {
            Quat Q = GetRotationQuat(body->joints[0]->axis, { 1.0f, 0.0f, 0.0f });
            Vec3 a = { 1.0f, 0.0f, 0.0f };
            Vec3 b = Normalize(Rotate(Q, body->joints[1]->axis));
            Vec3 c = Normalize(Rotate(Q, body->joints[2]->axis));

            if (fabs(Dot(a, b)) > 1e-4f || fabs(Dot(a, c)) > 1e-4f || fabs(Dot(b, c)) > 1e-4f)
            {
                CARB_LOG_WARN("*** Non-othogonal joint axes are not supported");
                // exit(0);
            }

            if (std::fabs(Dot(b, { 0.0f, 1.0f, 0.0f })) > std::fabs(Dot(b, { 0.0f, 0.0f, 1.0f })))
            {
                axisMap[1] = 1;
                axisMap[2] = 2;
                Matrix33 M(Normalize(body->joints[0]->axis), Normalize(body->joints[1]->axis),
                           Normalize(body->joints[2]->axis));
                origin.q = Quat(M);
            }
            else
            {
                axisMap[1] = 2;
                axisMap[2] = 1;
                Matrix33 M(Normalize(body->joints[0]->axis), Normalize(body->joints[2]->axis),
                           Normalize(body->joints[1]->axis));
                origin.q = Quat(M);
            }
        }
        else
        {
            CARB_LOG_ERROR("*** Don't know how to handle >3 joints per body pair");
            exit(0);
        }
    }
}

bool MJCFImporter::contactBodyExclusion(MJCFBody* body1, MJCFBody* body2)
{
    // Assumes that contact graph is already set up
    // handle current geoms first
    for (MJCFGeom* geom1 : body1->geoms)
    {
        for (MJCFGeom* geom2 : body2->geoms)
        {
            auto index1 = geomNameToIdx.find(geom1->name);
            auto index2 = geomNameToIdx.find(geom2->name);
            if (index1 == geomNameToIdx.end() || index2 == geomNameToIdx.end())
            {
                return false;
            }

            int geomIndex1 = index1->second;
            int geomIndex2 = index2->second;

            contactGraph[geomIndex1].adjacentNodes.erase(geomIndex2);
            contactGraph[geomIndex2].adjacentNodes.erase(geomIndex1);
        }
    }
    return true;
}

bool MJCFImporter::createContactGraph()
{
    contactGraph = std::vector<ContactNode>{ collisionGeoms.size() };

    // initialize nodes with no contacts
    for (int i = 0; i < int(collisionGeoms.size()); ++i)
    {
        contactGraph[i].name = collisionGeoms[i]->name;
    }

    // First check pairwise compatability with contype/conaffinity
    for (int i = 0; i < int(collisionGeoms.size()) - 1; ++i)
    {
        for (int j = i + 1; j < collisionGeoms.size(); ++j)
        {
            MJCFGeom* geom1 = collisionGeoms[i];
            MJCFGeom* geom2 = collisionGeoms[j];
            if ((geom1->contype & geom2->conaffinity) || (geom2->contype && geom1->conaffinity))
            {
                contactGraph[i].adjacentNodes.insert(j);
                contactGraph[j].adjacentNodes.insert(i);
            }
        }
    }

    // Handle contact specifications
    for (auto& contact : contacts)
    {
        if (contact.type == MJCFContact::PAIR)
        {
            auto index1 = geomNameToIdx.find(contact.geom1);
            auto index2 = geomNameToIdx.find(contact.geom2);
            if (index1 == geomNameToIdx.end() || index2 == geomNameToIdx.end())
            {
                return false;
            }

            int geomIndex1 = index1->second;
            int geomIndex2 = index2->second;

            contactGraph[geomIndex1].adjacentNodes.insert(geomIndex2);
            contactGraph[geomIndex2].adjacentNodes.insert(geomIndex1);
        }
        else if (contact.type == MJCFContact::EXCLUDE)
        {
            // this is on the level of bodies, not geoms
            auto body1 = nameToBody.find(contact.body1);
            auto body2 = nameToBody.find(contact.body2);
            if (body1 == nameToBody.end() || body2 == nameToBody.end())
            {
                return false;
            }
            if (!contactBodyExclusion(body1->second, body2->second))
            {
                return false;
            }
        }
    }

    return true;
}

void MJCFImporter::computeKinematicHierarchy()
{
    // prepare bodyQueue for breadth-first search
    for (int i = 0; i < int(bodies.size()); i++)
    {
        bodyQueue.push(bodies[i]);
    }

    int level_num = 0;
    int num_bodies_at_level;

    while (bodyQueue.size() != 0)
    {
        num_bodies_at_level = bodyQueue.size();

        for (int i = 0; i < num_bodies_at_level; i++)
        {

            MJCFBody* body = bodyQueue.front();
            bodyQueue.pop();
            for (MJCFBody* childBody : body->bodies)
            {
                bodyQueue.push(childBody);
            }

            for (MJCFJoint* joint : body->joints)
            {
                jointToKinematicHierarchy[joint->name] = level_num;
            }
        }
        level_num += 1;
    }
}
}
}
}
