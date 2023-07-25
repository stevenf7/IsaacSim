// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <string>

namespace omni::sensors::nv
{

//-----------------------------------------------------------------------------
static inline std::string ReadWholeTextFile(std::string fullPath)
{
    std::FILE* f = nullptr;

#if defined(_WIN32) || defined(_WIN64)
    ::fopen_s(&f, fullPath.c_str(), "rb");
#else
    f = std::fopen(fullPath.c_str(), "r");
#endif

    if (nullptr == f)
        return {};

    std::fseek(f, 0, SEEK_END);
    size_t size = ::ftell(f);
    std::fseek(f, 0, SEEK_SET);

    std::string str(size + 1, '\0');

    std::fread(&str[0], 1, size, f);
    std::fclose(f);

    return str;
}
} // namespace omni::sensors::nv
