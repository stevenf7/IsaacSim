// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include "MjcfParser.h"

#include "MeshImporter.h"
#include "MjcfUtils.h"

#include <carb/logging/Log.h>

namespace omni
{
namespace isaac
{
namespace mjcf
{

tinyxml2::XMLElement* LoadInclude(tinyxml2::XMLDocument& doc, const tinyxml2::XMLElement* c, const std::string baseDirPath)
{
    if (c)
    {
        std::string s;
        if ((s = GetAttr(c, "file")) != "")
        {
            std::string fileName(s);
            std::string filePath = baseDirPath + fileName;

            tinyxml2::XMLElement* root = LoadFile(doc, filePath);
            return root;
        }
    }
    return nullptr;
}

void LoadCompiler(tinyxml2::XMLElement* c, MJCFCompiler& compiler)
{
    if (c)
    {
        std::string s;

        if ((s = GetAttr(c, "eulerseq")) != "")
        {
            if (s != "xyz")
            {
                std::cout << "Euler sequence other than xyz is not supported now..." << std::endl;
                exit(0);
            }
        }

        if ((s = GetAttr(c, "angle")) != "")
        {
            compiler.angleInRad = (s == "radian");
        }

        if ((s = GetAttr(c, "inertiafromgeom")) != "")
        {
            compiler.inertiafromgeom = (s == "true");
        }

        if ((s = GetAttr(c, "coordinate")) != "")
        {
            compiler.coordinateInLocal = (s == "local");
            if (!compiler.coordinateInLocal)
            {
                std::cout << "Don't know how to handle global coordinate yet!" << std::endl;
                exit(0);
            }
        }

        getIfExist(c, "meshdir", compiler.meshDir);

        // load assets
    }
}

void LoadInertial(tinyxml2::XMLElement* i, MJCFInertial& inertial)
{
    if (!i)
    {
        return;
    }
    getIfExist(i, "mass", inertial.mass);
    getIfExist(i, "pos", inertial.pos);
    getIfExist(i, "diaginertia", inertial.diaginertia);
}

void LoadGeom(tinyxml2::XMLElement* g,
              MJCFGeom& geom,
              std::string className,
              MJCFCompiler& compiler,
              std::map<std::string, MJCFClass>& classes)
{
    if (!g)
    {
        return;
    }
    if (g->Attribute("class"))
        className = g->Attribute("class");
    geom = classes[className].dgeom;

    getIfExist(g, "conaffinity", geom.conaffinity);
    getIfExist(g, "condim", geom.condim);
    getIfExist(g, "contype", geom.contype);
    getIfExist(g, "margin", geom.margin);
    getIfExist(g, "friction", geom.friction);
    getIfExist(g, "material", geom.material);
    getIfExist(g, "rgba", geom.rgba);
    getIfExist(g, "solimp", geom.solimp);
    getIfExist(g, "solref", geom.solref);
    getIfExist(g, "fromto", geom.from, geom.to);
    getIfExist(g, "zaxis", geom.zaxis);
    getIfExist(g, "size", geom.size);
    getIfExist(g, "name", geom.name);
    getIfExist(g, "pos", geom.pos);
    getEulerIfExist(g, "euler", geom.quat, compiler.eulerseq, compiler.angleInRad);
    getAngleAxisIfExist(g, "axisangle", geom.quat, compiler.angleInRad);
    getIfExist(g, "quat", geom.quat);
    getIfExist(g, "density", geom.density);
    getIfExist(g, "mesh", geom.mesh);

    if (g->Attribute("fromto"))
    {
        geom.hasFromTo = true;
    }
    if (g->Attribute("zaxis"))
    {
        geom.hasZAxis = true;
    }

    std::string type = "";
    getIfExist(g, "type", type);
    if (type == "capsule")
    {
        geom.type = MJCFGeom::CAPSULE;
    }
    else if (type == "sphere")
    {
        geom.type = MJCFGeom::SPHERE;
    }
    else if (type == "ellipsoid")
    {
        std::cout << "Ellipsoid is not natively supported, tesellated mesh will be used" << std::endl;
        geom.type = MJCFGeom::ELLIPSOID;
    }
    else if (type == "cylinder")
    {
        std::cout << "Cylinder is not natively supported, tesellated mesh will be used" << std::endl;
        geom.type = MJCFGeom::CYLINDER;
    }
    else if (type == "box")
    {
        geom.type = MJCFGeom::BOX;
    }
    else if (type == "mesh")
    {
        geom.type = MJCFGeom::MESH;
    }
    else if (type != "")
    {
        std::cout << "Geom type " << type << " not yet supported!" << std::endl;
    }

    if (geom.hasZAxis)
    {
        // Convert to quat
        geom.quat = Quat(geom.zaxis);
    }
}

void LoadActuator(tinyxml2::XMLElement* g,
                  MJCFActuator& actuator,
                  std::string className,
                  MJCFActuator::Type type,
                  std::map<std::string, MJCFClass>& classes)
{
    if (!g)
    {
        return;
    }

    if (g->Attribute("class"))
    {
        className = g->Attribute("class");
    }
    actuator = classes[className].dactuator;
    actuator.type = type;
    getIfExist(g, "ctrllimited", actuator.ctrllimited);
    getIfExist(g, "forcelimited", actuator.forcelimited);
    getIfExist(g, "ctrlrange", actuator.ctrlrange);
    getIfExist(g, "forcerange", actuator.forcerange);
    getIfExist(g, "gear", actuator.gear);
    getIfExist(g, "joint", actuator.joint);
    getIfExist(g, "name", actuator.name);

    // actuator specific attributes
    getIfExist(g, "kp", actuator.kp);
    getIfExist(g, "kv", actuator.kv);
}

void LoadContact(tinyxml2::XMLElement* g,
                 MJCFContact& contact,
                 MJCFContact::Type type,
                 std::map<std::string, MJCFClass>& classes)
{
    if (!g)
    {
        return;
    }

    getIfExist(g, "name", contact.name);
    if (type == MJCFContact::PAIR)
    {
        getIfExist(g, "geom1", contact.geom1);
        getIfExist(g, "geom2", contact.geom2);
        getIfExist(g, "condim", contact.condim);
    }
    else if (type == MJCFContact::EXCLUDE)
    {
        getIfExist(g, "body1", contact.body1);
        getIfExist(g, "body2", contact.body2);
    }
    contact.type = type;
}

void LoadTendon(tinyxml2::XMLElement* g,
                MJCFTendon& tendon,
                std::string className,
                MJCFTendon::Type type,
                std::map<std::string, MJCFClass>& classes)
{
    if (!g)
    {
        return;
    }
    if (g->Attribute("class"))
        className = g->Attribute("class");
    tendon = classes[className].dtendon;
    if (MJCFTendon::SPATIAL == type)
    {
        CARB_LOG_WARN("*** Spatial tendons are not yet supported.");
    }

    tendon.type = type;

    // parse tendon parameters:
    getIfExist(g, "name", tendon.name);
    getIfExist(g, "limited", tendon.limited);
    getIfExist(g, "range", tendon.range);
    getIfExist(g, "solimplimit", tendon.solimplimit);
    getIfExist(g, "solreflimit", tendon.solreflimit);
    getIfExist(g, "solimpfriction", tendon.solimpfriction);
    getIfExist(g, "solreffriction", tendon.solreffriction);
    getIfExist(g, "margin", tendon.margin);
    getIfExist(g, "frictionloss", tendon.frictionloss);
    getIfExist(g, "width", tendon.width);
    getIfExist(g, "material", tendon.material);
    getIfExist(g, "rgba", tendon.rgba);
    getIfExist(g, "springlength", tendon.springlength);
    if (tendon.springlength < 0.0f)
    {
        CARB_LOG_WARN("*** Automatic tendon springlength calculation is not supported (negative springlengths are,.");
    }
    getIfExist(g, "stiffness", tendon.stiffness);
    getIfExist(g, "damping", tendon.damping);

    // and then go through the joints in the fixed tendon:
    tinyxml2::XMLElement* j = g->FirstChildElement("joint");
    while (j)
    {
        // parse fixed joint:
        if (!j->Attribute("joint"))
        {
            CARB_LOG_FATAL("*** Fixed tendon joint must have a joint attribute.");
        }
        if (!j->Attribute("coef"))
        {
            CARB_LOG_FATAL("*** Fixed tendon joint must have a coef attribute.");
        }
        MJCFTendon::FixedJoint jnt;
        getIfExist(j, "joint", jnt.joint);
        getIfExist(j, "coef", jnt.coef);

        // if coef nonzero, add:
        if (0.0f != jnt.coef)
        {
            tendon.fixedJoints.push_back(jnt);
        }

        // scan for next joint in tendon:
        j = j->NextSiblingElement("joint");
    }
}


void LoadJoint(tinyxml2::XMLElement* g,
               MJCFJoint& joint,
               std::string className,
               MJCFCompiler& compiler,
               std::map<std::string, MJCFClass>& classes)
{
    if (!g)
    {
        return;
    }
    if (g->Attribute("class"))
        className = g->Attribute("class");
    joint = classes[className].djoint;

    std::string type = "";
    getIfExist(g, "type", type);
    if (type == "hinge")
    {
        joint.type = MJCFJoint::HINGE;
    }
    else if (type == "slide")
    {
        joint.type = MJCFJoint::SLIDE;
    }
    else if (type != "")
    {
        std::cout << "JointSpec type " << type << " not yet supported!" << std::endl;
    }
    getIfExist(g, "ref", joint.ref);
    getIfExist(g, "armature", joint.armature);
    getIfExist(g, "damping", joint.damping);
    getIfExist(g, "limited", joint.limited);
    getIfExist(g, "axis", joint.axis);
    getIfExist(g, "name", joint.name);
    getIfExist(g, "pos", joint.pos);
    getIfExist(g, "range", joint.range);
    if (joint.type != MJCFJoint::Type::SLIDE && !compiler.angleInRad)
    {
        // cout << "Angle in deg" << endl;
        joint.range.x = kPi * joint.range.x / 180.0f;
        joint.range.y = kPi * joint.range.y / 180.0f;
    }
    getIfExist(g, "stiffness", joint.stiffness);
    joint.axis = Normalize(joint.axis);
}


void LoadDefault(tinyxml2::XMLElement* e,
                 const std::string className,
                 MJCFClass& cl,
                 MJCFCompiler& compiler,
                 std::map<std::string, MJCFClass>& classes)
{
    LoadJoint(e->FirstChildElement("joint"), cl.djoint, className, compiler, classes);
    LoadGeom(e->FirstChildElement("geom"), cl.dgeom, className, compiler, classes);
    LoadTendon(e->FirstChildElement("tendon"), cl.dtendon, className, MJCFTendon::DEFAULT, classes);

    // A defaults class should have one general actuator element, so only one of these should be sucessful
    LoadActuator(e->FirstChildElement("motor"), cl.dactuator, className, MJCFActuator::MOTOR, classes);
    LoadActuator(e->FirstChildElement("position"), cl.dactuator, className, MJCFActuator::POSITION, classes);
    LoadActuator(e->FirstChildElement("velocity"), cl.dactuator, className, MJCFActuator::VELOCITY, classes);

    tinyxml2::XMLElement* d = e->FirstChildElement("default");
    while (d)
    {
        // While there is child default
        // Must have name
        if (!d->Attribute("class"))
        {
            std::cout << "Non-top level class must have name" << std::endl;
            exit(0);
        }

        std::string name = d->Attribute("class");
        classes[name] = cl; // Copy from this class
        LoadDefault(d, name, classes[name], compiler, classes); // Recursively load it
        d = d->NextSiblingElement("default");
    }
}

void LoadBody(tinyxml2::XMLElement* g,
              std::vector<MJCFBody*>& bodies,
              MJCFBody& body,
              std::string className,
              MJCFCompiler& compiler,
              std::map<std::string, MJCFClass>& classes)
{
    if (!g)
    {
        return;
    }

    if (g->Attribute("childclass"))
    {
        className = g->Attribute("childclass");
    }
    getIfExist(g, "name", body.name);
    getIfExist(g, "pos", body.pos);
    getEulerIfExist(g, "euler", body.quat, compiler.eulerseq, compiler.angleInRad);
    getAngleAxisIfExist(g, "axisangle", body.quat, compiler.angleInRad);
    getIfExist(g, "quat", body.quat);

    // Load interial
    tinyxml2::XMLElement* c = g->FirstChildElement("inertial");
    if (c)
    {
        body.inertial = new MJCFInertial();
        LoadInertial(c, *body.inertial);
    }

    // Load geoms
    c = g->FirstChildElement("geom");
    while (c)
    {
        body.geoms.push_back(new MJCFGeom());
        LoadGeom(c, *body.geoms.back(), className, compiler, classes);
        c = c->NextSiblingElement("geom");
    }

    // Load joints
    c = g->FirstChildElement("joint");
    while (c)
    {
        body.joints.push_back(new MJCFJoint());
        LoadJoint(c, *body.joints.back(), className, compiler, classes);
        c = c->NextSiblingElement("joint");
    }

    // Load child bodies
    c = g->FirstChildElement("body");
    while (c)
    {
        body.bodies.push_back(new MJCFBody());
        LoadBody(c, bodies, *body.bodies.back(), className, compiler, classes);
        c = c->NextSiblingElement("body");
    }
}

tinyxml2::XMLElement* LoadFile(tinyxml2::XMLDocument& doc, const std::string filePath)
{
    if (doc.LoadFile(filePath.c_str()) != tinyxml2::XML_SUCCESS)
    {
        CARB_LOG_ERROR("*** Failed to load '%s'", filePath.c_str());
        return nullptr;
    }

    tinyxml2::XMLElement* root = doc.RootElement();
    if (!root)
    {
        CARB_LOG_ERROR("*** Empty document '%s'", filePath.c_str());
    }

    return root;
}

void LoadAssets(tinyxml2::XMLElement* a,
                std::string baseDirPath,
                MJCFCompiler& compiler,
                std::map<std::string, MeshInfo>& simulationMeshCache,
                std::map<std::string, MJCFMesh>& meshes,
                std::map<std::string, MJCFMaterial>& materials,
                std::map<std::string, MJCFTexture>& textures)
{
    tinyxml2::XMLElement* m = a->FirstChildElement("mesh");
    while (m)
    {
        std::string meshName;
        std::string meshFile;
        Vec3 meshScale = Vec3(1.0f);

        getIfExist(m, "name", meshName);
        getIfExist(m, "file", meshFile);
        getIfExist(m, "scale", meshScale);

        std::string meshPath = baseDirPath + compiler.meshDir + "/" + meshFile;

        MJCFMesh mMesh = MJCFMesh();
        mMesh.name = meshName;
        mMesh.filename = meshFile;
        mMesh.scale = meshScale;

        meshes[meshName] = mMesh;

        std::map<std::string, MeshInfo>::iterator it = simulationMeshCache.find(meshName);
        Mesh* mesh = nullptr;
        TriangleMeshHandle trimesh;
        const float dilation = 0.005f;

        if (it == simulationMeshCache.end())
        {
            Vec3 scale{ 1.f };
            mesh::MeshImporter meshImporter;
            mesh = meshImporter.loadMeshAssimp(meshPath.c_str(), scale, GymMeshNormalMode::eComputePerFace);

            if (!mesh)
            {
                CARB_LOG_ERROR("*** Failed to load '%s'!\n", meshPath.c_str());
            }

            if (meshScale.x != 1.0f || meshScale.y != 1.0f || meshScale.z != 1.0f)
            {
                mesh->Transform(ScaleMatrix(meshScale));
            }

            mesh->name = meshName;

            // use flat normals on collision shapes
            mesh->CalculateFaceNormals();
            GymMeshHandle gymMeshHandle = -1;
            // CreateTriangleMesh(sim, mesh, dilation, &trimesh, &gymMeshHandle);

            MeshInfo meshInfo;
            meshInfo.mesh = mesh;
            // meshInfo.meshId = trimesh;
            meshInfo.meshHandle = gymMeshHandle;
            simulationMeshCache[meshName] = meshInfo;
        }
        else
        {
            mesh = it->second.mesh;
            trimesh = it->second.meshId;
        }

        m = m->NextSiblingElement("mesh");
    }

    tinyxml2::XMLElement* mat = a->FirstChildElement("material");
    while (mat)
    {
        std::string matName = "", texture = "";
        float matSpecular = 0.5f, matShininess = 0.0f;
        Vec4 rgba = Vec4(0.2f, 0.2f, 0.2f, 1.0f);

        getIfExist(mat, "name", matName);
        getIfExist(mat, "specular", matSpecular);
        getIfExist(mat, "shininess", matShininess);
        getIfExist(mat, "texture", texture);
        getIfExist(mat, "rgba", rgba);

        MJCFMaterial material = MJCFMaterial();
        material.name = matName;
        material.texture = texture;
        material.specular = matSpecular;
        material.shininess = matShininess;
        material.rgba = rgba;

        materials[matName] = material;
        mat = mat->NextSiblingElement("material");
    }

    tinyxml2::XMLElement* tex = a->FirstChildElement("texture");
    while (tex)
    {
        std::string texName = "", texFile = "", gridsize = "", gridlayout = "", type = "";

        getIfExist(tex, "name", texName);
        getIfExist(tex, "file", texFile);
        getIfExist(tex, "gridsize", gridsize);
        getIfExist(tex, "gridlayout", gridlayout);
        getIfExist(tex, "type", type);

        if (texFile != "")
        {
            texFile = baseDirPath + texFile;
        }

        MJCFTexture texture = MJCFTexture();
        texture.name = texName;
        texture.filename = texFile;
        texture.gridsize = gridsize;
        texture.gridlayout = gridlayout;
        texture.type = type;

        textures[texName] = texture;
        tex = tex->NextSiblingElement("texture");
    }
}


void LoadGlobals(tinyxml2::XMLElement* root,
                 std::string& defaultClassName,
                 std::string baseDirPath,
                 std::vector<MJCFBody*>& bodies,
                 std::vector<MJCFActuator>& actuators,
                 std::vector<MJCFTendon>& tendons,
                 std::vector<MJCFContact>& contacts,
                 std::map<std::string, MeshInfo>& simulationMeshCache,
                 std::map<std::string, MJCFMesh>& meshes,
                 std::map<std::string, MJCFMaterial>& materials,
                 std::map<std::string, MJCFTexture>& textures,
                 MJCFCompiler& compiler,
                 std::map<std::string, MJCFClass>& classes,
                 std::map<std::string, int>& jointToActuatorIdx)
{
    LoadCompiler(root->FirstChildElement("compiler"), compiler);

    // Deal with defaults
    tinyxml2::XMLElement* d = root->FirstChildElement("default");
    if (!d)
    {
        // No default, set the defaultClassName to default if it does not exist yet
        // preist@: Added this condition to avoid overwriting default class parameters
        // parsed in a prior call
        if (classes.find(defaultClassName) == classes.end())
        {
            classes[defaultClassName] = MJCFClass();
        }
    }
    else
    {
        // Only handle one top level default
        if (d->Attribute("class"))
            defaultClassName = d->Attribute("class");
        classes[defaultClassName] = MJCFClass();
        LoadDefault(d, defaultClassName, classes[defaultClassName], compiler, classes);
        if (d->NextSiblingElement("default"))
        {
            CARB_LOG_ERROR("*** Can only handle one top level default at the moment!");
            return;
        }
    }

    tinyxml2::XMLElement* a = root->FirstChildElement("asset");
    if (a)
    {
        {
            tinyxml2::XMLDocument includeDoc;
            tinyxml2::XMLElement* includeRoot = LoadInclude(includeDoc, a->FirstChildElement("include"), baseDirPath);
            if (includeRoot)
            {
                LoadAssets(includeRoot, baseDirPath, compiler, simulationMeshCache, meshes, materials, textures);
            }
        }

        LoadAssets(a, baseDirPath, compiler, simulationMeshCache, meshes, materials, textures);
    }

    tinyxml2::XMLElement* wb = root->FirstChildElement("worldbody");
    if (wb)
    {
        {
            tinyxml2::XMLDocument includeDoc;
            tinyxml2::XMLElement* includeRoot = LoadInclude(includeDoc, wb->FirstChildElement("include"), baseDirPath);
            if (includeRoot)
            {
                tinyxml2::XMLElement* c = includeRoot->FirstChildElement("body");
                while (c)
                {
                    bodies.push_back(new MJCFBody());
                    LoadBody(c, bodies, *bodies.back(), defaultClassName, compiler, classes);
                    c = c->NextSiblingElement("body");
                }
            }
        }

        tinyxml2::XMLElement* c = wb->FirstChildElement("body");
        while (c)
        {
            bodies.push_back(new MJCFBody());
            LoadBody(c, bodies, *bodies.back(), defaultClassName, compiler, classes);
            c = c->NextSiblingElement("body");
        }
    }

    tinyxml2::XMLElement* ac = root->FirstChildElement("actuator");
    if (ac)
    {
        tinyxml2::XMLElement* c = ac->FirstChildElement();
        while (c)
        {
            MJCFActuator::Type type;
            std::string elementName{ c->Name() };
            if (elementName == "motor")
            {
                type = MJCFActuator::MOTOR;
            }
            else if (elementName == "position")
            {
                type = MJCFActuator::POSITION;
            }
            else if (elementName == "velocity")
            {
                type = MJCFActuator::VELOCITY;
            }
            else
            {
                CARB_LOG_ERROR("*** Only motor, position, velocity actuators supported");
                continue;
            }

            MJCFActuator actuator;
            LoadActuator(c, actuator, defaultClassName, type, classes);
            jointToActuatorIdx[actuator.joint] = int(actuators.size());
            actuators.push_back(actuator);
            c = c->NextSiblingElement();
        }
    }

    // load tendons
    tinyxml2::XMLElement* tc = root->FirstChildElement("tendon");
    if (tc)
    {
        {
            // do fixed tendons first
            tinyxml2::XMLElement* c = tc->FirstChildElement("fixed");
            while (c)
            {
                MJCFTendon tendon;
                LoadTendon(c, tendon, defaultClassName, MJCFTendon::FIXED, classes);
                tendons.push_back(tendon);
                c = c->NextSiblingElement("fixed");
            }
        }
        {
            // do spatial tendons next
            tinyxml2::XMLElement* c = tc->FirstChildElement("spatial");
            while (c)
            {
                MJCFTendon tendon;
                LoadTendon(c, tendon, defaultClassName, MJCFTendon::SPATIAL, classes);
                tendons.push_back(tendon);
                c = c->NextSiblingElement("spatial");
            }
        }
    }

    tinyxml2::XMLElement* cc = root->FirstChildElement("contact");
    if (cc)
    {
        tinyxml2::XMLElement* c = cc->FirstChildElement();
        while (c)
        {
            MJCFContact::Type type;
            std::string elementName{ c->Name() };
            if (elementName == "pair")
            {
                type = MJCFContact::PAIR;
            }
            else if (elementName == "exclude")
            {
                type = MJCFContact::EXCLUDE;
            }
            else
            {
                CARB_LOG_ERROR("*** Invalid contact specification");
                continue;
            }

            MJCFContact contact;
            LoadContact(c, contact, type, classes);
            contacts.push_back(contact);
            c = c->NextSiblingElement();
        }
    }
}

}
}
}
