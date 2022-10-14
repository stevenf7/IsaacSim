// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include "core/mesh.h"

#include <omni/isaac/math/core/maths.h>

#include <set>
#include <vector>

namespace omni
{
namespace isaac
{
namespace mjcf
{

typedef unsigned int TriangleMeshHandle;
typedef int64_t GymMeshHandle;

struct MeshInfo
{
    Mesh* mesh = nullptr;
    TriangleMeshHandle meshId = -1;
    GymMeshHandle meshHandle = -1;
};

struct ContactNode
{
    std::string name;
    std::set<int> adjacentNodes;
};

class MJCFJoint
{
public:
    enum Type
    {
        HINGE,
        SLIDE
    };

    std::string name;
    Type type;
    bool limited;

    float armature;
    // dynamics
    float stiffness;
    float damping;
    float friction;

    // axis
    Vec3 axis;
    float ref;

    Vec3 pos; // aka origin's position: origin is {position, quat}
    // limits
    Vec2 range; // lower to upper joint limit
    float velocityLimits[6];

    float initVal;

    MJCFJoint()
    {
        armature = 0.0f;
        damping = 0.0f;
        limited = false;
        axis = Vec3(1.0f, 0.0f, 0.0f);
        name = "";

        pos = Vec3(0.0f, 0.0f, 0.0f);
        range = Vec2(0.0f, 0.0f);
        stiffness = 0.0f;
        friction = 0.0f;
        type = HINGE;

        ref = 0.0f;
        initVal = 0.0f;
    }
};

class MJCFGeom
{
public:
    enum Type
    {
        CAPSULE,
        SPHERE,
        ELLIPSOID,
        CYLINDER,
        BOX,
        MESH
    };

    float density;
    int conaffinity;
    int condim;
    int contype;
    float margin;

    Vec3 friction; // Sliding Torsion Rolling

    std::string material;
    Vec4 rgba;
    Vec3 solimp;
    Vec2 solref;
    Vec3 from;
    Vec3 to;
    Vec3 size;

    std::string name;
    Vec3 pos;
    Type type;
    Quat quat;
    Vec4 axisangle;
    Vec3 zaxis;

    std::string mesh;

    bool hasFromTo;
    bool hasZAxis;

    MJCFGeom()
    {
        conaffinity = 1;
        condim = 3;
        contype = 1;
        margin = 0.0f;
        friction = Vec3(1.0f, 0.005f, 0.0001f);

        material = "";
        rgba = Vec4(0.5f, 0.5f, 0.5f, 1.0f);

        solimp = Vec3(0.9f, 0.95f, 0.001f);
        solref = Vec2(0.02f, 1.0f);

        from = Vec3(0.0f, 0.0f, 0.0f);
        to = Vec3(0.0f, 0.0f, 0.0f);
        size = Vec3(1.0f, 1.0f, 1.0f);

        name = "";

        pos = Vec3(0.0f, 0.0f, 0.0f);
        type = SPHERE;
        density = 1000.0f;

        quat = Quat();
        hasFromTo = false;
        hasZAxis = false;
    }
};

class MJCFInertial
{
public:
    float mass;
    Vec3 pos;
    Vec3 diaginertia;

    MJCFInertial()
    {
        mass = -1.0f;
        pos = Vec3(0.0f, 0.0f, 0.0f);
        diaginertia = Vec3(0.0f, 0.0f, 0.0f);
    }
};

enum JointAxis
{
    eJointAxisX, //!< Corresponds to translation around the body0 x-axis
    eJointAxisY, //!< Corresponds to translation around the body0 y-axis
    eJointAxisZ, //!< Corresponds to translation around the body0 z-axis
    eJointAxisTwist, //!< Corresponds to rotation around the body0 x-axis
    eJointAxisSwing1, //!< Corresponds to rotation around the body0 y-axis
    eJointAxisSwing2, //!< Corresponds to rotation around the body0 z-axis
};


class MJCFBody
{
public:
    std::string name;
    Vec3 pos;
    Quat quat;
    MJCFInertial* inertial;
    std::vector<MJCFGeom*> geoms;
    std::vector<MJCFJoint*> joints;
    std::vector<MJCFBody*> bodies;
    bool hasVisual;

    MJCFBody()
    {
        name = "";
        pos = Vec3(0.0f, 0.0f, 0.0f);
        quat = Quat();
        inertial = nullptr;
        geoms.clear();
        joints.clear();
        bodies.clear();
        hasVisual = false;
    }

