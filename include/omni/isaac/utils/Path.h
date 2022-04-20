// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
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

#include <string>


namespace omni
{
namespace isaac
{
namespace utils
{
namespace path
{

inline std::string normalizeUrl(const char* url)
{
    std::string ret;
    char stringBuffer[1024];
    std::unique_ptr<char[]> stringBufferHeap;
    size_t bufferSize = sizeof(stringBuffer);
    const char* normalizedUrl = omniClientNormalizeUrl(url, stringBuffer, &bufferSize);
    if (!normalizedUrl)
    {
        stringBufferHeap = std::unique_ptr<char[]>(new char[bufferSize]);
        normalizedUrl = omniClientNormalizeUrl(url, stringBufferHeap.get(), &bufferSize);
        if (!normalizedUrl)
        {
            normalizedUrl = "";
            CARB_LOG_ERROR("Cannot normalize %s", url);
        }
    }

    ret = normalizedUrl;
    for (auto& c : ret)
    {
        if (c == '\\')
        {
            c = '/';
        }
    }
    return ret;
}


std::string resolve_absolute(std::string parent, std::string relative)
{
    size_t bufferSize = parent.size() + relative.size();
    std::unique_ptr<char[]> stringBuffer = std::unique_ptr<char[]>(new char[bufferSize]);
    std::string combined_url = normalizeUrl((parent + "/" + relative).c_str());
    return combined_url;
}

}
}
}
}
