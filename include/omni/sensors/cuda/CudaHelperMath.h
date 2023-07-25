// Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
/**
 * Copyright 1993-2012 NVIDIA Corporation.  All rights reserved.
 *
 * Please refer to the NVIDIA end user license agreement (EULA) associated
 * with this source code for terms and conditions that govern your use of
 * this software. Any use, reproduction, disclosure, or distribution of
 * this software and related documentation outside the terms of the EULA
 * is strictly prohibited.
 *
 */

/*
 *  This file implements common mathematical operations on vector types
 *  (float3, float4 etc.) since these are not provided as standard by CUDA.
 *
 *  The syntax is modeled on the Cg standard library.
 *
 *  This is part of the Helper library includes
 *
 *    Thanks to Linh Hah for additions and fixes.
 */

#pragma once

#include "CudaHelperDecl.h"

#include <cuComplex.h>

typedef unsigned int uint;


////////////////////////////////////////////////////////////////////////////////
// constants
////////////////////////////////////////////////////////////////////////////////

static constexpr float TAU = 6.28318530717958647692f;
static constexpr float PI = 3.14159265358979323846f;
static constexpr float HALF_PI = 1.57079632679489661923f;
static constexpr float SRQRT2 = 1.41421356237309504880f;
static constexpr uint64_t NS_IN_S = 1000 * 1000 * 1000;
static constexpr uint64_t US_IN_S = 1000 * 1000;
static constexpr uint64_t NS_IN_US = 1000;


#ifndef __CUDACC__
#    include <math.h>

#    ifndef __align__
#        ifdef __GNUC__
#            define __align__(n) __attribute__((aligned(n)))
#        else
#            define __align__(n) __declspec(align(n))
#        endif
#    endif

////////////////////////////////////////////////////////////////////////////////
// host implementations of CUDA functions
////////////////////////////////////////////////////////////////////////////////
#    ifndef __VECTOR_TYPES_H__
struct float2
{
    float x, y;
};

struct float3
{
    float x, y, z;
};

struct __align__(16) float4
{
    float x, y, z, w;
};

struct int2
{
    int x, y;
};

struct int3
{
    int x, y, z;
};

struct __align__(16) int4
{
    int x, y, z, w;
};

struct uint2
{
    unsigned int x, y;
};

struct uint3
{
    unsigned int x, y, z;
};

struct __align__(16) uint4
{
    unsigned int x, y, z, w;
};

inline float2 make_float2(float x, float y)
{
    float2 t;
    t.x = x;
    t.y = y;
    return t;
}

inline float3 make_float3(float x, float y, float z)
{
    float3 t;
    t.x = x;
    t.y = y;
    t.z = z;
    return t;
}

inline float4 make_float4(float x, float y, float z, float w)
{
    float4 t;
    t.x = x;
    t.y = y;
    t.z = z;
    t.w = w;
    return t;
}

inline int2 make_int2(int x, int y)
{
    int2 t;
    t.x = x;
    t.y = y;
    return t;
}

inline uint2 make_uint2(unsigned int x, unsigned int y)
{
    uint2 t;
    t.x = x;
    t.y = y;
    return t;
}

inline int3 make_int3(int x, int y, int z)
{
    int3 t;
    t.x = x;
    t.y = y;
    t.z = z;
    return t;
}

inline uint3 make_uint3(unsigned int x, unsigned int y, unsigned int z)
{
    uint3 t;
    t.x = x;
    t.y = y;
    t.z = z;
    return t;
}

inline int4 make_int4(int x, int y, int z, int w)
{
    int4 t;
    t.x = x;
    t.y = y;
    t.z = z;
    t.w = w;
    return t;
}

inline uint4 make_uint4(unsigned int x, unsigned int y, unsigned int z, unsigned int w)
{
    uint4 t;
    t.x = x;
    t.y = y;
    t.z = z;
    t.w = w;
    return t;
}

#    endif

inline int max(int a, int b)
{
    return a > b ? a : b;
}

inline int min(int a, int b)
{
    return a < b ? a : b;
}

inline float rsqrtf(float x)
{
    return 1.0f / sqrtf(x);
}

#endif


////////////////////////////////////////////////////////////////////////////////
// constructors
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float2 make_float2(float s)
{
    return make_float2(s, s);
}
inline NV_HOSTDEVICE float2 make_float2(float3 a)
{
    return make_float2(a.x, a.y);
}
inline NV_HOSTDEVICE float2 make_float2(int2 a)
{
    return make_float2(float(a.x), float(a.y));
}
inline NV_HOSTDEVICE float2 make_float2(uint2 a)
{
    return make_float2(float(a.x), float(a.y));
}

inline NV_HOSTDEVICE int2 make_int2(int s)
{
    return make_int2(s, s);
}
inline NV_HOSTDEVICE int2 make_int2(int3 a)
{
    return make_int2(a.x, a.y);
}
inline NV_HOSTDEVICE int2 make_int2(uint2 a)
{
    return make_int2(int(a.x), int(a.y));
}
inline NV_HOSTDEVICE int2 make_int2(float2 a)
{
    return make_int2(int(a.x), int(a.y));
}

inline NV_HOSTDEVICE uint2 make_uint2(uint s)
{
    return make_uint2(s, s);
}
inline NV_HOSTDEVICE uint2 make_uint2(uint3 a)
{
    return make_uint2(a.x, a.y);
}
inline NV_HOSTDEVICE uint2 make_uint2(int2 a)
{
    return make_uint2(uint(a.x), uint(a.y));
}

inline NV_HOSTDEVICE float3 make_float3(float s)
{
    return make_float3(s, s, s);
}
inline NV_HOSTDEVICE float3 make_float3(float2 a)
{
    return make_float3(a.x, a.y, 0.0f);
}
inline NV_HOSTDEVICE float3 make_float3(float2 a, float s)
{
    return make_float3(a.x, a.y, s);
}
inline NV_HOSTDEVICE float3 make_float3(float4 a)
{
    return make_float3(a.x, a.y, a.z);
}
inline NV_HOSTDEVICE float3 make_float3(int3 a)
{
    return make_float3(float(a.x), float(a.y), float(a.z));
}
inline NV_HOSTDEVICE float3 make_float3(uint3 a)
{
    return make_float3(float(a.x), float(a.y), float(a.z));
}

inline NV_HOSTDEVICE int3 make_int3(int s)
{
    return make_int3(s, s, s);
}
inline NV_HOSTDEVICE int3 make_int3(int2 a)
{
    return make_int3(a.x, a.y, 0);
}
inline NV_HOSTDEVICE int3 make_int3(int2 a, int s)
{
    return make_int3(a.x, a.y, s);
}
inline NV_HOSTDEVICE int3 make_int3(uint3 a)
{
    return make_int3(int(a.x), int(a.y), int(a.z));
}
inline NV_HOSTDEVICE int3 make_int3(float3 a)
{
    return make_int3(int(a.x), int(a.y), int(a.z));
}

inline NV_HOSTDEVICE uint3 make_uint3(uint s)
{
    return make_uint3(s, s, s);
}
inline NV_HOSTDEVICE uint3 make_uint3(uint2 a)
{
    return make_uint3(a.x, a.y, 0);
}
inline NV_HOSTDEVICE uint3 make_uint3(uint2 a, uint s)
{
    return make_uint3(a.x, a.y, s);
}
inline NV_HOSTDEVICE uint3 make_uint3(uint4 a)
{
    return make_uint3(a.x, a.y, a.z);
}
inline NV_HOSTDEVICE uint3 make_uint3(int3 a)
{
    return make_uint3(uint(a.x), uint(a.y), uint(a.z));
}

inline NV_HOSTDEVICE float4 make_float4(float s)
{
    return make_float4(s, s, s, s);
}
inline NV_HOSTDEVICE float4 make_float4(float3 a)
{
    return make_float4(a.x, a.y, a.z, 0.0f);
}
inline NV_HOSTDEVICE float4 make_float4(float3 a, float w)
{
    return make_float4(a.x, a.y, a.z, w);
}
inline NV_HOSTDEVICE float4 make_float4(int4 a)
{
    return make_float4(float(a.x), float(a.y), float(a.z), float(a.w));
}
inline NV_HOSTDEVICE float4 make_float4(uint4 a)
{
    return make_float4(float(a.x), float(a.y), float(a.z), float(a.w));
}

inline NV_HOSTDEVICE int4 make_int4(int s)
{
    return make_int4(s, s, s, s);
}
inline NV_HOSTDEVICE int4 make_int4(int3 a)
{
    return make_int4(a.x, a.y, a.z, 0);
}
inline NV_HOSTDEVICE int4 make_int4(int3 a, int w)
{
    return make_int4(a.x, a.y, a.z, w);
}
inline NV_HOSTDEVICE int4 make_int4(uint4 a)
{
    return make_int4(int(a.x), int(a.y), int(a.z), int(a.w));
}
inline NV_HOSTDEVICE int4 make_int4(float4 a)
{
    return make_int4(int(a.x), int(a.y), int(a.z), int(a.w));
}