    ~MJCFBody()
    {
        if (inertial)
        {
            delete inertial;
        }

        for (int i = 0; i < (int)geoms.size(); i++)
        {
            delete geoms[i];
        }

        for (int i = 0; i < (int)joints.size(); i++)
        {
            delete joints[i];
        }

        for (int i = 0; i < (int)bodies.size(); i++)
        {
            delete bodies[i];
        }
    }
};


class MJCFCompiler
{
public:
    bool angleInRad;
    bool inertiafromgeom;
    bool coordinateInLocal;
    std::string eulerseq;
    std::string meshDir;

    MJCFCompiler()
    {
        eulerseq = "xyz";
        angleInRad = false;
        inertiafromgeom = true;
        coordinateInLocal = true;
    }
};

class MJCFContact
{
public:
    enum Type
    {
        PAIR,
        EXCLUDE,
        DEFAULT
    };

    Type type;

    std::string name;

    std::string geom1, geom2;
    int condim;

    std::string body1, body2;

    MJCFContact()
    {
        type = DEFAULT;

        name = "";
        geom1 = "";
        geom2 = "";
        body1 = "";
        body2 = "";
        int condim = 3;
    }
};

class MJCFActuator
{
public:
    enum Type
    {
        MOTOR,
        POSITION,
        VELOCITY,
        DEFAULT
    };

    Type type;

    bool ctrllimited;
    bool forcelimited;

    Vec2 ctrlrange;
    Vec2 forcerange;

    float gear;
    std::string joint;
    std::string name;

    float kp, kv;

    MJCFActuator()
    {
        type = DEFAULT;

        ctrllimited = false;
        forcelimited = false;

        ctrlrange = Vec2(-1.0f, 1.0f);
        forcerange = Vec2(-FLT_MAX, FLT_MAX);

        gear = 0.0f;
        name = "";
        joint = "";

        kp = 0.f;
        kv = 0.f;
    }
};

class MJCFTendon
{
public:
    enum Type
    {
        SPATIAL = 0,
        FIXED,
        DEFAULT // flag for default tendon
    };

    struct FixedJoint
    {
        std::string joint;
        float coef;
    };

    Type type;

    std::string name;
    bool limited;
    Vec2 range;

    // limit and friction solver params:
    Vec3 solimplimit;
    Vec2 solreflimit;
    Vec3 solimpfriction;
    Vec2 solreffriction;

    float margin;
    float frictionloss;

    float width;
    std::string material;
    Vec4 rgba;

    float springlength;
    float stiffness;
    float damping;

    std::vector<FixedJoint> fixedJoints;

    MJCFTendon()
    {
        type = FIXED;
        limited = false;
        range = Vec2(0.0f, 0.0f);

        solimplimit = Vec3(0.9f, 0.95f, 0.001f);
        solreflimit = Vec2(0.02f, 1.0f);
        solimpfriction = Vec3(0.9f, 0.95f, 0.001f);
        solreffriction = Vec2(0.02f, 1.0f);

        margin = 0.0f;
        frictionloss = 0.0f;

        width = 0.003f;
        material = "";
        rgba = Vec4(0.5f, 0.5f, 0.5f, 1.0f);

        // was previously commented out
        float springLength = 0.0f;
        float stiffness = 0.0f;
        float damping = 0.0f;
    }
};

class MJCFMesh
{
public:
    std::string name;
    std::string filename;
    Vec3 scale;

    MJCFMesh()
    {
        name = "";
        filename = "";
        scale = Vec3(1.0f);
    }
};

class MJCFTexture
{
public:
    std::string name;
    std::string filename;

    std::string gridsize;
    std::string gridlayout;
    std::string type;

    MJCFTexture()
    {
        name = "";
        filename = "";
        gridsize = "";
        gridlayout = "";
        type = "";
    }
};

class MJCFMaterial
{
public:
    std::string name;
    std::string texture;
    float specular;
    float roughness;
    float shininess;
    Vec4 rgba;

    MJCFMaterial()
    {
        name = "";
        texture = "";
        specular = 0.5f;
        roughness = 0.5f;
        shininess = 0.0f; // metallic
        rgba = Vec4(0.2f, 0.2f, 0.2f, 1.0f);
    }
};

class MJCFClass
{
public:
    MJCFJoint djoint;
    MJCFGeom dgeom;
    MJCFActuator dactuator;
    MJCFTendon dtendon;
    std::string name;
};


} // namespace mjcf
}
}
