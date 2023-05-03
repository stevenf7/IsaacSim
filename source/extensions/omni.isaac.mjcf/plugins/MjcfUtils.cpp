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
        // Euler
        if (eulerseq != "xyz")
        {
            std::cout << "Only support xyz Euler seq" << std::endl;
            exit(0);
        }

        float a, b, c;
        sscanf(st, "%f %f %f", &a, &b, &c);
        if (!angleInRad)
        {
            a = kPi * a / 180.0f;
            b = kPi * b / 180.0f;
            c = kPi * c / 180.0f;
        }
        // mujoco xyz rotation is an intrinsic rotation about x, then rotated y, then twice rotated z
        q = euler_xyz2quat(a, b, c);
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

}
}
}