inline NV_HOSTDEVICE uint4 make_uint4(uint s)
{
    return make_uint4(s, s, s, s);
}
inline NV_HOSTDEVICE uint4 make_uint4(uint3 a)
{
    return make_uint4(a.x, a.y, a.z, 0);
}
inline NV_HOSTDEVICE uint4 make_uint4(uint3 a, uint w)
{
    return make_uint4(a.x, a.y, a.z, w);
}
inline NV_HOSTDEVICE uint4 make_uint4(int4 a)
{
    return make_uint4(uint(a.x), uint(a.y), uint(a.z), uint(a.w));
}

////////////////////////////////////////////////////////////////////////////////
// negate
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float2 operator-(float2& a)
{
    return make_float2(-a.x, -a.y);
}
inline NV_HOSTDEVICE int2 operator-(int2& a)
{
    return make_int2(-a.x, -a.y);
}
inline NV_HOSTDEVICE float3 operator-(float3& a)
{
    return make_float3(-a.x, -a.y, -a.z);
}
inline NV_HOSTDEVICE int3 operator-(int3& a)
{
    return make_int3(-a.x, -a.y, -a.z);
}
inline NV_HOSTDEVICE float4 operator-(float4& a)
{
    return make_float4(-a.x, -a.y, -a.z, -a.w);
}
inline NV_HOSTDEVICE int4 operator-(int4& a)
{
    return make_int4(-a.x, -a.y, -a.z, -a.w);
}

////////////////////////////////////////////////////////////////////////////////
// addition
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float2 operator+(float2 a, float2 b)
{
    return make_float2(a.x + b.x, a.y + b.y);
}
inline NV_HOSTDEVICE void operator+=(float2& a, float2 b)
{
    a.x += b.x;
    a.y += b.y;
}
inline NV_HOSTDEVICE float2 operator+(float2 a, float b)
{
    return make_float2(a.x + b, a.y + b);
}
inline NV_HOSTDEVICE float2 operator+(float b, float2 a)
{
    return make_float2(a.x + b, a.y + b);
}
inline NV_HOSTDEVICE void operator+=(float2& a, float b)
{
    a.x += b;
    a.y += b;
}

inline NV_HOSTDEVICE int2 operator+(int2 a, int2 b)
{
    return make_int2(a.x + b.x, a.y + b.y);
}
inline NV_HOSTDEVICE void operator+=(int2& a, int2 b)
{
    a.x += b.x;
    a.y += b.y;
}
inline NV_HOSTDEVICE int2 operator+(int2 a, int b)
{
    return make_int2(a.x + b, a.y + b);
}
inline NV_HOSTDEVICE int2 operator+(int b, int2 a)
{
    return make_int2(a.x + b, a.y + b);
}
inline NV_HOSTDEVICE void operator+=(int2& a, int b)
{
    a.x += b;
    a.y += b;
}

inline NV_HOSTDEVICE uint2 operator+(uint2 a, uint2 b)
{
    return make_uint2(a.x + b.x, a.y + b.y);
}
inline NV_HOSTDEVICE void operator+=(uint2& a, uint2 b)
{
    a.x += b.x;
    a.y += b.y;
}
inline NV_HOSTDEVICE uint2 operator+(uint2 a, uint b)
{
    return make_uint2(a.x + b, a.y + b);
}
inline NV_HOSTDEVICE uint2 operator+(uint b, uint2 a)
{
    return make_uint2(a.x + b, a.y + b);
}
inline NV_HOSTDEVICE void operator+=(uint2& a, uint b)
{
    a.x += b;
    a.y += b;
}


inline NV_HOSTDEVICE float3 operator+(float3 a, float3 b)
{
    return make_float3(a.x + b.x, a.y + b.y, a.z + b.z);
}
inline NV_HOSTDEVICE void operator+=(float3& a, float3 b)
{
    a.x += b.x;
    a.y += b.y;
    a.z += b.z;
}
inline NV_HOSTDEVICE float3 operator+(float3 a, float b)
{
    return make_float3(a.x + b, a.y + b, a.z + b);
}
inline NV_HOSTDEVICE void operator+=(float3& a, float b)
{
    a.x += b;
    a.y += b;
    a.z += b;
}

inline NV_HOSTDEVICE int3 operator+(int3 a, int3 b)
{
    return make_int3(a.x + b.x, a.y + b.y, a.z + b.z);
}
inline NV_HOSTDEVICE void operator+=(int3& a, int3 b)
{
    a.x += b.x;
    a.y += b.y;
    a.z += b.z;
}
inline NV_HOSTDEVICE int3 operator+(int3 a, int b)
{
    return make_int3(a.x + b, a.y + b, a.z + b);
}
inline NV_HOSTDEVICE void operator+=(int3& a, int b)
{
    a.x += b;
    a.y += b;
    a.z += b;
}

inline NV_HOSTDEVICE uint3 operator+(uint3 a, uint3 b)
{
    return make_uint3(a.x + b.x, a.y + b.y, a.z + b.z);
}
inline NV_HOSTDEVICE void operator+=(uint3& a, uint3 b)
{
    a.x += b.x;
    a.y += b.y;
    a.z += b.z;
}
inline NV_HOSTDEVICE uint3 operator+(uint3 a, uint b)
{
    return make_uint3(a.x + b, a.y + b, a.z + b);
}
inline NV_HOSTDEVICE void operator+=(uint3& a, uint b)
{
    a.x += b;
    a.y += b;
    a.z += b;
}

inline NV_HOSTDEVICE int3 operator+(int b, int3 a)
{
    return make_int3(a.x + b, a.y + b, a.z + b);
}
inline NV_HOSTDEVICE uint3 operator+(uint b, uint3 a)
{
    return make_uint3(a.x + b, a.y + b, a.z + b);
}
inline NV_HOSTDEVICE float3 operator+(float b, float3 a)
{
    return make_float3(a.x + b, a.y + b, a.z + b);
}

inline NV_HOSTDEVICE float4 operator+(float4 a, float4 b)
{
    return make_float4(a.x + b.x, a.y + b.y, a.z + b.z, a.w + b.w);
}
inline NV_HOSTDEVICE void operator+=(float4& a, float4 b)
{
    a.x += b.x;
    a.y += b.y;
    a.z += b.z;
    a.w += b.w;
}
inline NV_HOSTDEVICE float4 operator+(float4 a, float b)
{
    return make_float4(a.x + b, a.y + b, a.z + b, a.w + b);
}
inline NV_HOSTDEVICE float4 operator+(float b, float4 a)
{
    return make_float4(a.x + b, a.y + b, a.z + b, a.w + b);
}
inline NV_HOSTDEVICE void operator+=(float4& a, float b)
{
    a.x += b;
    a.y += b;
    a.z += b;
    a.w += b;
}

inline NV_HOSTDEVICE int4 operator+(int4 a, int4 b)
{
    return make_int4(a.x + b.x, a.y + b.y, a.z + b.z, a.w + b.w);
}
inline NV_HOSTDEVICE void operator+=(int4& a, int4 b)
{
    a.x += b.x;
    a.y += b.y;
    a.z += b.z;
    a.w += b.w;
}
inline NV_HOSTDEVICE int4 operator+(int4 a, int b)
{
    return make_int4(a.x + b, a.y + b, a.z + b, a.w + b);
}
inline NV_HOSTDEVICE int4 operator+(int b, int4 a)
{
    return make_int4(a.x + b, a.y + b, a.z + b, a.w + b);
}
inline NV_HOSTDEVICE void operator+=(int4& a, int b)
{
    a.x += b;
    a.y += b;
    a.z += b;
    a.w += b;
}

inline NV_HOSTDEVICE uint4 operator+(uint4 a, uint4 b)
{
    return make_uint4(a.x + b.x, a.y + b.y, a.z + b.z, a.w + b.w);
}
inline NV_HOSTDEVICE void operator+=(uint4& a, uint4 b)
{
    a.x += b.x;
    a.y += b.y;
    a.z += b.z;
    a.w += b.w;
}
inline NV_HOSTDEVICE uint4 operator+(uint4 a, uint b)
{
    return make_uint4(a.x + b, a.y + b, a.z + b, a.w + b);
}
inline NV_HOSTDEVICE uint4 operator+(uint b, uint4 a)
{
    return make_uint4(a.x + b, a.y + b, a.z + b, a.w + b);
}
inline NV_HOSTDEVICE void operator+=(uint4& a, uint b)
{
    a.x += b;
    a.y += b;
    a.z += b;
    a.w += b;
}

