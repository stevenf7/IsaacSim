// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "MjcfImporter.h"

namespace omni
{
namespace isaac
{
namespace mjcf
{

MJCFImporter::MJCFImporter(const std::string fullPath, ImportConfig& config)
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


    // if the mjcf file contains <include file="....">, load the included file as well
    {
        tinyxml2::XMLDocument includeDoc;
        tinyxml2::XMLElement* includeElement = root->FirstChildElement("include");
        tinyxml2::XMLElement* includeRoot = LoadInclude(includeDoc, includeElement, baseDirPath);
        while (includeRoot)
        {
            LoadGlobals(includeRoot, defaultClassName, baseDirPath, worldBody, bodies, actuators, tendons, contacts,
                        simulationMeshCache, meshes, materials, textures, compiler, classes, jointToActuatorIdx, config);

            includeElement = includeElement->NextSiblingElement("include");
            includeRoot = LoadInclude(includeDoc, includeElement, baseDirPath);
        }
    }

    LoadGlobals(root, defaultClassName, baseDirPath, worldBody, bodies, actuators, tendons, contacts,
                simulationMeshCache, meshes, materials, textures, compiler, classes, jointToActuatorIdx, config);


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

    // loading is complete if it reaches here
    this->isLoaded = true;
}

MJCFImporter::~MJCFImporter()
{
    for (int i = 0; i < (int)bodies.size(); i++)
    {
        delete bodies[i];
    }
    for (int i = 0; i < (int)actuators.size(); i++)
    {
        delete actuators[i];
    }
    for (int i = 0; i < (int)tendons.size(); i++)
    {
        delete tendons[i];
    }
    for (int i = 0; i < (int)contacts.size(); i++)
    {
        delete contacts[i];
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
        if (config.instanceableMeshUsdPath[0] == '.')
        {
            // make relative path relative to output directory
            std::string relativePath = config.instanceableMeshUsdPath.substr(1);
            std::string curStagePath = stage->GetRootLayer()->GetIdentifier();
            std::string directory;
            size_t pos = curStagePath.find_last_of("\\/");
            directory = (std::string::npos == pos) ? "" : curStagePath.substr(0, pos);
            instanceableUSDPath = directory + relativePath;
        }
        pxr::UsdStageRefPtr instanceableMeshStage = pxr::UsdStage::CreateNew(instanceableUSDPath);
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

    addWorldGeomsAndSites(stage, rootPrimPath, config);
    AddContactFilters(stage);
    AddTendons(stage, rootPrimPath);

    return true;
}

bool MJCFImporter::addVisualGeom(pxr::UsdStageWeakPtr stage,
                                 pxr::UsdPrim bodyPrim,
                                 MJCFBody* body,
                                 std::string bodyPath,
                                 const ImportConfig& config,
                                 bool createGeoms)
{
    bool hasVisualGeoms = false;
    for (int i = 0; i < (int)body->geoms.size(); i++)
    {
        bool isVisual = body->geoms[i]->contype == 0 && body->geoms[i]->conaffinity == 0;
        if (isVisual || !body->hasVisual || config.visualizeCollisionGeoms)
        {
            if (!config.makeInstanceable || createGeoms)
            {
                std::string geomPath = bodyPath + "/visuals/" + SanitizeUsdName(body->geoms[i]->name);
                pxr::UsdPrim prim =
                    createPrimitiveGeom(stage, geomPath, body->geoms[i], simulationMeshCache, config, true);

                // parse material and texture
                if (body->geoms[i]->material != "")
                {
                    if (materials.find(body->geoms[i]->material) != materials.end())
                    {
                        MJCFMaterial material = materials.find(body->geoms[i]->material)->second;
                        MJCFTexture* texture = nullptr;
                        if (material.texture != "")
                        {
                            if (textures.find(material.texture) == textures.end())
                            {
                                CARB_LOG_ERROR("Cannot find texture with name %s.\n", material.texture.c_str());
                            }
                            texture = &(textures.find(material.texture)->second);
                        }
                        Vec4 color = Vec4();
                        createAndBindMaterial(stage, prim, &material, texture, color, false);
                    }
                    else
                    {
                        CARB_LOG_ERROR("Cannot find material with name %s.\n", body->geoms[i]->material.c_str());
                    }
                }
                else if (body->geoms[i]->rgba.x != 0.2 || body->geoms[i]->rgba.y != 0.2 || body->geoms[i]->rgba.z != 0.2)
                {
                    // create material with color only
                    createAndBindMaterial(stage, prim, nullptr, nullptr, body->geoms[i]->rgba, true);
                }
                geomPrimMap[body->geoms[i]->name] = prim;
            }
            // if (bodyPrim)
            geomToBodyPrim[body->geoms[i]->name] = bodyPrim;
            hasVisualGeoms = true;
        }
    }
    return hasVisualGeoms;
}

void MJCFImporter::addVisualSites(
    pxr::UsdStageWeakPtr stage, pxr::UsdPrim bodyPrim, MJCFBody* body, std::string bodyPath, const ImportConfig& config)
{
    for (int i = 0; i < (int)body->sites.size(); i++)
    {
        std::string sitePath = bodyPath + "/sites/" + SanitizeUsdName(body->sites[i]->name);
        pxr::UsdPrim prim;
        if (body->sites[i]->hasGeom)
        {
            prim = createPrimitiveGeom(stage, sitePath, body->sites[i], config, true);

            // parse material and texture
            if (body->sites[i]->material != "")
            {
                if (materials.find(body->sites[i]->material) != materials.end())
                {
                    MJCFMaterial material = materials.find(body->sites[i]->material)->second;
                    MJCFTexture* texture = nullptr;
                    if (material.texture != "")
                    {
                        if (textures.find(material.texture) == textures.end())
                        {
                            CARB_LOG_ERROR("Cannot find texture with name %s.\n", material.texture.c_str());
                        }
                        texture = &(textures.find(material.texture)->second);
                    }
                    Vec4 color = Vec4();
                    createAndBindMaterial(stage, prim, &material, texture, color, false);
                }
                else
                {
                    CARB_LOG_ERROR("Cannot find material with name %s.\n", body->geoms[i]->material.c_str());
                }
            }
            else if (body->sites[i]->rgba.x != 0.2 || body->sites[i]->rgba.y != 0.2 || body->sites[i]->rgba.z != 0.2)
            {
                // create material with color only
                createAndBindMaterial(stage, prim, nullptr, nullptr, body->sites[i]->rgba, true);
            }
        }
        else
        {
            prim = pxr::UsdGeomXform::Define(stage, pxr::SdfPath(sitePath)).GetPrim();
        }
        sitePrimMap[body->sites[i]->name] = prim;
        siteToBodyPrim[body->sites[i]->name] = bodyPrim;
    }
}

void MJCFImporter::addWorldGeomsAndSites(pxr::UsdStageWeakPtr stage, std::string rootPath, const ImportConfig& config)
{
    // we have to create a dummy link to place the sites/geoms defined in the world body
    std::string bodyPath = rootPath + "/dummyLinkForWorld";
    pxr::UsdPrim dummyLink = pxr::UsdGeomXform::Define(stage, pxr::SdfPath(bodyPath)).GetPrim();
    pxr::UsdPhysicsRigidBodyAPI physicsAPI = pxr::UsdPhysicsRigidBodyAPI::Apply(dummyLink);
    pxr::PhysxSchemaPhysxRigidBodyAPI::Apply(dummyLink);

    // fix the dummy link to the root
    std::string jointPath = bodyPath + "/fixedJoint";
    pxr::UsdPhysicsJoint jointPrim = pxr::UsdPhysicsFixedJoint::Define(stage, pxr::SdfPath(jointPath));
    pxr::SdfPathVector val0{ pxr::SdfPath(rootPath) };
    pxr::SdfPathVector val1{ pxr::SdfPath(jointPath) };
    jointPrim.CreateBody0Rel().SetTargets(val0);
    jointPrim.CreateBody1Rel().SetTargets(val1);

    bool hasVisualGeoms = addVisualGeom(stage, dummyLink, &worldBody, bodyPath, config, true);
    addVisualSites(stage, dummyLink, &worldBody, bodyPath, config);
}

void MJCFImporter::AddContactFilters(pxr::UsdStageWeakPtr stage)
{
    // adding collision filtering pairs
    for (int i = 0; i < (int)contactGraph.size(); i++)
    {
        std::string& primPath = nameToUsdCollisionPrim[contactGraph[i]->name];
        pxr::UsdPhysicsFilteredPairsAPI filteredPairsAPI =
            pxr::UsdPhysicsFilteredPairsAPI::Apply(stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        std::set<int> neighborhood = contactGraph[i]->adjacentNodes;
        neighborhood.insert(i);
        for (int j = 0; j < (int)contactGraph.size(); j++)
        {
            if (neighborhood.find(j) == neighborhood.end())
            {
                std::string& filteredPrimPath = nameToUsdCollisionPrim[contactGraph[j]->name];
                filteredPairsAPI.CreateFilteredPairsRel().AddTarget(pxr::SdfPath(filteredPrimPath));
            }
        }
    }
}

void MJCFImporter::AddTendons(pxr::UsdStageWeakPtr stage, std::string rootPath)
{
    // adding tendons
    for (const auto& t : tendons)
    {
        if (t->type == MJCFTendon::FIXED)
        {
            // setting the joint with the lowest kinematic hierarchy number as the TendonAxisRoot
            if (t->fixedJoints.size() != 0)
            {
                MJCFTendon::FixedJoint* rootJoint = t->fixedJoints[0];
                for (int i = 0; i < (int)t->fixedJoints.size(); i++)
                {
                    if (jointToKinematicHierarchy[t->fixedJoints[i]->joint] < jointToKinematicHierarchy[rootJoint->joint])
                    {
                        rootJoint = t->fixedJoints[i];
                    }
                }

                // adding the TendonAxisRoot api to the root joint
                pxr::VtArray<float> coef = { rootJoint->coef };
                if (revoluteJointsMap.find(rootJoint->joint) != revoluteJointsMap.end())
                {
                    pxr::UsdPhysicsRevoluteJoint rootJointPrim = revoluteJointsMap[rootJoint->joint];
                    pxr::PhysxSchemaPhysxTendonAxisRootAPI rootAPI = pxr::PhysxSchemaPhysxTendonAxisRootAPI::Apply(
                        rootJointPrim.GetPrim(), pxr::TfToken(SanitizeUsdName(t->name)));
                    if (t->limited)
                    {
                        rootAPI.CreateLowerLimitAttr().Set(t->range[0]);
                        rootAPI.CreateUpperLimitAttr().Set(t->range[1]);
                    }
                    if (t->springlength >= 0)
                    {
                        rootAPI.CreateRestLengthAttr().Set(t->springlength);
                    }
                    rootAPI.CreateStiffnessAttr().Set(t->stiffness);
                    rootAPI.CreateDampingAttr().Set(t->damping);
                    rootAPI.CreateGearingAttr().Set(coef);
                }
                else if (prismaticJointsMap.find(rootJoint->joint) != prismaticJointsMap.end())
                {
                    pxr::UsdPhysicsPrismaticJoint rootJointPrim = prismaticJointsMap[rootJoint->joint];
                    pxr::PhysxSchemaPhysxTendonAxisRootAPI rootAPI = pxr::PhysxSchemaPhysxTendonAxisRootAPI::Apply(
                        rootJointPrim.GetPrim(), pxr::TfToken(SanitizeUsdName(t->name)));
                    if (t->limited)
                    {
                        rootAPI.CreateLowerLimitAttr().Set(t->range[0]);
                        rootAPI.CreateUpperLimitAttr().Set(t->range[1]);
                    }
                    rootAPI.CreateStiffnessAttr().Set(t->stiffness);
                    rootAPI.CreateDampingAttr().Set(t->damping);
                    rootAPI.CreateGearingAttr().Set(coef);
                }
                else
                {
                    CARB_LOG_ERROR(
                        "Joint %s required for tendon %s cannot be found", rootJoint->joint.c_str(), t->name.c_str());
                }

                // adding TendonAxis api to the other joints in the tendon
                for (int i = 0; i < (int)t->fixedJoints.size(); i++)
                {
                    if (t->fixedJoints[i]->joint != rootJoint->joint)
                    {
                        MJCFTendon::FixedJoint* childJoint = t->fixedJoints[i];
                        pxr::VtArray<float> coef = { childJoint->coef };
                        if (revoluteJointsMap.find(childJoint->joint) != revoluteJointsMap.end())
                        {
                            pxr::UsdPhysicsRevoluteJoint childJointPrim = revoluteJointsMap[childJoint->joint];
                            pxr::PhysxSchemaPhysxTendonAxisAPI axisAPI = pxr::PhysxSchemaPhysxTendonAxisAPI::Apply(
                                childJointPrim.GetPrim(), pxr::TfToken(SanitizeUsdName(t->name)));
                            axisAPI.CreateGearingAttr().Set(coef);
                        }
                        else if (prismaticJointsMap.find(childJoint->joint) != prismaticJointsMap.end())
                        {
                            pxr::UsdPhysicsPrismaticJoint childJointPrim = prismaticJointsMap[childJoint->joint];
                            pxr::PhysxSchemaPhysxTendonAxisAPI axisAPI = pxr::PhysxSchemaPhysxTendonAxisAPI::Apply(
                                childJointPrim.GetPrim(), pxr::TfToken(SanitizeUsdName(t->name)));
                            axisAPI.CreateGearingAttr().Set(coef);
                        }
                        else
                        {
                            CARB_LOG_ERROR("Joint %s required for tendon %s cannot be found", childJoint->joint.c_str(),
                                           t->name.c_str());
                        }
                    }
                }
            }
            else
            {
                CARB_LOG_ERROR("%s cannot be added since it has no specified joints to attach to.", t->name.c_str());
            }
        }
        else if (t->type == MJCFTendon::SPATIAL)
        {
            std::map<std::string, int> attachmentNames;
            bool isFirstAttachment = true;

            if (t->spatialAttachments.size() > 0)
            {
                for (auto it = t->spatialBranches.begin(); it != t->spatialBranches.end(); it++)
                {
                    std::vector<MJCFTendon::SpatialAttachment*> attachments = it->second;
                    pxr::UsdPrim parentPrim;
                    std::string parentName;
                    for (int i = (int)attachments.size() - 1; i >= 0; --i)
                    {
                        MJCFTendon::SpatialAttachment* attachment = attachments[i];
                        std::string name;
                        pxr::UsdPrim linkPrim;
                        bool hasLink = false;
                        if (attachment->type == MJCFTendon::SpatialAttachment::GEOM)
                        {
                            name = attachment->geom;
                            if (geomToBodyPrim.find(name) != geomToBodyPrim.end())
                            {
                                linkPrim = geomToBodyPrim[name];
                                hasLink = true;
                            }
                        }
                        else if (attachment->type == MJCFTendon::SpatialAttachment::SITE)
                        {
                            name = attachment->site;
                            if (siteToBodyPrim.find(name) != siteToBodyPrim.end())
                            {
                                linkPrim = siteToBodyPrim[name];
                                hasLink = true;
                            }
                        }
                        if (!hasLink)
                        {
                            pxr::UsdPrim dummyLink = stage->GetPrimAtPath(pxr::SdfPath(rootPath + "/dummyLinkForWorld"));

                            // check if they are part of the world sites/geoms
                            if (attachment->type == MJCFTendon::SpatialAttachment::GEOM)
                            {
                                name = attachment->geom;
                                linkPrim = dummyLink;
                                geomToBodyPrim[name] = dummyLink;
                                hasLink = true;
                            }
                            else if (attachment->type == MJCFTendon::SpatialAttachment::SITE)
                            {
                                name = attachment->site;
                                linkPrim = dummyLink;
                                siteToBodyPrim[name] = dummyLink;
                                hasLink = true;
                            }

                            if (!hasLink)
                            {
                                // we shouldn't be here...
                                CARB_LOG_ERROR(
                                    "Error adding attachment %s. Failed to find attached link.\n", name.c_str());
                            }
                        }

                        // create additional attachments if duplicates are found
                        if (attachmentNames.find(name) != attachmentNames.end())
                        {
                            attachmentNames[name]++;
                            name = name + "_" + std::to_string(attachmentNames[name] - 1);
                        }
                        else
                        {
                            attachmentNames[name] = 0;
                        }

                        // setting the first attachment link as the AttachmentRoot
                        if (isFirstAttachment)
                        {
                            isFirstAttachment = false;
                            parentPrim = linkPrim;
                            parentName = name;
                            auto rootApi =
                                pxr::PhysxSchemaPhysxTendonAttachmentRootAPI::Apply(linkPrim, pxr::TfToken(name));
                            pxr::GfVec3f localPos = GetLocalPos(*attachment);
                            pxr::PhysxSchemaPhysxTendonAttachmentAPI(rootApi, pxr::TfToken(name))
                                .CreateLocalPosAttr()
                                .Set(localPos);
                            rootApi.CreateStiffnessAttr().Set(t->stiffness);
                            rootApi.CreateDampingAttr().Set(t->damping);
                        }
                        // last attachment point
                        else if (i == 0)
                        {
                            auto leafApi =
                                pxr::PhysxSchemaPhysxTendonAttachmentLeafAPI::Apply(linkPrim, pxr::TfToken(name));
                            pxr::PhysxSchemaPhysxTendonAttachmentAPI(leafApi, pxr::TfToken(name))
                                .CreateParentLinkRel()
                                .AddTarget(parentPrim.GetPath());
                            pxr::PhysxSchemaPhysxTendonAttachmentAPI(leafApi, pxr::TfToken(name))
                                .CreateParentAttachmentAttr()
                                .Set(pxr::TfToken(parentName));
                            pxr::GfVec3f localPos = GetLocalPos(*attachment);
                            pxr::PhysxSchemaPhysxTendonAttachmentAPI(leafApi, pxr::TfToken(name))
                                .CreateLocalPosAttr()
                                .Set(localPos);
                        }
                        // intermediate attachment point
                        else
                        {
                            auto attachmentApi =
                                pxr::PhysxSchemaPhysxTendonAttachmentAPI::Apply(linkPrim, pxr::TfToken(name));
                            attachmentApi.CreateParentLinkRel().AddTarget(parentPrim.GetPath());
                            attachmentApi.CreateParentAttachmentAttr().Set(pxr::TfToken(parentName));
                            pxr::GfVec3f localPos = GetLocalPos(*attachment);
                            attachmentApi.CreateLocalPosAttr().Set(localPos);
                        }

                        // set current body as parent
                        parentName = name;
                        parentPrim = linkPrim;
                    }
                }
            }
            else
            {
                CARB_LOG_ERROR(
                    "Spatial tendon %s cannot be added since it has no attachments specified.", t->name.c_str());
            }
        }
        else
        {
            CARB_LOG_ERROR(
                "Tendon %s is not a fixed or spatial tendon. Only fixed and spatial tendons are currently supported.",
                t->name.c_str());
        }
    }
}

pxr::GfVec3f MJCFImporter::GetLocalPos(MJCFTendon::SpatialAttachment attachment)
{
    pxr::GfVec3f localPos;
    if (attachment.type == MJCFTendon::SpatialAttachment::GEOM)
    {
        if (geomToBodyPrim.find(attachment.geom) != geomToBodyPrim.end())
        {
            const pxr::UsdPrim rootPrim = geomToBodyPrim[attachment.geom];
            const pxr::UsdPrim geomPrim = geomPrimMap[attachment.geom];
            pxr::GfVec3d geomTranslate = pxr::UsdGeomXformable(geomPrim)
                                             .ComputeLocalToWorldTransform(pxr::UsdTimeCode::Default())
                                             .ExtractTranslation();
            pxr::GfVec3d linkTranslate = pxr::UsdGeomXformable(rootPrim)
                                             .ComputeLocalToWorldTransform(pxr::UsdTimeCode::Default())
                                             .ExtractTranslation();
            localPos = pxr::GfVec3f(geomTranslate - linkTranslate);
        }
    }
    else if (attachment.type == MJCFTendon::SpatialAttachment::SITE)
    {
        if (siteToBodyPrim.find(attachment.site) != siteToBodyPrim.end())
        {
            pxr::UsdPrim rootPrim = siteToBodyPrim[attachment.site];
            pxr::UsdPrim sitePrim = sitePrimMap[attachment.site];
            pxr::GfVec3d siteTranslate = pxr::UsdGeomXformable(sitePrim)
                                             .ComputeLocalToWorldTransform(pxr::UsdTimeCode::Default())
                                             .ExtractTranslation();
            pxr::GfVec3d linkTranslate = pxr::UsdGeomXformable(rootPrim)
                                             .ComputeLocalToWorldTransform(pxr::UsdTimeCode::Default())
                                             .ExtractTranslation();
            localPos = pxr::GfVec3f(siteTranslate - linkTranslate);
        }
    }
    return localPos;
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

        // add collision geoms first to detect whether visuals are available
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
                pxr::UsdPrim prim =
                    createPrimitiveGeom(stage, geomPath, body->geoms[i], simulationMeshCache, config, false);

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

        // add visual geoms
        addVisualGeom(stage, pxr::UsdPrim(), body, bodyPath, config, true);

        // recursively create children's bodies
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

        // add Rigid Body
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

        // add collision geoms first to detect whether visuals are available
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
                    pxr::UsdPrim prim =
                        createPrimitiveGeom(stage, geomPath, body->geoms[i], simulationMeshCache, config, false);

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

        // add visual geoms
        bool hasVisualGeoms = addVisualGeom(stage, bodyPrim.GetPrim(), body, bodyPath, config, false);
        if (config.makeInstanceable && hasVisualGeoms)
        {
            // make main visuals prim instanceable and reference meshes
            pxr::SdfPath visualsPath = pxr::SdfPath(bodyPath + "/visuals");
            pxr::UsdPrim visualsPrim = stage->DefinePrim(visualsPath);
            visualsPrim.GetReferences().AddReference(instanceableUsdPath, visualsPath);
            visualsPrim.SetInstanceable(true);
        }

        // add sites
        if (config.importSites)
        {
            addVisualSites(stage, bodyPrim.GetPrim(), body, bodyPath, config);
        }

        // add joints
        // create joint linked to parent
        if (!isRoot)
        {
            // jointSpec transform
            Transform origin;
            if (body->joints.size() > 0)
            {
                // origin at last joint (deepest)
                origin.p = body->joints[0]->pos;
            }
            else
            {
                origin.p = Vec3(0.0f, 0.0f, 0.0f);
            }

            // compute joint frame and map joint axes to D6 axes
            int axisMap[3] = { 0, 1, 2 };
            computeJointFrame(origin, axisMap, body);

            origin = myTrans * origin;

            Transform ptran = trans;
            Transform mtran = myTrans;

            Transform ppose = (Inverse(ptran)) * origin;
            Transform cpose = (Inverse(mtran)) * origin;

            std::string jointPath = rootPrimPath + "/joints/" + SanitizeUsdName(body->name);

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

                auto actuatorIterator = jointToActuatorIdx.find(joint->name);
                int actuatorIdx = actuatorIterator != jointToActuatorIdx.end() ? actuatorIterator->second : -1;
                MJCFActuator* actuator = nullptr;
                if (actuatorIdx != -1)
                {
                    actuatorIdx = actuatorIterator->second;
                    actuator = actuators[actuatorIdx];
                }

                if (joint->type == MJCFJoint::HINGE)
                {
                    pxr::UsdPhysicsRevoluteJoint jointPrim =
                        pxr::UsdPhysicsRevoluteJoint::Define(stage, pxr::SdfPath(jointPath));
                    initPhysicsJoint(jointPrim, poseJointToParentBody, poseJointToChildBody, parentBodyPath, bodyPath,
                                     config.distanceScale);
                    applyPhysxJoint(jointPrim, joint);

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

                    createJointDrives(jointPrim, joint, actuator, "X", config);
                }
                else if (joint->type == MJCFJoint::SLIDE)
                {
                    pxr::UsdPhysicsPrismaticJoint jointPrim =
                        pxr::UsdPhysicsPrismaticJoint::Define(stage, pxr::SdfPath(jointPath));
                    initPhysicsJoint(jointPrim, poseJointToParentBody, poseJointToChildBody, parentBodyPath, bodyPath,
                                     config.distanceScale);
                    applyPhysxJoint(jointPrim, joint);

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

                    createJointDrives(jointPrim, joint, actuator, "X", config);
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
                applyPhysxJoint(jointPrim, body->joints[0]);

                // TODO: this needs to be updated to support all joint types and combinations
                // set joint limits
                for (int jid = 0; jid < (int)body->joints.size(); jid++)
                {
                    // all locked
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
                        actuator = actuators[actuatorIdx];
                    }

                    applyJointLimits(jointPrim, body->joints[jid], actuator, axisMap, jid, numJoints, config);
                }
            }
        }

        // recursively create children's bodies
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
        if (geom1->conaffinity & geom1->contype)
        {
            for (MJCFGeom* geom2 : body2->geoms)
            {
                if (geom2->conaffinity & geom2->contype)
                {
                    auto index1 = geomNameToIdx.find(geom1->name);
                    auto index2 = geomNameToIdx.find(geom2->name);
                    if (index1 == geomNameToIdx.end() || index2 == geomNameToIdx.end())
                    {
                        return false;
                    }

                    int geomIndex1 = index1->second;
                    int geomIndex2 = index2->second;

                    contactGraph[geomIndex1]->adjacentNodes.erase(geomIndex2);
                    contactGraph[geomIndex2]->adjacentNodes.erase(geomIndex1);
                }
            }
        }
    }
    return true;
}

bool MJCFImporter::createContactGraph()
{
    contactGraph = std::vector<ContactNode*>();

    // initialize nodes with no contacts
    for (int i = 0; i < int(collisionGeoms.size()); ++i)
    {
        ContactNode* node = new ContactNode();
        node->name = collisionGeoms[i]->name;
        contactGraph.push_back(node);
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
                contactGraph[i]->adjacentNodes.insert(j);
                contactGraph[j]->adjacentNodes.insert(i);
            }
        }
    }

    // Handle contact specifications
    for (auto& contact : contacts)
    {
        if (contact->type == MJCFContact::PAIR)
        {
            auto index1 = geomNameToIdx.find(contact->geom1);
            auto index2 = geomNameToIdx.find(contact->geom2);
            if (index1 == geomNameToIdx.end() || index2 == geomNameToIdx.end())
            {
                return false;
            }

            int geomIndex1 = index1->second;
            int geomIndex2 = index2->second;

            contactGraph[geomIndex1]->adjacentNodes.insert(geomIndex2);
            contactGraph[geomIndex2]->adjacentNodes.insert(geomIndex1);
        }
        else if (contact->type == MJCFContact::EXCLUDE)
        {
            // this is on the level of bodies, not geoms
            auto body1 = nameToBody.find(contact->body1);
            auto body2 = nameToBody.find(contact->body2);
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
