// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
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
namespace gxf_bridge
{


void toVector3d(const pxr::GfVec3d& usdVec3d, ::nvidia::isaac::Vector3d& isaacVector3d)
{
    isaacVector3d = { usdVec3d[0], usdVec3d[1], usdVec3d[2] };
}


void toVector3d(const carb::Float3& carbFloat3, ::nvidia::isaac::Vector3d& isaacVector3d)
{
    isaacVector3d = { carbFloat3.x, carbFloat3.y, carbFloat3.z };
}

void toSO3d(const pxr::GfQuatd& usdQuat, ::nvidia::isaac::SO3d& isaacSO3d)
{
    isaacSO3d = ::nvidia::isaac::SO3d::FromQuaternion(::nvidia::isaac::Quaterniond(
        usdQuat.GetReal(), usdQuat.GetImaginary()[0], usdQuat.GetImaginary()[1], usdQuat.GetImaginary()[2]));
}

}
}
}