////////////////////////////////////////////////////////////////////////////////
// subtract
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float2 operator-(float2 a, float2 b)
{
    return make_float2(a.x - b.x, a.y - b.y);
}
inline NV_HOSTDEVICE void operator-=(float2& a, float2 b)
{
    a.x -= b.x;
    a.y -= b.y;
}
inline NV_HOSTDEVICE float2 operator-(float2 a, float b)
{
    return make_float2(a.x - b, a.y - b);
}
inline NV_HOSTDEVICE float2 operator-(float b, float2 a)
{
    return make_float2(b - a.x, b - a.y);
}
inline NV_HOSTDEVICE void operator-=(float2& a, float b)
{
    a.x -= b;
    a.y -= b;
}

inline NV_HOSTDEVICE int2 operator-(int2 a, int2 b)
{
    return make_int2(a.x - b.x, a.y - b.y);
}
inline NV_HOSTDEVICE void operator-=(int2& a, int2 b)
{
    a.x -= b.x;
    a.y -= b.y;
}
inline NV_HOSTDEVICE int2 operator-(int2 a, int b)
{
    return make_int2(a.x - b, a.y - b);
}
inline NV_HOSTDEVICE int2 operator-(int b, int2 a)
{
    return make_int2(b - a.x, b - a.y);
}
inline NV_HOSTDEVICE void operator-=(int2& a, int b)
{
    a.x -= b;
    a.y -= b;
}

inline NV_HOSTDEVICE uint2 operator-(uint2 a, uint2 b)
{
    return make_uint2(a.x - b.x, a.y - b.y);
}
inline NV_HOSTDEVICE void operator-=(uint2& a, uint2 b)
{
    a.x -= b.x;
    a.y -= b.y;
}
inline NV_HOSTDEVICE uint2 operator-(uint2 a, uint b)
{
    return make_uint2(a.x - b, a.y - b);
}
inline NV_HOSTDEVICE uint2 operator-(uint b, uint2 a)
{
    return make_uint2(b - a.x, b - a.y);
}
inline NV_HOSTDEVICE void operator-=(uint2& a, uint b)
{
    a.x -= b;
    a.y -= b;
}

inline NV_HOSTDEVICE float3 operator-(float3 a, float3 b)
{
    return make_float3(a.x - b.x, a.y - b.y, a.z - b.z);
}
inline NV_HOSTDEVICE void operator-=(float3& a, float3 b)
{
    a.x -= b.x;
    a.y -= b.y;
    a.z -= b.z;
}
inline NV_HOSTDEVICE float3 operator-(float3 a, float b)
{
    return make_float3(a.x - b, a.y - b, a.z - b);
}
inline NV_HOSTDEVICE float3 operator-(float b, float3 a)
{
    return make_float3(b - a.x, b - a.y, b - a.z);
}
inline NV_HOSTDEVICE void operator-=(float3& a, float b)
{
    a.x -= b;
    a.y -= b;
    a.z -= b;
}

inline NV_HOSTDEVICE int3 operator-(int3 a, int3 b)
{
    return make_int3(a.x - b.x, a.y - b.y, a.z - b.z);
}
inline NV_HOSTDEVICE void operator-=(int3& a, int3 b)
{
    a.x -= b.x;
    a.y -= b.y;
    a.z -= b.z;
}
inline NV_HOSTDEVICE int3 operator-(int3 a, int b)
{
    return make_int3(a.x - b, a.y - b, a.z - b);
}
inline NV_HOSTDEVICE int3 operator-(int b, int3 a)
{
    return make_int3(b - a.x, b - a.y, b - a.z);
}
inline NV_HOSTDEVICE void operator-=(int3& a, int b)
{
    a.x -= b;
    a.y -= b;
    a.z -= b;
}

inline NV_HOSTDEVICE uint3 operator-(uint3 a, uint3 b)
{
    return make_uint3(a.x - b.x, a.y - b.y, a.z - b.z);
}
inline NV_HOSTDEVICE void operator-=(uint3& a, uint3 b)
{
    a.x -= b.x;
    a.y -= b.y;
    a.z -= b.z;
}
inline NV_HOSTDEVICE uint3 operator-(uint3 a, uint b)
{
    return make_uint3(a.x - b, a.y - b, a.z - b);
}
inline NV_HOSTDEVICE uint3 operator-(uint b, uint3 a)
{
    return make_uint3(b - a.x, b - a.y, b - a.z);
}
inline NV_HOSTDEVICE void operator-=(uint3& a, uint b)
{
    a.x -= b;
    a.y -= b;
    a.z -= b;
}

inline NV_HOSTDEVICE float4 operator-(float4 a, float4 b)
{
    return make_float4(a.x - b.x, a.y - b.y, a.z - b.z, a.w - b.w);
}
inline NV_HOSTDEVICE void operator-=(float4& a, float4 b)
{
    a.x -= b.x;
    a.y -= b.y;
    a.z -= b.z;
    a.w -= b.w;
}
inline NV_HOSTDEVICE float4 operator-(float4 a, float b)
{
    return make_float4(a.x - b, a.y - b, a.z - b, a.w - b);
}
inline NV_HOSTDEVICE void operator-=(float4& a, float b)
{
    a.x -= b;
    a.y -= b;
    a.z -= b;
    a.w -= b;
}

inline NV_HOSTDEVICE int4 operator-(int4 a, int4 b)
{
    return make_int4(a.x - b.x, a.y - b.y, a.z - b.z, a.w - b.w);
}
inline NV_HOSTDEVICE void operator-=(int4& a, int4 b)
{
    a.x -= b.x;
    a.y -= b.y;
    a.z -= b.z;
    a.w -= b.w;
}
inline NV_HOSTDEVICE int4 operator-(int4 a, int b)
{
    return make_int4(a.x - b, a.y - b, a.z - b, a.w - b);
}
inline NV_HOSTDEVICE int4 operator-(int b, int4 a)
{
    return make_int4(b - a.x, b - a.y, b - a.z, b - a.w);
}
inline NV_HOSTDEVICE void operator-=(int4& a, int b)
{
    a.x -= b;
    a.y -= b;
    a.z -= b;
    a.w -= b;
}

inline NV_HOSTDEVICE uint4 operator-(uint4 a, uint4 b)
{
    return make_uint4(a.x - b.x, a.y - b.y, a.z - b.z, a.w - b.w);
}
inline NV_HOSTDEVICE void operator-=(uint4& a, uint4 b)
{
    a.x -= b.x;
    a.y -= b.y;
    a.z -= b.z;
    a.w -= b.w;
}
inline NV_HOSTDEVICE uint4 operator-(uint4 a, uint b)
{
    return make_uint4(a.x - b, a.y - b, a.z - b, a.w - b);
}
inline NV_HOSTDEVICE uint4 operator-(uint b, uint4 a)
{
    return make_uint4(b - a.x, b - a.y, b - a.z, b - a.w);
}
inline NV_HOSTDEVICE void operator-=(uint4& a, uint b)
{
    a.x -= b;
    a.y -= b;
    a.z -= b;
    a.w -= b;
}

////////////////////////////////////////////////////////////////////////////////
// multiply
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float2 operator*(float2 a, float2 b)
{
    return make_float2(a.x * b.x, a.y * b.y);
}
inline NV_HOSTDEVICE void operator*=(float2& a, float2 b)
{
    a.x *= b.x;
    a.y *= b.y;
}
inline NV_HOSTDEVICE float2 operator*(float2 a, float b)
{
    return make_float2(a.x * b, a.y * b);
}
inline NV_HOSTDEVICE float2 operator*(float b, float2 a)
{
    return make_float2(b * a.x, b * a.y);
}
inline NV_HOSTDEVICE void operator*=(float2& a, float b)
{
    a.x *= b;
    a.y *= b;
}

inline NV_HOSTDEVICE int2 operator*(int2 a, int2 b)
{
    return make_int2(a.x * b.x, a.y * b.y);
}
inline NV_HOSTDEVICE void operator*=(int2& a, int2 b)
{
    a.x *= b.x;
    a.y *= b.y;
}
inline NV_HOSTDEVICE int2 operator*(int2 a, int b)
{
    return make_int2(a.x * b, a.y * b);
}
inline NV_HOSTDEVICE int2 operator*(int b, int2 a)
{
    return make_int2(b * a.x, b * a.y);
}
inline NV_HOSTDEVICE void operator*=(int2& a, int b)
{
    a.x *= b;
    a.y *= b;
}

inline NV_HOSTDEVICE uint2 operator*(uint2 a, uint2 b)
{
    return make_uint2(a.x * b.x, a.y * b.y);
}
inline NV_HOSTDEVICE void operator*=(uint2& a, uint2 b)
{
    a.x *= b.x;
    a.y *= b.y;
}
inline NV_HOSTDEVICE uint2 operator*(uint2 a, uint b)
{
    return make_uint2(a.x * b, a.y * b);
}
inline NV_HOSTDEVICE uint2 operator*(uint b, uint2 a)
{
    return make_uint2(b * a.x, b * a.y);
}
inline NV_HOSTDEVICE void operator*=(uint2& a, uint b)
{
    a.x *= b;
    a.y *= b;
}

