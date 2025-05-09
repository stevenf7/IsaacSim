// SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#pragma once

#include "math/core/maths.h"

#include <tinyxml2.h>

namespace isaacsim
{
namespace asset
{
namespace importer
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
void getZAxisIfExist(tinyxml2::XMLElement* e, const char* aname, Quat& q);
void getAngleAxisIfExist(tinyxml2::XMLElement* e, const char* aname, Quat& q, bool angleInRad);
Quat indexedRotation(int axis, float s, float c);
Vec3 Diagonalize(const Matrix33& m, Quat& massFrame);

} // namespace mjcf
} // namespace importer
} // namespace asset
} // namespace isaacsim
