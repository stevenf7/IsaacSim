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
#include "UsdPCH.h"
// clang-format on


#include "assimp/scene.h"

#include <string>


namespace omni
{
namespace isaac
{
namespace urdf
{


pxr::SdfPath SimpleImport(pxr::UsdStageRefPtr usdStage,
                          std::string path,
                          const aiScene* mScene,
                          const std::string mesh_path,
                          std::map<pxr::TfToken, std::string>& materialsList,
                          const bool loadMaterials = true,
                          const bool flipVisuals = false,
                          const char* subdvisionScheme = "none",
                          const bool instanceable = false);


}
}
}
