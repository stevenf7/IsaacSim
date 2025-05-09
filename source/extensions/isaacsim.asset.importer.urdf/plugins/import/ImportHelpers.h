// SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#pragma once

// clang-format off
#include "../UsdPCH.h"
// clang-format on

#include "../UrdfTypes.h"
#include "../math/core/maths.h"
#include "../parse/UrdfParser.h"
#include "KinematicChain.h"

namespace isaacsim
{
namespace asset
{
namespace importer
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
}