inline NV_HOSTDEVICE float3 operator*(float3 a, float3 b)
{
    return make_float3(a.x * b.x, a.y * b.y, a.z * b.z);
}
inline NV_HOSTDEVICE void operator*=(float3& a, float3 b)
{
    a.x *= b.x;
    a.y *= b.y;
    a.z *= b.z;
}
inline NV_HOSTDEVICE float3 operator*(float3 a, float b)
{
    return make_float3(a.x * b, a.y * b, a.z * b);
}
inline NV_HOSTDEVICE float3 operator*(float b, float3 a)
{
    return make_float3(b * a.x, b * a.y, b * a.z);
}
inline NV_HOSTDEVICE void operator*=(float3& a, float b)
{
    a.x *= b;
    a.y *= b;
    a.z *= b;
}

inline NV_HOSTDEVICE int3 operator*(int3 a, int3 b)
{
    return make_int3(a.x * b.x, a.y * b.y, a.z * b.z);
}
inline NV_HOSTDEVICE void operator*=(int3& a, int3 b)
{
    a.x *= b.x;
    a.y *= b.y;
    a.z *= b.z;
}
inline NV_HOSTDEVICE int3 operator*(int3 a, int b)
{
    return make_int3(a.x * b, a.y * b, a.z * b);
}
inline NV_HOSTDEVICE int3 operator*(int b, int3 a)
{
    return make_int3(b * a.x, b * a.y, b * a.z);
}
inline NV_HOSTDEVICE void operator*=(int3& a, int b)
{
    a.x *= b;
    a.y *= b;
    a.z *= b;
}

inline NV_HOSTDEVICE uint3 operator*(uint3 a, uint3 b)
{
    return make_uint3(a.x * b.x, a.y * b.y, a.z * b.z);
}
inline NV_HOSTDEVICE void operator*=(uint3& a, uint3 b)
{
    a.x *= b.x;
    a.y *= b.y;
    a.z *= b.z;
}
inline NV_HOSTDEVICE uint3 operator*(uint3 a, uint b)
{
    return make_uint3(a.x * b, a.y * b, a.z * b);
}
inline NV_HOSTDEVICE uint3 operator*(uint b, uint3 a)
{
    return make_uint3(b * a.x, b * a.y, b * a.z);
}
inline NV_HOSTDEVICE void operator*=(uint3& a, uint b)
{
    a.x *= b;
    a.y *= b;
    a.z *= b;
}

inline NV_HOSTDEVICE float4 operator*(float4 a, float4 b)
{
    return make_float4(a.x * b.x, a.y * b.y, a.z * b.z, a.w * b.w);
}
inline NV_HOSTDEVICE void operator*=(float4& a, float4 b)
{
    a.x *= b.x;
    a.y *= b.y;
    a.z *= b.z;
    a.w *= b.w;
}
inline NV_HOSTDEVICE float4 operator*(float4 a, float b)
{
    return make_float4(a.x * b, a.y * b, a.z * b, a.w * b);
}
inline NV_HOSTDEVICE float4 operator*(float b, float4 a)
{
    return make_float4(b * a.x, b * a.y, b * a.z, b * a.w);
}
inline NV_HOSTDEVICE void operator*=(float4& a, float b)
{
    a.x *= b;
    a.y *= b;
    a.z *= b;
    a.w *= b;
}

inline NV_HOSTDEVICE int4 operator*(int4 a, int4 b)
{
    return make_int4(a.x * b.x, a.y * b.y, a.z * b.z, a.w * b.w);
}
inline NV_HOSTDEVICE void operator*=(int4& a, int4 b)
{
    a.x *= b.x;
    a.y *= b.y;
    a.z *= b.z;
    a.w *= b.w;
}
inline NV_HOSTDEVICE int4 operator*(int4 a, int b)
{
    return make_int4(a.x * b, a.y * b, a.z * b, a.w * b);
}
inline NV_HOSTDEVICE int4 operator*(int b, int4 a)
{
    return make_int4(b * a.x, b * a.y, b * a.z, b * a.w);
}
inline NV_HOSTDEVICE void operator*=(int4& a, int b)
{
    a.x *= b;
    a.y *= b;
    a.z *= b;
    a.w *= b;
}

inline NV_HOSTDEVICE uint4 operator*(uint4 a, uint4 b)
{
    return make_uint4(a.x * b.x, a.y * b.y, a.z * b.z, a.w * b.w);
}
inline NV_HOSTDEVICE void operator*=(uint4& a, uint4 b)
{
    a.x *= b.x;
    a.y *= b.y;
    a.z *= b.z;
    a.w *= b.w;
}
inline NV_HOSTDEVICE uint4 operator*(uint4 a, uint b)
{
    return make_uint4(a.x * b, a.y * b, a.z * b, a.w * b);
}
inline NV_HOSTDEVICE uint4 operator*(uint b, uint4 a)
{
    return make_uint4(b * a.x, b * a.y, b * a.z, b * a.w);
}
inline NV_HOSTDEVICE void operator*=(uint4& a, uint b)
{
    a.x *= b;
    a.y *= b;
    a.z *= b;
    a.w *= b;
}

////////////////////////////////////////////////////////////////////////////////
// divide
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float2 operator/(float2 a, float2 b)
{
    return make_float2(a.x / b.x, a.y / b.y);
}
inline NV_HOSTDEVICE void operator/=(float2& a, float2 b)
{
    a.x /= b.x;
    a.y /= b.y;
}
inline NV_HOSTDEVICE float2 operator/(float2 a, float b)
{
    return make_float2(a.x / b, a.y / b);
}
inline NV_HOSTDEVICE void operator/=(float2& a, float b)
{
    a.x /= b;
    a.y /= b;
}
inline NV_HOSTDEVICE float2 operator/(float b, float2 a)
{
    return make_float2(b / a.x, b / a.y);
}

inline NV_HOSTDEVICE float3 operator/(float3 a, float3 b)
{
    return make_float3(a.x / b.x, a.y / b.y, a.z / b.z);
}
inline NV_HOSTDEVICE void operator/=(float3& a, float3 b)
{
    a.x /= b.x;
    a.y /= b.y;
    a.z /= b.z;
}
inline NV_HOSTDEVICE float3 operator/(float3 a, float b)
{
    return make_float3(a.x / b, a.y / b, a.z / b);
}
inline NV_HOSTDEVICE void operator/=(float3& a, float b)
{
    a.x /= b;
    a.y /= b;
    a.z /= b;
}
inline NV_HOSTDEVICE float3 operator/(float b, float3 a)
{
    return make_float3(b / a.x, b / a.y, b / a.z);
}

inline NV_HOSTDEVICE float4 operator/(float4 a, float4 b)
{
    return make_float4(a.x / b.x, a.y / b.y, a.z / b.z, a.w / b.w);
}
inline NV_HOSTDEVICE void operator/=(float4& a, float4 b)
{
    a.x /= b.x;
    a.y /= b.y;
    a.z /= b.z;
    a.w /= b.w;
}
inline NV_HOSTDEVICE float4 operator/(float4 a, float b)
{
    return make_float4(a.x / b, a.y / b, a.z / b, a.w / b);
}
inline NV_HOSTDEVICE void operator/=(float4& a, float b)
{
    a.x /= b;
    a.y /= b;
    a.z /= b;
    a.w /= b;
}
inline NV_HOSTDEVICE float4 operator/(float b, float4 a)
{
    return make_float4(b / a.x, b / a.y, b / a.z, b / a.w);
}

////////////////////////////////////////////////////////////////////////////////
// min
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float2 fminf(float2 a, float2 b)
{
    return make_float2(fminf(a.x, b.x), fminf(a.y, b.y));
}
inline NV_HOSTDEVICE float3 fminf(float3 a, float3 b)
{
    return make_float3(fminf(a.x, b.x), fminf(a.y, b.y), fminf(a.z, b.z));
}
inline NV_HOSTDEVICE float4 fminf(float4 a, float4 b)
{
    return make_float4(fminf(a.x, b.x), fminf(a.y, b.y), fminf(a.z, b.z), fminf(a.w, b.w));
}

inline NV_HOSTDEVICE int2 min(int2 a, int2 b)
{
    return make_int2(min(a.x, b.x), min(a.y, b.y));
}
inline NV_HOSTDEVICE int3 min(int3 a, int3 b)
{
    return make_int3(min(a.x, b.x), min(a.y, b.y), min(a.z, b.z));
}
inline NV_HOSTDEVICE int4 min(int4 a, int4 b)
{
    return make_int4(min(a.x, b.x), min(a.y, b.y), min(a.z, b.z), min(a.w, b.w));
}

