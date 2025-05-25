// SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

/**
 * @brief Controls verbose output for debugging purposes
 * @details Set to 1 to enable verbose output, 0 to disable
 */
#define ENABLE_VERBOSE_OUTPUT 0

/**
 * @brief Controls APIC capture functionality
 * @details Set to 1 to enable APIC capture, 0 to disable
 */
#define ENABLE_APIC_CAPTURE 0

/**
 * @brief Controls Perfalyze capture functionality
 * @details Set to 1 to enable Perfalyze capture, 0 to disable
 */
#define ENABLE_PERFALYZE_CAPTURE 0

#if ENABLE_VERBOSE_OUTPUT
/**
 * @brief Verbose output macro for debugging
 * @details When ENABLE_VERBOSE_OUTPUT is enabled, executes the given statement
 */
#    define VERBOSE(a) a##;
#else
/**
 * @brief Verbose output macro (disabled)
 * @details When ENABLE_VERBOSE_OUTPUT is disabled, expands to nothing
 */
#    define VERBOSE(a)
#endif

// #define Super __super

// basically just a collection of macros and types
#ifndef UNUSED
/**
 * @brief Marks a variable as unused to suppress compiler warnings
 * @param[in] x Variable to mark as unused
 * @details Explicitly casts the variable to void to indicate intentional non-use
 */
#    define UNUSED(x) (void)x;
#endif

/**
 * @brief Prevents definition of min/max macros that conflict with STL
 * @details Disables the Windows min/max macro definitions
 */
#define NOMINMAX

#if !PLATFORM_OPENCL
#    include <cassert>
#endif

#include "Types.h"

#if !PLATFORM_SPU && !PLATFORM_OPENCL
#    include <algorithm>
#    include <fstream>
#    include <functional>
#    include <iostream>
#    include <string>
#endif

#include <string.h>

// disable some warnings
#if _WIN32
#    pragma warning(disable : 4996) // secure io
#    pragma warning(disable : 4100) // unreferenced param
#    pragma warning(disable : 4324) // structure was padded due to __declspec(align())
#endif

// alignment helpers
/**
 * @brief Default memory alignment in bytes
 * @details Standard alignment boundary of 16 bytes for SIMD operations
 */
#define DEFAULT_ALIGNMENT 16

#if PLATFORM_LINUX
/**
 * @brief Alignment specifier macro for Linux platforms
 * @param[in] x Alignment boundary in bytes
 * @details On Linux, alignment is specified after the declaration
 */
#    define ALIGN_N(x)
/**
 * @brief End alignment specifier macro for Linux platforms
 * @param[in] x Alignment boundary in bytes
 * @details Uses GCC attribute syntax for alignment specification
 */
#    define ENDALIGN_N(x) __attribute__((aligned(x)))
#else
/**
 * @brief Alignment specifier macro for non-Linux platforms
 * @param[in] x Alignment boundary in bytes
 * @details Uses Microsoft-style alignment specification
 */
#    define ALIGN_N(x) __declspec(align(x))
/**
 * @brief End alignment specifier macro for non-Linux platforms
 * @param[in] x Alignment boundary in bytes
 * @details Not used on non-Linux platforms
 */
#    define END_ALIGN_N(x)
#endif

/**
 * @brief Default alignment macro using DEFAULT_ALIGNMENT
 * @details Aligns data structures to the default 16-byte boundary
 */
#define ALIGN ALIGN_N(DEFAULT_ALIGNMENT)

/**
 * @brief End alignment macro using DEFAULT_ALIGNMENT
 * @details Complements ALIGN for platforms that require it
 */
#define END_ALIGN END_ALIGN_N(DEFAULT_ALIGNMENT)

/**
 * @brief Checks if a number is a power of two
 * @param[in] n Integer value to check
 * @return True if n is a power of two, false otherwise
 * @details Uses bit manipulation: (n & (n-1)) == 0 for powers of two
 */
inline bool IsPowerOfTwo(int n)
{
    return (n & (n - 1)) == 0;
}

/**
 * @brief Aligns a pointer to a specified power-of-two boundary
 * @tparam T Pointer type
 * @param[in] p Pointer to align
 * @param[in] alignment Alignment boundary (must be power of two)
 * @return Aligned pointer
 * @pre alignment must be a power of two
 */
template <typename T>
inline T* AlignPtr(T* p, uint32_t alignment)
{
    assert(IsPowerOfTwo(alignment));

    // cast to safe ptr type
    uintptr_t up = reinterpret_cast<uintptr_t>(p);
    return (T*)((up + (alignment - 1)) & ~(alignment - 1));
}

/**
 * @brief Aligns an unsigned value to a specified power-of-two boundary
 * @param[in] val Value to align
 * @param[in] alignment Alignment boundary (must be power of two)
 * @return Aligned value
 * @pre alignment must be a power of two
 */
inline uint32_t Align(uint32_t val, uint32_t alignment)
{
    assert(IsPowerOfTwo(alignment));

    return (val + (alignment - 1)) & ~(alignment - 1);
}

/**
 * @brief Checks if a pointer is aligned to a specified boundary
 * @param[in] p Pointer to check
 * @param[in] alignment Alignment boundary to check against
 * @return True if pointer is aligned, false otherwise
 */
inline bool IsAligned(void* p, uint32_t alignment)
{
    return (((uintptr_t)p) & (alignment - 1)) == 0;
}

/**
 * @brief Performs type punning between two types of the same size
 * @tparam To Target type to convert to
 * @tparam From Source type to convert from
 * @param[in] in Value to convert
 * @return Value reinterpreted as target type
 * @details Uses anonymous union for safe type punning without undefined behavior
 */
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

/**
 * @brief Reverses the byte order of a value (endian swap)
 * @tparam T Type of the value to byte swap
 * @param[in] val Value to byte swap
 * @return Value with reversed byte order
 * @details Reverses all bytes in the value using std::reverse
 */
template <typename T>
T ByteSwap(const T& val)
{
    T copy = val;
    uint8_t* p = reinterpret_cast<uint8_t*>(&copy);

    std::reverse(p, p + sizeof(T));

    return copy;
}

#ifndef LITTLE_ENDIAN
/**
 * @brief Defines little endian byte order for the platform
 * @details Set to 1 on little endian platforms (most modern systems)
 */
#    define LITTLE_ENDIAN WIN32
#endif

#ifndef BIG_ENDIAN
/**
 * @brief Defines big endian byte order for the platform
 * @details Set to 1 on big endian platforms (some older systems)
 */
#    define BIG_ENDIAN PLATFORM_PS3 || PLATFORM_SPU
#endif

#if BIG_ENDIAN
/**
 * @brief Converts a value to little endian byte order
 * @param[in] x Value to convert
 * @return Value in little endian byte order
 * @details On big endian platforms, performs byte swap; on little endian, returns unchanged
 */
#    define ToLittleEndian(x) ByteSwap(x)
#else
/**
 * @brief Converts a value to little endian byte order
 * @param[in] x Value to convert
 * @return Value in little endian byte order
 * @details On little endian platforms, returns value unchanged
 */
#    define ToLittleEndian(x) x
#endif
