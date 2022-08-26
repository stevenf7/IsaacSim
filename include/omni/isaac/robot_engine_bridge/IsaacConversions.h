// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <omni/isaac/robot_engine_bridge/IsaacMessage.h>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

/**
 * @brief Converts sim Vec3d to robot engine Vector3d proto
 *
 * @param usdVec3d
 * @param isaacVector3dProto
 */
inline void toVector3dProto(const pxr::GfVec3d& usdVec3d, isaac_message::Vector3d::Builder& isaacVector3dProto)
{
    isaacVector3dProto.setX(usdVec3d[0]);
    isaacVector3dProto.setY(usdVec3d[1]);
    isaacVector3dProto.setZ(usdVec3d[2]);
}

/**
 * @brief Converts sim Float3 to robot engine Vector3d proto
 *
 * @param carbFloat3
 * @param isaacVector3dProto
 */
inline void toVector3dProto(const carb::Float3& carbFloat3, isaac_message::Vector3d::Builder& isaacVector3dProto)
{
    isaacVector3dProto.setX(carbFloat3.x);
    isaacVector3dProto.setY(carbFloat3.y);
    isaacVector3dProto.setZ(carbFloat3.z);
}
/**
 * @brief Converts sim quat to robot engine SO3d proto
 *
 * @param usdQuat
 * @param isaacSO3dProto
 */
inline void toSO3dProto(const pxr::GfQuatd& usdQuat, isaac_message::SO3d::Builder& isaacSO3dProto)
{
    auto isaacSO3dQuatProto = isaacSO3dProto.initQ();
    isaacSO3dQuatProto.setX(usdQuat.GetImaginary()[0]);
    isaacSO3dQuatProto.setY(usdQuat.GetImaginary()[1]);
    isaacSO3dQuatProto.setZ(usdQuat.GetImaginary()[2]);
    isaacSO3dQuatProto.setW(usdQuat.GetReal());
}
/**
 * @brief Converts a robot engine QuaterniondProto to a GfQuatd
 *
 * @param isaacSO3dProto
 */
inline pxr::GfQuatd toGfQuatd(const QuaterniondProto::Reader& isaacSO3dProto)
{
    return pxr::GfQuatd(isaacSO3dProto.getW(), isaacSO3dProto.getX(), isaacSO3dProto.getY(), isaacSO3dProto.getZ());
}
/**
 * @brief Converts a robot engine QuaterniondProto to a GfQuatf
 *
 * @param isaacSO3d
 */
inline pxr::GfQuatf toGfQuatf(const QuaterniondProto::Reader& isaacSO3dProto)
{
    return pxr::GfQuatf(isaacSO3dProto.getW(), isaacSO3dProto.getX(), isaacSO3dProto.getY(), isaacSO3dProto.getZ());
}

}
}
}
