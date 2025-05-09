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

#include <algorithm>
#include <cassert>
#include <cstring>
#include <functional>
#include <iostream>

inline bool IsPowerOfTwo(int n)
{
    return (n & (n - 1)) == 0;
}

// align a ptr to a power of tow
template <typename T>
inline T* AlignPtr(T* p, uint32_t alignment)
{
    assert(IsPowerOfTwo(alignment));

    // cast to safe ptr type
    uintptr_t up = reinterpret_cast<uintptr_t>(p);
    return (T*)((up + (alignment - 1)) & ~(alignment - 1));
}

// align an unsigned value to a power of two
inline uint32_t Align(uint32_t val, uint32_t alignment)
{
    assert(IsPowerOfTwo(alignment));

    return (val + (alignment - 1)) & ~(alignment - 1);
}

inline bool IsAligned(void* p, uint32_t alignment)
{
    return (((uintptr_t)p) & (alignment - 1)) == 0;
}

template <typename To, typename From>
To UnionCast(From in)
{
    union
    {
        To t;
        From f;
    };

    f = in;

    return t;
}

// Endian helpers
template <typename T>
T ByteSwap(const T& val)
{
    T copy = val;
    uint8_t* p = reinterpret_cast<uint8_t*>(&copy);

    std::reverse(p, p + sizeof(T));

    return copy;
}

#ifndef LITTLE_ENDIAN
#    define LITTLE_ENDIAN WIN32
#endif

#ifndef BIG_ENDIAN
#    define BIG_ENDIAN PLATFORM_PS3 || PLATFORM_SPU
#endif

#if BIG_ENDIAN
#    define ToLittleEndian(x) ByteSwap(x)
#else
#    define ToLittleEndian(x) x
#endif

// #include "platform.h"

// #define sizeof_array(x) (sizeof(x)/sizeof(*x))
template <typename T, size_t N>
size_t sizeof_array(const T (&)[N])
{
    return N;
}

// unary_function depricated in c++11
// functor designed for use in the stl
// template <typename T>
// class free_ptr : public std::unary_function<T*, void>
//{
// public:
//    void operator()(const T* ptr)
//    {
//        delete ptr;
//    }
//};


// given the path of one file it strips the filename and appends the relative path onto it
inline void MakeRelativePath(const char* filePath, const char* fileRelativePath, char* fullPath)
{
    // get base path of file
    const char* lastSlash = nullptr;

    if (!lastSlash)
        lastSlash = strrchr(filePath, '\\');
    if (!lastSlash)
        lastSlash = strrchr(filePath, '/');

    int baseLength = 0;

    if (lastSlash)
    {
        baseLength = int(lastSlash - filePath) + 1;

        // copy base path (including slash to relative path)
        memcpy(fullPath, filePath, baseLength);
    }

    // if (fileRelativePath[0] == '.')
    //++fileRelativePath;
    if (fileRelativePath[0] == '\\' || fileRelativePath[0] == '/')
        ++fileRelativePath;

// append mesh filename
#ifdef _WIN32
    strcpy_s(fullPath + baseLength, baseLength, fileRelativePath);
#else
    strcpy(fullPath + baseLength, fileRelativePath);
#endif
}
