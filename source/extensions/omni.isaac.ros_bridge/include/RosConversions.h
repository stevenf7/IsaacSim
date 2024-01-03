// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Framework.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>

#include <PxActor.h>

namespace omni
{
namespace isaac
{
namespace conversions
{
template <typename T>
inline dynamic_control::DcTransform rosPoseAsDcTransform(const T& p, const float scale = 1)
{
    dynamic_control::DcTransform t;
    t.p = { static_cast<float>(p.position.x * scale), static_cast<float>(p.position.y * scale),
            static_cast<float>(p.position.z * scale) };
    t.r = { static_cast<float>(p.orientation.x), static_cast<float>(p.orientation.y),
            static_cast<float>(p.orientation.z), static_cast<float>(p.orientation.w) };
    return t;
}
template <typename T>
inline dynamic_control::DcTransform rosTransformAsDcTransform(const T& p, const float scale = 1)
{
    dynamic_control::DcTransform t;
    t.p = { static_cast<float>(p.translation.x * scale), static_cast<float>(p.translation.y * scale),
            static_cast<float>(p.translation.z * scale) };
    t.r = { static_cast<float>(p.rotation.x), static_cast<float>(p.rotation.y), static_cast<float>(p.rotation.z),
            static_cast<float>(p.rotation.w) };
    return t;
}
template <typename T>
inline T asRosPose(const dynamic_control::DcTransform& trans, const float scale = 1)
{
    T p;

    p.position.x = trans.p.x * scale;
    p.position.y = trans.p.y * scale;
    p.position.z = trans.p.z * scale;
    p.orientation.x = trans.r.x;
    p.orientation.y = trans.r.y;
    p.orientation.z = trans.r.z;
    p.orientation.w = trans.r.w;
    return p;
}
template <typename T>
inline T asRosPose(const pxr::GfTransform& trans, const float scale = 1)
{
    T p;
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
template <typename T>
inline T asRosTransform(const dynamic_control::DcTransform& trans, const float scale = 1)
{
    T p;

    p.translation.x = trans.p.x * scale;
    p.translation.y = trans.p.y * scale;
    p.translation.z = trans.p.z * scale;
    p.rotation.x = trans.r.x;
    p.rotation.y = trans.r.y;
    p.rotation.z = trans.r.z;
    p.rotation.w = trans.r.w;
    return p;
}
template <typename T>
inline T asRosTransform(const physx::PxTransform& trans, const float scale = 1)
{
    T p;

    p.translation.x = trans.p.x * scale;
    p.translation.y = trans.p.y * scale;
    p.translation.z = trans.p.z * scale;
    p.rotation.x = trans.q.x;
    p.rotation.y = trans.q.y;
    p.rotation.z = trans.q.z;
    p.rotation.w = trans.q.w;
    return p;
}
template <typename T>
inline T asRosTransform(const pxr::GfTransform& trans, const float scale = 1)
{
    T p;
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
template <typename T>
inline carb::Float3 asCarbFloat3(const T& p, const float scale = 1)
{
    carb::Float3 t = { static_cast<float>(p.x) * scale, static_cast<float>(p.y) * scale, static_cast<float>(p.z) * scale };
    return t;
}


}
}
}
