// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include <pxr/base/vt/array.h>
#include <pxr/base/vt/token.h>
#include <pxr/pxr.h>
#include <pxr/usd/usd/attribute.h>
#include <pxr/usd/usd/prim.h>
#include <pxr/usd/usd/relationship.h>

#include <unordered_map>

namespace isaacsim
{
namespace robot
{
namespace schema
{

// Enum for classes
enum class Classes
{
    ROBOT_API,
    LINK_API,
    REFERENCE_POINT_API,
    JOINT_API
};

// Enum for attributes
enum class Attributes
{
    DESCRIPTION,
    NAMESPACE,
    INDEX,
    NAME_OVERRIDE,
    FORWARD_AXIS,
    JOINT_INDEX,
    ROT_X_OFFSET,
    ROT_Y_OFFSET,
    ROT_Z_OFFSET,
    TR_X_OFFSET,
    TR_Y_OFFSET,
    TR_Z_OFFSET,
    ACCELERATION_LIMIT,
    JERK_LIMIT,
    ACTUATOR
};

// Enum for relations
enum class Relations
{
    ROBOT_LINKS,
    ROBOT_JOINTS
};

// Common prefix token
const pxr::VtToken _attrPrefix = pxr::VtToken("isaac");

// Map of class names
const std::string classNames[] = { "RobotAPI", "LinkAPI", "ReferencePointAPI", "JointAPI" };

// Map of attribute names and types
const std::unordered_map<Attributes, std::pair<pxr::VtToken, pxr::SdfValueTypeNames>> attributeNames = {
    { Attributes::DESCRIPTION, { pxr::VtToken("description"), pxr::SdfValueTypeNames::String } },
    { Attributes::NAMESPACE, { pxr::VtToken("namespace"), pxr::SdfValueTypeNames::String } },
    { Attributes::INDEX, { pxr::VtToken("physics:index"), pxr::SdfValueTypeNames::Int } },
    { Attributes::NAME_OVERRIDE, { pxr::VtToken("nameOverride"), pxr::SdfValueTypeNames::String } },
    { Attributes::FORWARD_AXIS, { pxr::VtToken("forwardAxis"), pxr::SdfValueTypeNames::Token } },
    { Attributes::JOINT_INDEX, { pxr::VtToken("physics:index"), pxr::SdfValueTypeNames::Int } },
    { Attributes::ROT_X_OFFSET, { pxr::VtToken("physics:Rot_X:DofOffset"), pxr::SdfValueTypeNames::Int } },
    { Attributes::ROT_Y_OFFSET, { pxr::VtToken("physics:Rot_Y:DofOffset"), pxr::SdfValueTypeNames::Int } },
    { Attributes::ROT_Z_OFFSET, { pxr::VtToken("physics:Rot_Z:DofOffset"), pxr::SdfValueTypeNames::Int } },
    { Attributes::TR_X_OFFSET, { pxr::VtToken("physics:Tr_X:DofOffset"), pxr::SdfValueTypeNames::Int } },
    { Attributes::TR_Y_OFFSET, { pxr::VtToken("physics:Tr_Y:DofOffset"), pxr::SdfValueTypeNames::Int } },
    { Attributes::TR_Z_OFFSET, { pxr::VtToken("physics:Tr_Z:DofOffset"), pxr::SdfValueTypeNames::Int } },
    { Attributes::ACCELERATION_LIMIT, { pxr::VtToken("physics:AccelerationLimit"), pxr::SdfValueTypeNames::FloatArray } },
    { Attributes::JERK_LIMIT, { pxr::VtToken("physics:JerkLimit"), pxr::SdfValueTypeNames::FloatArray } },
    { Attributes::ACTUATOR, { pxr::VtToken("physics:JerkLimit"), pxr::SdfValueTypeNames::BoolArray } }
};

// List of relation names
const std::vector<std::pair<pxr::VtToken, pxr::VtToken>> relationNames = {
    { pxr::VtToken("physics:robotLinks"), pxr::VtToken("robotLinks") },
    { pxr::VtToken("physics:robotjoints"), pxr::VtToken("robotjoints") }
};

// Function to get attribute name
pxr::VtToken getAttributeName(Attributes attr)
{
    return _attrPrefix + attributeNames.at(attr).first;
}

// Function to apply RobotAPI
void ApplyRobotAPI(pxr::UsdPrim& prim)
{
    prim.AddAppliedSchema(classNames[static_cast<int>(Classes::ROBOT_API)]);
    for (const auto& attr : { Attributes::DESCRIPTION, Attributes::NAMESPACE })
    {
        prim.CreateAttribute(getAttributeName(attr), attributeNames.at(attr).second, true);
    }
    for (const auto& rel : relationNames)
    {
        prim.CreateRelationship(rel.first, rel.second, true);
    }
}

// Function to apply LinkAPI
void ApplyLinkAPI(pxr::UsdPrim& prim)
{
    prim.AddAppliedSchema(classNames[static_cast<int>(Classes::LINK_API)]);
    for (const auto& attr : { Attributes::NAME_OVERRIDE })
    {
        prim.CreateAttribute(getAttributeName(attr), attributeNames.at(attr).second, true);
    }
}

// Function to apply ReferencePointAPI
void ApplyReferencePointAPI(pxr::UsdPrim& prim)
{
    prim.AddAppliedSchema(classNames[static_cast<int>(Classes::REFERENCE_POINT_API)]);
    for (const auto& attr : { Attributes::DESCRIPTION, Attributes::FORWARD_AXIS })
    {
        prim.CreateAttribute(getAttributeName(attr), attributeNames.at(attr).second, true);
    }
}

// Function to apply JointAPI
void ApplyJointAPI(pxr::UsdPrim& prim)
{
    prim.AddAppliedSchema(classNames[static_cast<int>(Classes::JOINT_API)]);
    for (const auto& attr :
         { Attributes::JOINT_INDEX, Attributes::ROT_X_OFFSET, Attributes::ROT_Y_OFFSET, Attributes::ROT_Z_OFFSET,
           Attributes::TR_X_OFFSET, Attributes::TR_Y_OFFSET, Attributes::TR_Z_OFFSET, Attributes::NAME_OVERRIDE,
           Attributes::ACCELERATION_LIMIT, Attributes::JERK_LIMIT })
    {
        prim.CreateAttribute(getAttributeName(attr), attributeNames.at(attr).second, true);
    }
}
}
}
}
