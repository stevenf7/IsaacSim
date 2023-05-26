// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include "MjcfUtils.h"

namespace omni
{
namespace isaac
{
namespace mjcf
{

std::string SanitizeUsdName(const std::string& src)
{
    if (src.empty())
    {
        return "_";
    }
    std::string dst;
    if (std::isdigit(src[0]))
    {
        dst.push_back('_');
    }
    for (auto c : src)
    {
        if (std::isalnum(c) || c == '_')
        {
            dst.push_back(c);
        }
        else
        {
            dst.push_back('_');
        }
    }
    return dst;
}

std::string GetAttr(const tinyxml2::XMLElement* c, const char* name)
{
    if (c->Attribute(name))
    {
        return std::string(c->Attribute(name));
    }
    else
    {
        return "";
    }
}

void getIfExist(tinyxml2::XMLElement* e, const char* aname, bool& p)
{
    const char* st = e->Attribute(aname);
    if (st)
    {
        std::string s = st;
        if (s == "true")
        {
            p = true;
        }
        if (s == "1")
        {
            p = true;
        }
        if (s == "false")
        {
            p = false;
        }
        if (s == "0")
        {
            p = false;
        }
    }
}

void getIfExist(tinyxml2::XMLElement* e, const char* aname, int& p)
{
    const char* st = e->Attribute(aname);
    if (st)
    {
        sscanf(st, "%d", &p);
    }
}

void getIfExist(tinyxml2::XMLElement* e, const char* aname, float& p)
{
    const char* st = e->Attribute(aname);
    if (st)
    {
        sscanf(st, "%f", &p);
    }
}

void getIfExist(tinyxml2::XMLElement* e, const char* aname, std::string& s)
{
    const char* st = e->Attribute(aname);
    if (st)
    {
        s = st;
    }
}

void getIfExist(tinyxml2::XMLElement* e, const char* aname, Vec2& p)
{
    const char* st = e->Attribute(aname);
    if (st)
    {
        sscanf(st, "%f %f", &p.x, &p.y);
    }
}

void getIfExist(tinyxml2::XMLElement* e, const char* aname, Vec3& p)
{
    const char* st = e->Attribute(aname);
    if (st)
    {
        sscanf(st, "%f %f %f", &p.x, &p.y, &p.z);
    }
}

void getIfExist(tinyxml2::XMLElement* e, const char* aname, Vec3& from, Vec3& to)
{
    const char* st = e->Attribute(aname);
    if (st)
    {
        sscanf(st, "%f %f %f %f %f %f", &from.x, &from.y, &from.z, &to.x, &to.y, &to.z);
    }
}

void getIfExist(tinyxml2::XMLElement* e, const char* aname, Vec4& p)
{
    const char* st = e->Attribute(aname);
    if (st)
    {
        sscanf(st, "%f %f %f %f", &p.x, &p.y, &p.z, &p.w);
    }
}

void getIfExist(tinyxml2::XMLElement* e, const char* aname, Quat& q)
{
    const char* st = e->Attribute(aname);
    if (st)
    {
        sscanf(st, "%f %f %f %f", &q.w, &q.x, &q.y, &q.z);
        q = Normalize(q);
    }
}

void getEulerIfExist(tinyxml2::XMLElement* e, const char* aname, Quat& q, std::string eulerseq, bool angleInRad)
{
    const char* st = e->Attribute(aname);
    if (st)
    {
        float a, b, c;
        sscanf(st, "%f %f %f", &a, &b, &c);
        if (!angleInRad)
        {
            a = kPi * a / 180.0f;
            b = kPi * b / 180.0f;
            c = kPi * c / 180.0f;
        }

        float angles[3] = { a, b, c };
        q = Quat();

        for (int i = eulerseq.length() - 1; i >= 0; i--)
        {
            char axis = eulerseq[i];
            Quat new_quat = Quat();

            new_quat.w = cos(angles[i] / 2);

            if (axis == 'x')
            {
                new_quat.x = sin(angles[i] / 2);
            }
            else if (axis == 'y')
            {
                new_quat.y = sin(angles[i] / 2);
            }
            else if (axis == 'z')
            {
                new_quat.z = sin(angles[i] / 2);
            }
            else
            {
                std::cout << "The MJCF importer currently only supports euler sequences consisting of {x, y, z}"
                          << std::endl;
            }

            q = new_quat * q;
        }
    }
}

void getAngleAxisIfExist(tinyxml2::XMLElement* e, const char* aname, Quat& q, bool angleInRad)
{
    const char* st = e->Attribute(aname);
    if (st)
    {
        Vec3 axis;
        float angle;
        sscanf(st, "%f %f %f %f", &axis.x, &axis.y, &axis.z, &angle);

        // convert to quat
        if (!angleInRad)
        {
            angle = kPi * angle / 180.0f;
        }
        q = QuatFromAxisAngle(axis, angle);
    }
}


void getZAxisIfExist(tinyxml2::XMLElement* e, const char* aname, Quat& q)
{
    const char* st = e->Attribute(aname);
    if (st)
    {
        Vec3 zaxis;
        sscanf(st, "%f %f %f", &zaxis.x, &zaxis.y, &zaxis.z);

        Vec3 new_zaxis = zaxis;
        new_zaxis = Normalize(new_zaxis);
        Vec3 rotVec = Cross(Vec3(0.0f, 0.0f, 1.0f), new_zaxis);
        if (Length(rotVec) < 1e-5)
        {
            rotVec = Vec3(0.0f, 0.0f, 1.0f);
        }
        else
        {
            rotVec = Normalize(rotVec);
        }

        // essentially doing dot product between (0, 0, 1) and the vector and taking arccos to
        // obtain the angle between the two vectors
        float angle = acos(new_zaxis.z);
        q = QuatFromAxisAngle(rotVec, angle);
    }
}


void QuatFromZAxis(Vec3 zaxis, Quat& q)
{
    Vec3 new_zaxis = zaxis;
    new_zaxis = Normalize(new_zaxis);
    Vec3 rotVec = Cross(Vec3(0.0f, 0.0f, 1.0f), new_zaxis);
    if (Length(rotVec) < 1e-5)
    {
        rotVec = Vec3(0.0f, 0.0f, 1.0f);
    }
    else
    {
        rotVec = Normalize(rotVec);
    }

    // essentially doing dot product between (0, 0, 1) and the vector and taking arccos to
    // obtain the angle between the two vectors
    float angle = acos(new_zaxis.z);
    q = QuatFromAxisAngle(rotVec, angle);
}


PxQuat indexedRotation(PxU32 axis, PxReal s, PxReal c)
{
    PxReal v[3] = { 0, 0, 0 };
    v[axis] = s;
    return PxQuat(v[0], v[1], v[2], c);
}

PxVec3 Diagonalize(const PxMat33& m, PxQuat& massFrame)
{
    const PxU32 MAX_ITERS = 24;

    PxQuat q = PxQuat(PxIdentity);

    PxMat33 d;
    for (PxU32 i = 0; i < MAX_ITERS; i++)
    {
        PxMat33 axes(q);
        d = axes.getTranspose() * m * axes;

        PxReal d0 = PxAbs(d[1][2]), d1 = PxAbs(d[0][2]), d2 = PxAbs(d[0][1]);
        PxU32 a = PxU32(d0 > d1 && d0 > d2 ? 0 : d1 > d2 ? 1 : 2); // rotation axis index, from largest off-diagonal
        // element
        PxU32 a1 = (a + 1 + (a >> 1)) & 3, a2 = (a1 + 1 + (a1 >> 1)) & 3;

        if (d[a1][a2] == 0.0f || PxAbs(d[a1][a1] - d[a2][a2]) > 2e6f * PxAbs(2.0f * d[a1][a2]))
            break;

        PxReal w = (d[a1][a1] - d[a2][a2]) / (2.0f * d[a1][a2]); // cot(2 * phi), where phi is the rotation angle
        PxReal absw = PxAbs(w);

        PxQuat r;
        if (absw > 1000)
            r = indexedRotation(a, 1 / (4 * w), 1.f); // h will be very close to 1, so use small angle approx instead
        else
        {
            PxReal t = 1 / (absw + PxSqrt(w * w + 1)); // absolute value of tan phi
            PxReal h = 1 / PxSqrt(t * t + 1); // absolute value of cos phi

            PX_ASSERT(h != 1); // |w|<1000 guarantees this with typical IEEE754 machine eps (approx 6e-8)
            r = indexedRotation(a, PxSqrt((1 - h) / 2) * PxSign(w), PxSqrt((1 + h) / 2));
        }

        q = (q * r).getNormalized();
    }
    massFrame = q;
    return PxVec3(d.column0.x, d.column1.y, d.column2.z);
}


}
}
}
