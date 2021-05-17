// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
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

#include "../Core/IsaacMessage.h"

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
void toVector3dProto(const pxr::GfVec3d& usdVec3d, isaac_message::Vector3d::Builder& isaacVector3dProto);


/**
 * @brief Converts sim Float3 to robot engine Vector3d proto
 *
 * @param carbFloat3
 * @param isaacVector3dProto
 */
void toVector3dProto(const carb::Float3& carbFloat3, isaac_message::Vector3d::Builder& isaacVector3dProto);

/**
 * @brief Converts sim quat to robot engine SO3d proto
 *
 * @param usdQuat
 * @param isaacSO3dProto
 */
void toSO3dProto(const pxr::GfQuatd& usdQuat, isaac_message::SO3d::Builder& isaacSO3dProto);

/**
 * @brief Converts a robot engine QuaterniondProto to a GfQuatd
 *
 * @param isaacSO3dProto
 */
pxr::GfQuatd toGfQuatd(const QuaterniondProto::Reader& isaacSO3dProto);

/**
 * @brief Converts a robot engine QuaterniondProto to a GfQuatf
 *
 * @param isaacSO3d
 */
pxr::GfQuatf toGfQuatf(const QuaterniondProto::Reader& isaacSO3dProto);


}
}
}
