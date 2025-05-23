// SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

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
