// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "geometry_msgs/Transform.h"

#include <carb/Framework.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <tf2_ros/transform_listener.h>

#include <PxActor.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{
inline omni::isaac::dynamic_control::DcTransform asDcTransform(const geometry_msgs::Pose& p, const float scale = 1)
{
    omni::isaac::dynamic_control::DcTransform t;
    t.p = { p.position.x * scale, p.position.y * scale, p.position.z * scale };
    t.r = { p.orientation.x, p.orientation.y, p.orientation.z, p.orientation.w };
    return t;
}

inline omni::isaac::dynamic_control::DcTransform asDcTransform(const geometry_msgs::Transform& p, const float scale = 1)
{
    omni::isaac::dynamic_control::DcTransform t;
    t.p = { p.translation.x * scale, p.translation.y * scale, p.translation.z * scale };
    t.r = { p.rotation.x, p.rotation.y, p.rotation.z, p.rotation.w };
    return t;
}

inline geometry_msgs::Pose asRosPose(const omni::isaac::dynamic_control::DcTransform& trans, const float scale = 1)
{
    geometry_msgs::Pose p;

    p.position.x = trans.p.x * scale;
    p.position.y = trans.p.y * scale;
    p.position.z = trans.p.z * scale;
    p.orientation.x = trans.r.x;
    p.orientation.y = trans.r.y;
    p.orientation.z = trans.r.z;
    p.orientation.w = trans.r.w;
    return p;
}

inline geometry_msgs::Pose asRosPose(const pxr::GfTransform& trans, const float scale = 1)
{
    geometry_msgs::Pose p;
    const pxr::GfVec3d pos = trans.GetTranslation() * scale;
    const pxr::GfQuatd rot = trans.GetRotation().GetQuat();

    p.position.x = pos[0];
    p.position.y = pos[1];
    p.position.z = pos[2];
    p.orientation.x = rot.GetImaginary()[0];
    p.orientation.y = rot.GetImaginary()[1];
    p.orientation.z = rot.GetImaginary()[2];
    p.orientation.w = rot.GetReal();
    return p;
}

inline geometry_msgs::Transform asRosTransform(const omni::isaac::dynamic_control::DcTransform& trans,
                                               const float scale = 1)
{
    geometry_msgs::Transform p;

    p.translation.x = trans.p.x * scale;
    p.translation.y = trans.p.y * scale;
    p.translation.z = trans.p.z * scale;
    p.rotation.x = trans.r.x;
    p.rotation.y = trans.r.y;
    p.rotation.z = trans.r.z;
    p.rotation.w = trans.r.w;
    return p;
}

inline geometry_msgs::Transform asRosTransform(const physx::PxTransform& trans, const float scale = 1)
{
    geometry_msgs::Transform p;

    p.translation.x = trans.p.x * scale;
    p.translation.y = trans.p.y * scale;
    p.translation.z = trans.p.z * scale;
    p.rotation.x = trans.q.x;
    p.rotation.y = trans.q.y;
    p.rotation.z = trans.q.z;
    p.rotation.w = trans.q.w;
    return p;
}

inline geometry_msgs::Transform asRosTransform(const pxr::GfTransform& trans, const float scale = 1)
{
    geometry_msgs::Transform p;
    const pxr::GfVec3d pos = trans.GetTranslation() * scale;
    const pxr::GfQuatd rot = trans.GetRotation().GetQuat();

    p.translation.x = pos[0];
    p.translation.y = pos[1];
    p.translation.z = pos[2];
    p.rotation.x = rot.GetImaginary()[0];
    p.rotation.y = rot.GetImaginary()[1];
    p.rotation.z = rot.GetImaginary()[2];
    p.rotation.w = rot.GetReal();
    return p;
}
}
}
}
