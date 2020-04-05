#pragma once

// clang-format off
#include <UsdPCH.h>
// clang-format on

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
static void toVector3dProto(const pxr::GfVec3d& usdVec3d, isaac_message::Vector3d::Builder& isaacVector3dProto)
{
    isaacVector3dProto.setX(usdVec3d[0]);
    isaacVector3dProto.setY(usdVec3d[1]);
    isaacVector3dProto.setZ(usdVec3d[2]);
}

/**
 * @brief Converts sim quat to robot engine SO3d proto
 *
 * @param usdQuat
 * @param isaacSO3dProto
 */
static void toSO3dProto(const pxr::GfQuatd& usdQuat, isaac_message::SO3d::Builder& isaacSO3dProto)
{
    auto isaacSO3dQuatProto = isaacSO3dProto.initQ();
    isaacSO3dQuatProto.setX(usdQuat.GetImaginary()[0]);
    isaacSO3dQuatProto.setY(usdQuat.GetImaginary()[1]);
    isaacSO3dQuatProto.setZ(usdQuat.GetImaginary()[2]);
    isaacSO3dQuatProto.setW(usdQuat.GetReal());
}
}
}
}
