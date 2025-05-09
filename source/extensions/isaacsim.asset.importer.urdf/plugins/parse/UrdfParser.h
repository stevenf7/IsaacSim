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

#include "../UrdfTypes.h"

#include <tinyxml2.h>
namespace isaacsim
{
namespace asset
{
namespace importer
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

bool parseLoopJoints(const tinyxml2::XMLElement& element, std::map<std::string, UrdfLoopJoint>& loopJoints);

bool parseFixedFrames(const tinyxml2::XMLElement& element, std::map<std::string, UrdfLink>& links);

bool parseJoints(const tinyxml2::XMLElement& root, std::map<std::string, UrdfJoint>& urdfJoints);

float computeSimpleStiffness(const UrdfRobot& robot, std::string joint, float naturalFrequency);

bool parseSensors(const tinyxml2::XMLElement& root, std::map<std::string, UrdfLink>& urdfLinks);

bool parseUrdf(const std::string& urdfPackagePath, const std::string& urdfFileRelativeToPackage, UrdfRobot& urdfRobot);

bool parseUrdfString(const std::string& urdf_str, UrdfRobot& urdfRobot);

bool findRootLink(const std::map<std::string, UrdfLink>& urdfLinks,
                  const std::map<std::string, UrdfJoint>& urdfJoints,
                  std::string& rootLinkName);

} // namespace urdf
}
}
}