inline NV_HOSTDEVICE uint2 min(uint2 a, uint2 b)
{
    return make_uint2(min(a.x, b.x), min(a.y, b.y));
}
inline NV_HOSTDEVICE uint3 min(uint3 a, uint3 b)
{
    return make_uint3(min(a.x, b.x), min(a.y, b.y), min(a.z, b.z));
}
inline NV_HOSTDEVICE uint4 min(uint4 a, uint4 b)
{
    return make_uint4(min(a.x, b.x), min(a.y, b.y), min(a.z, b.z), min(a.w, b.w));
}

////////////////////////////////////////////////////////////////////////////////
// max
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float2 fmaxf(float2 a, float2 b)
{
    return make_float2(fmaxf(a.x, b.x), fmaxf(a.y, b.y));
}
inline NV_HOSTDEVICE float3 fmaxf(float3 a, float3 b)
{
    return make_float3(fmaxf(a.x, b.x), fmaxf(a.y, b.y), fmaxf(a.z, b.z));
}
inline NV_HOSTDEVICE float4 fmaxf(float4 a, float4 b)
{
    return make_float4(fmaxf(a.x, b.x), fmaxf(a.y, b.y), fmaxf(a.z, b.z), fmaxf(a.w, b.w));
}

inline NV_HOSTDEVICE int2 max(int2 a, int2 b)
{
    return make_int2(max(a.x, b.x), max(a.y, b.y));
}
inline NV_HOSTDEVICE int3 max(int3 a, int3 b)
{
    return make_int3(max(a.x, b.x), max(a.y, b.y), max(a.z, b.z));
}
inline NV_HOSTDEVICE int4 max(int4 a, int4 b)
{
    return make_int4(max(a.x, b.x), max(a.y, b.y), max(a.z, b.z), max(a.w, b.w));
}

inline NV_HOSTDEVICE uint2 max(uint2 a, uint2 b)
{
    return make_uint2(max(a.x, b.x), max(a.y, b.y));
}
inline NV_HOSTDEVICE uint3 max(uint3 a, uint3 b)
{
    return make_uint3(max(a.x, b.x), max(a.y, b.y), max(a.z, b.z));
}
inline NV_HOSTDEVICE uint4 max(uint4 a, uint4 b)
{
    return make_uint4(max(a.x, b.x), max(a.y, b.y), max(a.z, b.z), max(a.w, b.w));
}

////////////////////////////////////////////////////////////////////////////////
// lerp
// - linear interpolation between a and b, based on value t in [0, 1] range
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float lerp(float a, float b, float t)
{
    return a + t * (b - a);
}
inline NV_HOSTDEVICE float2 lerp(float2 a, float2 b, float t)
{
    return a + t * (b - a);
}
inline NV_HOSTDEVICE float3 lerp(float3 a, float3 b, float t)
{
    return a + t * (b - a);
}
inline NV_HOSTDEVICE float4 lerp(float4 a, float4 b, float t)
{
    return a + t * (b - a);
}

////////////////////////////////////////////////////////////////////////////////
// clamp
// - clamp the value v to be in the range [a, b]
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float clamp(float f, float a, float b)
{
    return fmaxf(a, fminf(f, b));
}
inline NV_HOSTDEVICE int clamp(int f, int a, int b)
{
    return max(a, min(f, b));
}
inline NV_HOSTDEVICE uint clamp(uint f, uint a, uint b)
{
    return max(a, min(f, b));
}

inline NV_HOSTDEVICE float2 clamp(float2 v, float a, float b)
{
    return make_float2(clamp(v.x, a, b), clamp(v.y, a, b));
}
inline NV_HOSTDEVICE float2 clamp(float2 v, float2 a, float2 b)
{
    return make_float2(clamp(v.x, a.x, b.x), clamp(v.y, a.y, b.y));
}
inline NV_HOSTDEVICE float3 clamp(float3 v, float a, float b)
{
    return make_float3(clamp(v.x, a, b), clamp(v.y, a, b), clamp(v.z, a, b));
}
inline NV_HOSTDEVICE float3 clamp(float3 v, float3 a, float3 b)
{
    return make_float3(clamp(v.x, a.x, b.x), clamp(v.y, a.y, b.y), clamp(v.z, a.z, b.z));
}
inline NV_HOSTDEVICE float4 clamp(float4 v, float a, float b)
{
    return make_float4(clamp(v.x, a, b), clamp(v.y, a, b), clamp(v.z, a, b), clamp(v.w, a, b));
}
inline NV_HOSTDEVICE float4 clamp(float4 v, float4 a, float4 b)
{
    return make_float4(clamp(v.x, a.x, b.x), clamp(v.y, a.y, b.y), clamp(v.z, a.z, b.z), clamp(v.w, a.w, b.w));
}

inline NV_HOSTDEVICE int2 clamp(int2 v, int a, int b)
{
    return make_int2(clamp(v.x, a, b), clamp(v.y, a, b));
}
inline NV_HOSTDEVICE int2 clamp(int2 v, int2 a, int2 b)
{
    return make_int2(clamp(v.x, a.x, b.x), clamp(v.y, a.y, b.y));
}
inline NV_HOSTDEVICE int3 clamp(int3 v, int a, int b)
{
    return make_int3(clamp(v.x, a, b), clamp(v.y, a, b), clamp(v.z, a, b));
}
inline NV_HOSTDEVICE int3 clamp(int3 v, int3 a, int3 b)
{
    return make_int3(clamp(v.x, a.x, b.x), clamp(v.y, a.y, b.y), clamp(v.z, a.z, b.z));
}
inline NV_HOSTDEVICE int4 clamp(int4 v, int a, int b)
{
    return make_int4(clamp(v.x, a, b), clamp(v.y, a, b), clamp(v.z, a, b), clamp(v.w, a, b));
}
inline NV_HOSTDEVICE int4 clamp(int4 v, int4 a, int4 b)
{
    return make_int4(clamp(v.x, a.x, b.x), clamp(v.y, a.y, b.y), clamp(v.z, a.z, b.z), clamp(v.w, a.w, b.w));
}

inline NV_HOSTDEVICE uint2 clamp(uint2 v, uint a, uint b)
{
    return make_uint2(clamp(v.x, a, b), clamp(v.y, a, b));
}
inline NV_HOSTDEVICE uint2 clamp(uint2 v, uint2 a, uint2 b)
{
    return make_uint2(clamp(v.x, a.x, b.x), clamp(v.y, a.y, b.y));
}
inline NV_HOSTDEVICE uint3 clamp(uint3 v, uint a, uint b)
{
    return make_uint3(clamp(v.x, a, b), clamp(v.y, a, b), clamp(v.z, a, b));
}
inline NV_HOSTDEVICE uint3 clamp(uint3 v, uint3 a, uint3 b)
{
    return make_uint3(clamp(v.x, a.x, b.x), clamp(v.y, a.y, b.y), clamp(v.z, a.z, b.z));
}
inline NV_HOSTDEVICE uint4 clamp(uint4 v, uint a, uint b)
{
    return make_uint4(clamp(v.x, a, b), clamp(v.y, a, b), clamp(v.z, a, b), clamp(v.w, a, b));
}
inline NV_HOSTDEVICE uint4 clamp(uint4 v, uint4 a, uint4 b)
{
    return make_uint4(clamp(v.x, a.x, b.x), clamp(v.y, a.y, b.y), clamp(v.z, a.z, b.z), clamp(v.w, a.w, b.w));
}

////////////////////////////////////////////////////////////////////////////////
// dot product
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float dot(float2 a, float2 b)
{
    return a.x * b.x + a.y * b.y;
}
inline NV_HOSTDEVICE float dot(float3 a, float3 b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z;
}
inline NV_HOSTDEVICE float dot(float4 a, float4 b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
}

inline NV_HOSTDEVICE int dot(int2 a, int2 b)
{
    return a.x * b.x + a.y * b.y;
}
inline NV_HOSTDEVICE int dot(int3 a, int3 b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z;
}
inline NV_HOSTDEVICE int dot(int4 a, int4 b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
}

inline NV_HOSTDEVICE uint dot(uint2 a, uint2 b)
{
    return a.x * b.x + a.y * b.y;
}
inline NV_HOSTDEVICE uint dot(uint3 a, uint3 b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z;
}
inline NV_HOSTDEVICE uint dot(uint4 a, uint4 b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
}

////////////////////////////////////////////////////////////////////////////////
// length
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float length(float2 v)
{
    return sqrtf(dot(v, v));
}
inline NV_HOSTDEVICE float length(float3 v)
{
    return sqrtf(dot(v, v));
}
inline NV_HOSTDEVICE float length(float4 v)
{
    return sqrtf(dot(v, v));
}

