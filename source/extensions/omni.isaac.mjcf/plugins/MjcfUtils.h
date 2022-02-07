// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <omni/isaac/math/core/maths.h>

#include <tinyxml2.h>

namespace omni
{
namespace isaac
{
namespace mjcf
{

std::string SanitizeUsdName(const std::string& src);
std::string GetAttr(const tinyxml2::XMLElement* c, const char* name);

void getIfExist(tinyxml2::XMLElement* e, const char* aname, bool& p);
void getIfExist(tinyxml2::XMLElement* e, const char* aname, int& p);
void getIfExist(tinyxml2::XMLElement* e, const char* aname, float& p);
void getIfExist(tinyxml2::XMLElement* e, const char* aname, std::string& s);
void getIfExist(tinyxml2::XMLElement* e, const char* aname, Vec2& p);
void getIfExist(tinyxml2::XMLElement* e, const char* aname, Vec3& p);
void getIfExist(tinyxml2::XMLElement* e, const char* aname, Vec3& from, Vec3& to);
void getIfExist(tinyxml2::XMLElement* e, const char* aname, Vec4& p);
void getIfExist(tinyxml2::XMLElement* e, const char* aname, Quat& q);
void getEulerIfExist(tinyxml2::XMLElement* e, const char* aname, Quat& q, std::string eulerseq, bool angleInRad);
void getAngleAxisIfExist(tinyxml2::XMLElement* e, const char* aname, Quat& q, bool angleInRad);

}
}
}
