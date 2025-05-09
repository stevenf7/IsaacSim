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


#include <string>


namespace isaacsim
{
namespace asset
{
namespace importer
{
namespace urdf
{
pxr::SdfPath SimpleImport(pxr::UsdStageRefPtr usdStage,
                          const std::string& path,
                          const std::string& meshPath,
                          std::map<pxr::TfToken, pxr::SdfPath>& meshList,
                          std::map<pxr::TfToken, pxr::SdfPath>& materialList,
                          const pxr::SdfPath& rootPath);


}
}
}
}
