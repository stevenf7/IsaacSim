// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <omni/isaac/urdf/UrdfTypes.h>

#include <tinyxml2.h>
namespace omni
{
namespace isaac
{
namespace urdf
{

// Parsers

bool parseJointType(const std::string& str, UrdfJointType& type);

bool parseOrigin(const tinyxml2::XMLElement& element, Transform& origin);

bool parseAxis(const tinyxml2::XMLElement& element, UrdfAxis& axis);

bool parseLimit(const tinyxml2::XMLElement& element, UrdfLimit& limit);

bool parseDynamics(const tinyxml2::XMLElement& element, UrdfDynamics& dynamics);

bool parseMass(const tinyxml2::XMLElement& element, float& mass);

bool parseInertia(const tinyxml2::XMLElement& element, UrdfInertia& inertia);

bool parseInertial(const tinyxml2::XMLElement& element, UrdfInertial& inertial);

bool parseGeometry(const tinyxml2::XMLElement& element, UrdfGeometry& geometry);

bool parseMaterial(const tinyxml2::XMLElement& element, UrdfMaterial& material);

bool parseMaterials(const tinyxml2::XMLElement& root, std::map<std::string, UrdfMaterial>& urdfMaterials);

bool parseLinks(const tinyxml2::XMLElement& root, std::map<std::string, UrdfLink>& urdfLinks);

bool parseJoints(const tinyxml2::XMLElement& root, std::map<std::string, UrdfJoint>& urdfJoints);

bool parseUrdf(const std::string& urdfPackagePath, const std::string& urdfFileRelativeToPackage, UrdfRobot& urdfRobot);

} // namespace urdf
}
}
