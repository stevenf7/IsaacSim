// Copyright (c) 2024-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <string>

#ifdef _MSC_VER
#    if ISAACSIM_CORE_UTILS_EXPORT
#        define DLL_EXPORT __declspec(dllexport)
#    else
#        define DLL_EXPORT __declspec(dllimport)
#    endif
#else
#    define DLL_EXPORT
#endif

namespace isaacsim
{
namespace core
{
namespace utils
{

DLL_EXPORT std::vector<std::string> findMatchingPrimPaths(const std::string& pattern,
                                                          long int stageId,
                                                          const std::string& api = std::string(""));

DLL_EXPORT void findMatchingChildren(pxr::UsdPrim root, const std::string& pattern, std::vector<pxr::UsdPrim>& primsRet);
}
}
}