////////////////////////////////////////////////////////////////////////////////
// normalize
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float2 normalize(float2 v)
{
    float invLen = rsqrtf(dot(v, v));
    return v * invLen;
}
inline NV_HOSTDEVICE float3 normalize(float3 v)
{
    float invLen = rsqrtf(dot(v, v));
    return v * invLen;
}
inline NV_HOSTDEVICE float4 normalize(float4 v)
{
    float invLen = rsqrtf(dot(v, v));
    return v * invLen;
}

////////////////////////////////////////////////////////////////////////////////
// floor
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float2 floorf(float2 v)
{
    return make_float2(::floorf(v.x), ::floorf(v.y));
}
inline NV_HOSTDEVICE float3 floorf(float3 v)
{
    return make_float3(::floorf(v.x), ::floorf(v.y), ::floorf(v.z));
}
inline NV_HOSTDEVICE float4 floorf(float4 v)
{
    return make_float4(::floorf(v.x), ::floorf(v.y), ::floorf(v.z), ::floorf(v.w));
}

////////////////////////////////////////////////////////////////////////////////
// frac - returns the fractional portion of a scalar or each vector component
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float fracf(float v)
{
    return v - ::floorf(v);
}
inline NV_HOSTDEVICE float2 fracf(float2 v)
{
    return make_float2(fracf(v.x), fracf(v.y));
}
inline NV_HOSTDEVICE float3 fracf(float3 v)
{
    return make_float3(fracf(v.x), fracf(v.y), fracf(v.z));
}
inline NV_HOSTDEVICE float4 fracf(float4 v)
{
    return make_float4(fracf(v.x), fracf(v.y), fracf(v.z), fracf(v.w));
}

////////////////////////////////////////////////////////////////////////////////
// fmod
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float2 fmodf(float2 a, float2 b)
{
    return make_float2(::fmodf(a.x, b.x), ::fmodf(a.y, b.y));
}
inline NV_HOSTDEVICE float3 fmodf(float3 a, float3 b)
{
    return make_float3(::fmodf(a.x, b.x), ::fmodf(a.y, b.y), ::fmodf(a.z, b.z));
}
inline NV_HOSTDEVICE float4 fmodf(float4 a, float4 b)
{
    return make_float4(::fmodf(a.x, b.x), ::fmodf(a.y, b.y), ::fmodf(a.z, b.z), ::fmodf(a.w, b.w));
}

////////////////////////////////////////////////////////////////////////////////
// absolute value
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float2 fabs(float2 v)
{
    return make_float2(::fabs(v.x), ::fabs(v.y));
}
inline NV_HOSTDEVICE float3 fabs(float3 v)
{
    return make_float3(::fabs(v.x), ::fabs(v.y), ::fabs(v.z));
}
inline NV_HOSTDEVICE float4 fabs(float4 v)
{
    return make_float4(::fabs(v.x), ::fabs(v.y), ::fabs(v.z), ::fabs(v.w));
}

inline NV_HOSTDEVICE int2 abs(int2 v)
{
    return make_int2(::abs(v.x), ::abs(v.y));
}
inline NV_HOSTDEVICE int3 abs(int3 v)
{
    return make_int3(::abs(v.x), ::abs(v.y), ::abs(v.z));
}
inline NV_HOSTDEVICE int4 abs(int4 v)
{
    return make_int4(::abs(v.x), ::abs(v.y), ::abs(v.z), ::abs(v.w));
}

////////////////////////////////////////////////////////////////////////////////
// reflect
// - returns reflection of incident ray I around surface normal N
// - N should be normalized, reflected vector's length is equal to length of I
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float3 reflect(float3 i, float3 n)
{
    return i - 2.0f * n * dot(n, i);
}

////////////////////////////////////////////////////////////////////////////////
// cross product
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float3 cross(float3 a, float3 b)
{
    return make_float3(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x);
}

////////////////////////////////////////////////////////////////////////////////
// smoothstep
// - returns 0 if x < a
// - returns 1 if x > b
// - otherwise returns smooth interpolation between 0 and 1 based on x
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float smoothstep(float a, float b, float x)
{
    float y = clamp((x - a) / (b - a), 0.0f, 1.0f);
    return (y * y * (3.0f - (2.0f * y)));
}
inline NV_HOSTDEVICE float2 smoothstep(float2 a, float2 b, float2 x)
{
    float2 y = clamp((x - a) / (b - a), 0.0f, 1.0f);
    return (y * y * (make_float2(3.0f) - (make_float2(2.0f) * y)));
}
inline NV_HOSTDEVICE float3 smoothstep(float3 a, float3 b, float3 x)
{
    float3 y = clamp((x - a) / (b - a), 0.0f, 1.0f);
    return (y * y * (make_float3(3.0f) - (make_float3(2.0f) * y)));
}
inline NV_HOSTDEVICE float4 smoothstep(float4 a, float4 b, float4 x)
{
    float4 y = clamp((x - a) / (b - a), 0.0f, 1.0f);
    return (y * y * (make_float4(3.0f) - (make_float4(2.0f) * y)));
}


//-----------------------------------------------------------------------------
NV_HOSTDEVICE
inline float3 rotateVector(const float4& q, const float3& v)
{
    const float3 Q{ q.x, q.y, q.z };
    const float3 T{ cross(Q, v) * 2.f };
    // const float3 result = v + (q.w * T) + cross(Q, T);
    float3 result = (q.w * q.w - dot(Q, Q)) * v + 2.f * dot(Q, v) * Q + 2.f * q.w * T;
    result = normalize(result);

    return result;
}

////////////////////////////////////////////////////////////////////////////////
// buildRotationMatrixForVectors
// - builds a rotation Matrix from source and destination vectors
// - rotates new vector into new rotated space
////////////////////////////////////////////////////////////////////////////////

inline NV_HOSTDEVICE float3 buildTangentSpaceVectorFromVectorSpace(const float3& src,
                                                                   const float3& dst,
                                                                   const float3& newVector)
{
    // src and dst vectors are assumed to be normalized
    float3 crossProd = cross(newVector, dst);
    float alpha = acosf(dot(src, dst));
    float sinAlpha = sinf(alpha / 2.0f);
    float cosAlpha = cosf(alpha / 2.0f);
    float4 quaternionRotator =
        make_float4(sinAlpha * crossProd.x, sinAlpha * crossProd.y, sinAlpha * crossProd.z, cosAlpha);
    float3 newNormTangentSpace = rotateVector(quaternionRotator, newVector);

    return newNormTangentSpace;
}

//-----------------------------------------------------------------------------
template <typename T>
inline NV_HOSTDEVICE T Pow(const T x, const int n)
{
    T result{ 1 };
    switch (n)
    {
    case 0:
        result = 1;
        break;
    case 1:
        result = x;
        break;
    case 2:
        result = x * x;
        break;
    case 3:
        result = x * x * x;
        break;
    case 4:
        result = x * x * x * x;
        break;
    case 5:
        result = x * x * x * x * x;
        break;
    case 6:
        result = x * x * x * x * x * x;
        break;
    case 7:
        result = x * x * x * x * x * x * x;
        break;
    case 8:
        result = x * x * x * x * x * x * x * x;
        break;
    case 9:
        result = x * x * x * x * x * x * x * x * x;
        break;
    default:
    {
        for (int i = 0; i < n; ++i)
        {
            result *= x;
        }
        break;
    }
    }
    return result;
}

