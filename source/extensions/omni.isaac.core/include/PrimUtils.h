// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#ifdef _MSC_VER
#    if OMPRIMUTILSEXPORT
#        define DllExport __declspec(dllexport)
#    else
#        define DllExport __declspec(dllimport)
#    endif
#else
#    define DllExport
#endif

namespace omni
{
namespace isaac
{
namespace core
{

DllExport std::vector<std::string> findMatchingPrimPaths(const std::string& pattern,
                                                         long int stageId,
                                                         const std::string& api = std::string(""));

DllExport void findMatchingChildren(pxr::UsdPrim root, const std::string& pattern, std::vector<pxr::UsdPrim>& primsRet);
}
}
}
