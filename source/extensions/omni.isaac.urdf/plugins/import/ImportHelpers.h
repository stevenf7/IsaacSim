// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "../parse/UrdfParser.h"
#include "KinematicChain.h"

#include <omni/isaac/math/core/maths.h>
#include <omni/isaac/urdf/UrdfTypes.h>

namespace omni
{
namespace isaac
{
namespace urdf
{
Quat indexedRotation(int axis, float s, float c);
Vec3 Diagonalize(const Matrix33& m, Quat& massFrame);
void inertiaToUrdf(const Matrix33& inertia, UrdfInertia& urdfInertia);
void urdfToInertia(const UrdfInertia& urdfInertia, Matrix33& inertia);
void mergeFixedChildLinks(const KinematicChain::Node& parentNode, UrdfRobot& robot);
bool collapseFixedJoints(UrdfRobot& robot);
Vec3 urdfAxisToVec(const UrdfAxis& axis);
std::string resolveXrefPath(const std::string& assetRoot, const std::string& urdfPath, const std::string& xrefpath);
bool IsUsdFile(const std::string& filename);
// Make a path name that is not already used.
std::string GetNewSdfPathString(pxr::UsdStageWeakPtr stage, std::string path, int nameClashNum = -1);
bool addVisualMeshToCollision(UrdfRobot& robot);


}
}
}