//-----------------------------------------------------------------------------
template <typename T>
inline NV_HOSTDEVICE T DivideRoundUp(const T& x, const T& y)
{
    return (x + (y - T{ 1 })) / y;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float CosineFactor(float t)
{
    return (1.f - cosf(t * PI)) / 2.f;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float CosineFactorApprox(float t)
{
    return t * t * (3.f - 2.f * t);
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float Deg2Rad(float deg)
{
    return (deg / 180.f) * PI;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float Rad2Deg(float rad)
{
    return (rad / PI) * 180.f;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float ConeSpotArea(float r, float angleRad)
{
    // iterentiev: assuming small beam divergence angle where tan(a) ~ a
    const float spotRadius = r * angleRad;
    return PI * spotRadius * spotRadius;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float SphereArea(float r)
{
    return 4.f * PI * r * r;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float TriangleWave(float t, float amp, float period)
{
    const float p = 1.f / period;
    return amp * fabsf(2.f * (t * p - ::floorf(t * p + 0.5f)));
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float3 RotateYZ(float3 v, float sa, float ca, float se, float ce)
{
    float3 out;

    out.x = ce * ca * v.x - ce * sa * v.y + se * v.z;
    out.y = sa * v.x + ca * v.y;
    out.z = -se * ca * v.x + se * sa * v.y + ce * v.z;

    return out;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float3 ToSpherical(float3 vec)
{
    const float length = sqrtf(dot(vec, vec));

    const float phi = (vec.x == 0.f && vec.y == 0.f) ? 0.f : atan2f(vec.y, vec.x);
    const float the = acosf(vec.z / length);

    return { phi, the, length };
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float3 Rotate(const float4& q, const float3& v)
{
    const float3 Q{ q.x, q.y, q.z };
    const float3 T = cross(Q, v) * 2.f;
    const float3 result = v + (q.w * T) + cross(Q, T);

    return result;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float4 MultiplyQs(const float4& q1, const float4& q2)
{
    float3 Q1{ q1.x, q1.y, q1.z };
    float3 Q2{ q2.x, q2.y, q2.z };
    float result_s;
    float3 result_v;
    result_s = (q1.w * q2.w) - dot(Q1, Q2);
    result_v = (q1.w * Q2) + (q2.w * Q1) + cross(Q1, Q2);

    return { result_v.x, result_v.y, result_v.z, result_s };
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float4 ConjugateQ(const float4& q)
{
    return { -q.x, -q.y, -q.z, q.w };
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float4 ReciprocateQ(const float4& q)
{
    return (ConjugateQ(q) / dot(q, q));
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float4 ConjugateQByQ(const float4& q1, const float4& q2)
{
    return MultiplyQs(q2, MultiplyQs(q1, ReciprocateQ(q2)));
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float3 ConjugateVByQ(const float3& v, const float4& q)
{
    float4 tmpQ{ v.x, v.y, v.z, 0 };

    tmpQ = ConjugateQByQ(tmpQ, q);

    return { tmpQ.x, tmpQ.y, tmpQ.z };
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float TodBsm(float rcsm2)
{
    return 10.f * log10f(rcsm2);
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE bool operator<(float3 a, float3 b)
{
    return a.x < b.x && a.y < b.y && a.z < b.z;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE bool float3DifferenceClose(float3 a, float3 b, float threshold)
{
    return (fabsf(a.x - b.x) < threshold) && (fabsf(a.y - b.y) < threshold) && (fabsf(a.z - b.z) < threshold);
}


//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float3 parallelVectorProjection(float3 a, float3 b)
{
    float scalar_projection = dot(a, normalize(b));
    float3 parallel_projection = scalar_projection * normalize(b);
    return parallel_projection;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float3 perpendicularVectorProjection(float3 a, float3 b)
{
    // projects a onto b
    // https://en.wikipedia.org/wiki/Vector_projection
    float3 parallel_projection = parallelVectorProjection(a, b);
    float3 perpendicular_projection = a - parallel_projection;
    return perpendicular_projection;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE bool isFiniteVector(const float* vector, int length)
{
    for (int i = 0; i < length; i++)
    {
        if (!isfinite(vector[i]))
        {
            return false;
        }
        if (::fabsf(vector[i]) > 100)
        {
            return false;
        }
    }
    return true;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float4 toQuaternion(float3 rollPitchYawRad)
{
    rollPitchYawRad *= 0.5f;

    const float cr = cosf(rollPitchYawRad.x);
    const float sr = sinf(rollPitchYawRad.x);
    const float cp = cosf(rollPitchYawRad.y);
    const float sp = sinf(rollPitchYawRad.y);
    const float cy = cosf(rollPitchYawRad.z);
    const float sy = sinf(rollPitchYawRad.z);

    return { sr * cp * cy - cr * sp * sy, cr * sp * cy + sr * cp * sy, cr * cp * sy - sr * sp * cy,
             cr * cp * cy + sr * sp * sy };
}

//-----------------------------------------------------------------------------
// This version does not account for gimbal lock
inline NV_HOSTDEVICE float3 toRollPitchYaw(float4 q)
{
    // https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles#Source_Code_2

    float3 angles;
    // roll (x-axis rotation)
    float sinr_cosp{ 2.f * (q.w * q.x + q.y * q.z) };
    float cosr_cosp{ 1.f - 2.f * (q.x * q.x + q.y * q.y) };
    angles.x = atan2f(sinr_cosp, cosr_cosp);

    // pitch (y-axis rotation)
    float sinp{ 2.f * (q.w * q.y - q.z * q.x) };
    if (fabsf(sinp) >= 1.f)
        angles.y = copysignf(PI / 2.f, sinp); // use 90 degrees if out of range
    else
        angles.y = asinf(sinp);

    // yaw (z-axis rotation)
    float siny_cosp{ 2 * (q.w * q.z + q.x * q.y) };
    float cosy_cosp{ 1 - 2 * (q.y * q.y + q.z * q.z) };
    angles.z = atan2f(siny_cosp, cosy_cosp);

    return angles;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float angleBetweenVectors(const float3& a, const float3& b)
{
    return acos(dot(a, b) / (length(a) * length(b)));
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float4 Qlerp(const float4& a, const float4& b, const float t)
{
    return normalize((1 - t) * a + t * b);
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float4 Qslerp(const float4& q1, const float4& q2, const float t)
{
    float4 qa = q1;
    float4 qb = q2;
    // Calculate angle between them.
    float cosHalfTheta = dot(qa, qb);
    // if qa=qb or qa=-qb then theta = 0 and we can return qa
    if (fabsf(cosHalfTheta) >= 0.999f)
    {
        return qa;
    }
    // if qb is in the opposite sphere, use the short angle
    if (cosHalfTheta < 0.0f)
    {
        qb = -1 * qb;
        cosHalfTheta = -cosHalfTheta;
    }
    // Calculate temporary values.
    float halfTheta = acosf(cosHalfTheta);
    float sinHalfTheta = sqrtf(1.0f - cosHalfTheta * cosHalfTheta);
    float ratioA = sinf((1 - t) * halfTheta) / sinHalfTheta;
    float ratioB = sinf(t * halfTheta) / sinHalfTheta;
    // calculate Quaternion.
    return (qa * ratioA + qb * ratioB);
}

//-----------------------------------------------------------------------------
/* wrap x -> [0,max) */
inline NV_HOSTDEVICE float wrapMax(float x, float max)
{
    /* integer math: `(max + x % max) % max` */
    return fmodf(max + fmodf(x, max), max);
}

//-----------------------------------------------------------------------------
/* wrap x -> [min,max) */
inline NV_HOSTDEVICE float wrapMinMax(float x, float min, float max)
{
    return min + wrapMax(x - min, max - min);
}

////////////////////////////////////////////////////////////////////////////////
// Complex types and Jones Matrix handlers
////////////////////////////////////////////////////////////////////////////////
//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float dotConjReal(const cuFloatComplex& value1, const cuFloatComplex& value2)
{
    return value1.x * value2.x + value1.y * value2.y;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float dotConjImag(const cuFloatComplex& value1, const cuFloatComplex& value2)
{
    return value1.y * value2.x - value1.x * value2.y;
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE float argf(const cuFloatComplex& value)
{
    return atan2f(value.y, value.x);
}

//-----------------------------------------------------------------------------
inline NV_HOSTDEVICE cuFloatComplex sqrtf(const cuFloatComplex& value)
{
    // cuFloatComplex is intrinsically a float2 type. The length function
    // is the same whether it is a real float2 vector or a complex expression
    const float magnitude{ sqrtf(length(value)) };
    const float argument{ 0.5f * argf(value) };
    return make_cuFloatComplex(magnitude * cosf(argument), magnitude * sinf(argument));
}

// Vector and matrix wrappers for handling scalar and complex types for
// jones vector math in handling phase and polarization aspects of light
template <typename T>
struct Vector2
{
    T e0, e1;

    NV_HOSTDEVICE Vector2<T>(T e0, T e1) : e0(e0), e1(e1){};

    NV_HOSTDEVICE Vector2<T>(){};

    NV_HOSTDEVICE void set(const T& e0, const T& e1)
    {
        this->e0 = e0;
        this->e1 = e1;
    }

    NV_HOSTDEVICE Vector2<T> operator+(const Vector2<T>& other) const
    {
        return Vector2<T>(e0 + other.e0, e1 + other.e1);
    }

    NV_HOSTDEVICE Vector2<T>& operator+=(const Vector2<T>& rhs)
    {
        this->e0 += rhs.e0;
        this->e1 += rhs.e1;
        return *this;
    }

    NV_HOSTDEVICE Vector2<T> operator-(const Vector2<T>& other) const
    {
        return Vector2<T>(e0 - other.e0, e1 - other.e1);
    }

    NV_HOSTDEVICE Vector2<T>& operator-=(const Vector2<T>& rhs)
    {
        this->e0 -= rhs.e0;
        this->e1 -= rhs.e1;
        return *this;
    }

    NV_HOSTDEVICE Vector2<T> operator*(const T& other) const
    {
        return Vector2<T>(e0 * other, e1 * other);
    }

    NV_HOSTDEVICE Vector2<T>& operator*=(const Vector2<T>& rhs)
    {
        this->e0 *= rhs.e0;
        this->e1 *= rhs.e1;
        return *this;
    }

    template <typename U>
    NV_HOSTDEVICE Vector2<T>& operator*=(const U& rhs)
    {
        this->e0 = this->e0 * rhs;
        this->e1 = this->e1 * rhs;
        return *this;
    }

    NV_HOSTDEVICE T dot(const T& other) const
    {
        return e0 * other.e0 + e1 * other.e1;
    }

    NV_HOSTDEVICE void sqrt()
    {
        e0 = sqrtf(e0);
        e1 = sqrtf(e1);
    }
};

template <>
struct Vector2<cuFloatComplex>
{
    cuFloatComplex e0, e1;

    NV_HOSTDEVICE Vector2<cuFloatComplex>(cuFloatComplex e0, cuFloatComplex e1) : e0(e0), e1(e1){};

    NV_HOSTDEVICE Vector2<cuFloatComplex>(){};

    NV_HOSTDEVICE void set(const cuFloatComplex& e0, const cuFloatComplex& e1)
    {
        this->e0 = e0;
        this->e1 = e1;
    }

    NV_HOSTDEVICE Vector2<cuFloatComplex> operator+(const Vector2<cuFloatComplex>& other) const
    {
        return Vector2<cuFloatComplex>(cuCaddf(e0, other.e0), cuCaddf(e1, other.e1));
    }

    NV_HOSTDEVICE Vector2<cuFloatComplex>& operator+=(const Vector2<cuFloatComplex>& rhs)
    {
        this->e0 = cuCaddf(this->e0, rhs.e0);
        this->e1 = cuCaddf(this->e1, rhs.e1);
        return *this;
    }

    NV_HOSTDEVICE Vector2<cuFloatComplex> operator-(const Vector2<cuFloatComplex>& other) const
    {
        return Vector2<cuFloatComplex>(cuCsubf(e0, other.e0), cuCsubf(e1, other.e1));
    }

    NV_HOSTDEVICE Vector2<cuFloatComplex>& operator-=(const Vector2<cuFloatComplex>& rhs)
    {
        this->e0 = cuCsubf(this->e0, rhs.e0);
        this->e1 = cuCsubf(this->e1, rhs.e1);
        return *this;
    }

    NV_HOSTDEVICE Vector2<cuFloatComplex> operator*(const cuFloatComplex& other) const
    {
        return Vector2<cuFloatComplex>(cuCmulf(e0, other), cuCmulf(e1, other));
    }

    NV_HOSTDEVICE Vector2<cuFloatComplex>& operator*=(const Vector2<cuFloatComplex>& rhs)
    {
        this->e0 = cuCmulf(this->e0, rhs.e0);
        this->e1 = cuCmulf(this->e1, rhs.e1);
        return *this;
    }

    template <typename U>
    NV_HOSTDEVICE Vector2<cuFloatComplex>& operator*=(const U& rhs)
    {
        this->e0 = this->e0 * rhs;
        this->e1 = this->e1 * rhs;
        return *this;
    }

    NV_HOSTDEVICE void sqrt()
    {
        e0 = sqrtf(e0);
        e1 = sqrtf(e1);
    }
};

template <typename T>
struct Matrix2x2
{
    T e00, e01, e10, e11;

    NV_HOSTDEVICE Matrix2x2<T>(){};
    NV_HOSTDEVICE Matrix2x2<T>(T e00, T e01, T e10, T e11) : e00(e00), e01(e01), e10(e10), e11(e11){};

    // Create a rotation matrix with the given angle (in radians).
    // TODO: restrict the angle and also the outputted matrix to real floats.
    // Need to write real matrix * complex matrix, and real matrix * complex vector for that.
    NV_HOSTDEVICE static Matrix2x2<T> createRotationMatrix(T angle)
    {
        return Matrix2x2<T>(cosf(angle), -sinf(angle), sinf(angle), cosf(angle));
    }

    NV_HOSTDEVICE void create(T angle)
    {
        e00 = cosf(angle);
        e01 = -sinf(angle);
        e10 = sinf(angle);
        e11 = cosf(angle);
    }

    NV_HOSTDEVICE void negateAngle()
    {
        e01 = -e01;
        e10 = -e10;
    }

    NV_HOSTDEVICE Matrix2x2<T> operator*(const Matrix2x2<T>& other) const
    {
        return Matrix2x2(e00 * other.e00 + e01 * other.e10, e10 * other.e00 + e11 * other.e10,
                         e00 * other.e01 + e01 * other.e11, e10 * other.e01 + e11 * other.e11);
    }

    template <typename U>
    NV_HOSTDEVICE Matrix2x2<T> operator*(const Matrix2x2<U>& other) const
    {
        return Matrix2x2(e00 * other.e00 + e01 * other.e10, e10 * other.e00 + e11 * other.e10,
                         e00 * other.e01 + e01 * other.e11, e10 * other.e01 + e11 * other.e11);
    }

    NV_HOSTDEVICE Vector2<T> operator*(const Vector2<T>& vector) const
    {
        return Vector2<T>(e00 * vector.e0 + e01 * vector.e1, e10 * vector.e0 + e11 * vector.e1);
    }

    template <typename U>
    NV_HOSTDEVICE Vector2<U> operator*(const Vector2<U>& vector) const
    {
        return Vector2<U>(e00 * vector.e0 + e01 * vector.e1, e10 * vector.e0 + e11 * vector.e1);
    }
};

template <>
struct Matrix2x2<cuFloatComplex>
{
    cuFloatComplex e00, e01, e10, e11;

    NV_HOSTDEVICE Matrix2x2<cuFloatComplex>(){};
    NV_HOSTDEVICE Matrix2x2<cuFloatComplex>(cuFloatComplex e00, cuFloatComplex e01, cuFloatComplex e10, cuFloatComplex e11)
        : e00(e00), e01(e01), e10(e10), e11(e11){};

    // Create a rotation matrix with the given angle (in radians).
    // TODO: restrict the angle and also the outputted matrix to real floats.
    // Need to write real matrix * complex matrix, and real matrix * complex vector for that.
    NV_HOSTDEVICE static Matrix2x2<cuFloatComplex> createRotationMatrix(const float angle)
    {
        return Matrix2x2<cuFloatComplex>(make_cuFloatComplex(cosf(angle), 0.f), make_cuFloatComplex(-sinf(angle), 0.f),
                                         make_cuFloatComplex(sinf(angle), 0.f), make_cuFloatComplex(cosf(angle), 0.f));
    }

    NV_HOSTDEVICE void create(float angle)
    {
        e00 = make_cuFloatComplex(cosf(angle), 0.f);
        e01 = make_cuFloatComplex(-sinf(angle), 0.f);
        e10 = make_cuFloatComplex(sinf(angle), 0.f);
        e11 = make_cuFloatComplex(cosf(angle), 0.f);
    }

    NV_HOSTDEVICE void negateAngle()
    {
        e01.x = -e01.x;
        e10.x = -e10.x;
    }

    NV_HOSTDEVICE Matrix2x2<cuFloatComplex> operator*(const Matrix2x2<cuFloatComplex>& other) const
    {
        return Matrix2x2<cuFloatComplex>(cuCaddf(cuCmulf(e00, other.e00), cuCmulf(e01, other.e10)),
                                         cuCaddf(cuCmulf(e10, other.e00), cuCmulf(e11, other.e10)),
                                         cuCaddf(cuCmulf(e00, other.e01), cuCmulf(e01, other.e11)),
                                         cuCaddf(cuCmulf(e10, other.e01), cuCmulf(e11, other.e11)));
    }

    template <typename U>
    NV_HOSTDEVICE Matrix2x2<cuFloatComplex> operator*(const Matrix2x2<U>& other) const
    {
        return Matrix2x2(e00 * other.e00 + e01 * other.e10, e10 * other.e00 + e11 * other.e10,
                         e00 * other.e01 + e01 * other.e11, e10 * other.e01 + e11 * other.e11);
    }

    NV_HOSTDEVICE Vector2<cuFloatComplex> operator*(const Vector2<cuFloatComplex>& vector) const
    {
        return Vector2<cuFloatComplex>(cuCaddf(cuCmulf(e00, vector.e0), cuCmulf(e01, vector.e1)),
                                       cuCaddf(cuCmulf(e10, vector.e0), cuCmulf(e11, vector.e1)));
    }

    template <typename U>
    NV_HOSTDEVICE Vector2<cuFloatComplex> operator*(const Vector2<U>& vector) const
    {
        return Vector2<cuFloatComplex>(e00 * vector.e0 + e01 * vector.e1, e10 * vector.e0 + e11 * vector.e1);
    }
};

using Vector2f = Vector2<float>;
using Matrix2x2f = Matrix2x2<float>;
using Vector2c = Vector2<cuFloatComplex>;
using Matrix2x2c = Matrix2x2<cuFloatComplex>;
