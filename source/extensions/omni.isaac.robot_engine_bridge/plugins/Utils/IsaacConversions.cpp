// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "IsaacConversions.h"

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

void toVector3dProto(const pxr::GfVec3d& usdVec3d, isaac_message::Vector3d::Builder& isaacVector3dProto)
{
    isaacVector3dProto.setX(usdVec3d[0]);
    isaacVector3dProto.setY(usdVec3d[1]);
    isaacVector3dProto.setZ(usdVec3d[2]);
}

void toVector3d(const pxr::GfVec3d& usdVec3d, ::isaac::Vector3d& isaacVector3d)
{
    isaacVector3d = { usdVec3d[0], usdVec3d[1], usdVec3d[2] };
}

void toVector3dProto(const carb::Float3& carbFloat3, isaac_message::Vector3d::Builder& isaacVector3dProto)
{
    isaacVector3dProto.setX(carbFloat3.x);
    isaacVector3dProto.setY(carbFloat3.y);
    isaacVector3dProto.setZ(carbFloat3.z);
}

void toVector3d(const carb::Float3& carbFloat3, ::isaac::Vector3d& isaacVector3d)
{
    isaacVector3d = { carbFloat3.x, carbFloat3.y, carbFloat3.z };
}

void toSO3dProto(const pxr::GfQuatd& usdQuat, isaac_message::SO3d::Builder& isaacSO3dProto)
{
    auto isaacSO3dQuatProto = isaacSO3dProto.initQ();
    isaacSO3dQuatProto.setX(usdQuat.GetImaginary()[0]);
    isaacSO3dQuatProto.setY(usdQuat.GetImaginary()[1]);
    isaacSO3dQuatProto.setZ(usdQuat.GetImaginary()[2]);
    isaacSO3dQuatProto.setW(usdQuat.GetReal());
}

void toSO3d(const pxr::GfQuatd& usdQuat, ::isaac::SO3d& isaacSO3d)
{
    isaacSO3d = ::isaac::SO3d::FromQuaternion(::isaac::Quaterniond(
        usdQuat.GetReal(), usdQuat.GetImaginary()[0], usdQuat.GetImaginary()[1], usdQuat.GetImaginary()[2]));
}

pxr::GfQuatd toGfQuatd(const QuaterniondProto::Reader& isaacSO3dProto)
{
    return pxr::GfQuatd(isaacSO3dProto.getW(), isaacSO3dProto.getX(), isaacSO3dProto.getY(), isaacSO3dProto.getZ());
}

pxr::GfQuatf toGfQuatf(const QuaterniondProto::Reader& isaacSO3dProto)
{
    return pxr::GfQuatf(isaacSO3dProto.getW(), isaacSO3dProto.getX(), isaacSO3dProto.getY(), isaacSO3dProto.getZ());
}
}
}
}
