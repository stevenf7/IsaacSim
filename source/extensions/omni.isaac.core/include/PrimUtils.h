// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

#include <carb/ObjectUtils.h>

#include <UsdPCH.h>

namespace omni
{
namespace isaac
{
namespace core
{

std::vector<std::string> findMatchingPrimPaths(const std::string& pattern, long int stageId);

void findMatchingChildren(pxr::UsdPrim root, const std::string& pattern, std::vector<pxr::UsdPrim>& primsRet);
}
}
}
