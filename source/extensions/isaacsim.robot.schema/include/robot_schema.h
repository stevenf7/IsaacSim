// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include <pxr/pxr.h>
#include <pxr/usd/usd/attribute.h>
#include <pxr/usd/usd/prim.h>
#include <pxr/usd/usd/schemaBase.h>

PXR_NAMESPACE_USING_DIRECTIVE

namespace isaacsim
{
namespace robot
{
namespace schema
{


enum class Classes
{
    ROBOT_API,
    LINK_API,
    REFERENCE_POINT_API,
    JOINT_API
};

const TfToken _attrPrefix = "isaac";

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
    JERK_LIMIT
};

const std::pair<TfToken, SdfValueType> attributeInfo[] = {
    { TfToken(_attrPrefix.GetString() + ":description"), SdfValueTypeNames->String },
    { TfToken(_attrPrefix.GetString() + ":namespace"), SdfValueTypeNames->String },
    { TfToken(_attrPrefix.GetString() + ":physics:index"), SdfValueTypeNames->Int },
    { TfToken(_attrPrefix.GetString() + ":nameOverride"), SdfValueTypeNames->String },
    { TfToken(_attrPrefix.GetString() + ":forwardAxis"), SdfValueTypeNames->Token },
    { TfToken(_attrPrefix.GetString() + ":physics:index"), SdfValueTypeNames->Int },
    { TfToken(_attrPrefix.GetString() + ":physics:Rot_X:DofOffset"), SdfValueTypeNames->Int },
    { TfToken(_attrPrefix.GetString() + ":physics:Rot_Y:DofOffset"), SdfValueTypeNames->Int },
    { TfToken(_attrPrefix.GetString() + ":physics:Rot_Z:DofOffset"), SdfValueTypeNames->Int },
    { TfToken(_attrPrefix.GetString() + ":physics:Tr_X:DofOffset"), SdfValueTypeNames->Int },
    { TfToken(_attrPrefix.GetString() + ":physics:Tr_Y:DofOffset"), SdfValueTypeNames->Int },
    { TfToken(_attrPrefix.GetString() + ":physics:Tr_Z:DofOffset"), SdfValueTypeNames->Int },
    { TfToken(_attrPrefix.GetString() + ":physics:AccelerationLimit"), SdfValueTypeNames->FloatArray },
    { TfToken(_attrPrefix.GetString() + ":physics:JerkLimit"), SdfValueTypeNames->FloatArray }
};

void ApplyRobotAPI(UsdPrim& prim)
{
    prim.AddAppliedSchema(SdfPath(TfToken("RobotAPI")));
    for (const auto& attr : { Attributes::DESCRIPTION, Attributes::NAMESPACE })
    {
        prim.CreateAttribute(attributeInfo[static_cast<int>(attr)].first, attributeInfo[static_cast<int>(attr)].second);
    }
}

void ApplyLinkAPI(UsdPrim& prim)
{
    prim.AddAppliedSchema(SdfPath(TfToken("LinkAPI")));
    for (const auto& attr : { Attributes::INDEX, Attributes::NAME_OVERRIDE })
    {
        prim.CreateAttribute(attributeInfo[static_cast<int>(attr)].first, attributeInfo[static_cast<int>(attr)].second);
    }
}

void ApplyReferencePointAPI(UsdPrim& prim)
{
    prim.AddAppliedSchema(SdfPath(TfToken("ReferencePointAPI")));
    for (const auto& attr : { Attributes::DESCRIPTION, Attributes::FORWARD_AXIS })
    {
        prim.CreateAttribute(attributeInfo[static_cast<int>(attr)].first, attributeInfo[static_cast<int>(attr)].second);
    }
}

void ApplyJointAPI(UsdPrim& prim)
{
    prim.AddAppliedSchema(SdfPath(TfToken("JointAPI")));
    for (const auto& attr :
         { Attributes::JOINT_INDEX, Attributes::ROT_X_OFFSET, Attributes::ROT_Y_OFFSET, Attributes::ROT_Z_OFFSET,
           Attributes::TR_X_OFFSET, Attributes::TR_Y_OFFSET, Attributes::TR_Z_OFFSET, Attributes::NAME_OVERRIDE,
           Attributes::ACCELERATION_LIMIT, Attributes::JERK_LIMIT })
    {
        prim.CreateAttribute(attributeInfo[static_cast<int>(attr)].first, attributeInfo[static_cast<int>(attr)].second);
    }
}

}
}
}
