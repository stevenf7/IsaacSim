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
#include "gems/pose_tree/pose_tree.hpp"

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
 * @brief Converts sim Vec3d to robot engine Vector3d C++ type
 *
 * @param usdVec3d
 * @param ::isaac::Vector3d
 */
void toVector3d(const pxr::GfVec3d& usdVec3d, ::isaac::Vector3d& isaaVector3d);

/**
 * @brief Converts sim Float3 to robot engine Vector3d proto
 *
 * @param carbFloat3
 * @param isaacVector3dProto
 */
void toVector3dProto(const carb::Float3& carbFloat3, isaac_message::Vector3d::Builder& isaacVector3dProto);

/**
 * @brief Converts sim Float3 to robot engine Vector3d C++ type
 *
 * @param carbFloat3
 * @param ::isaac::Vector3d
 */
void toVector3d(const carb::Float3& carbFloat3, ::isaac::Vector3d& isaacVector3d);

/**
 * @brief Converts sim quat to robot engine SO3d proto
 *
 * @param usdQuat
 * @param isaacSO3dProto
 */
void toSO3dProto(const pxr::GfQuatd& usdQuat, isaac_message::SO3d::Builder& isaacSO3dProto);

/**
 * @brief Converts sim quat to robot engine SO3d C++ type
 *
 * @param usdQuat
 * @param ::isaac::SO3d
 */
void toSO3d(const pxr::GfQuatd& usdQuat, ::isaac::SO3d& isaacSO3d);

}
}
}
