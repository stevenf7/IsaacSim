// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#pragma once

// Inline CPU gather/scatter functions for Newton tensor views.
// All functions accept size_t counts and use sentinel index -1 to write zeros.
// No heap allocation; designed for direct use in CPU view getter/setter methods.

#include "utils/WarpCompat.h"

#include <cstddef>
#include <cstring>

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

inline void gatherFloat(const float* src, float* dst, const int* indices, size_t n)
{
    for (size_t i = 0; i < n; ++i)
        dst[i] = (indices[i] >= 0) ? src[indices[i]] : 0.0f;
}

inline void gatherTransform(const wp::transform* src, float* dst, const int* indices, size_t n)
{
    for (size_t i = 0; i < n; ++i)
    {
        float* d = dst + i * 7;
        if (indices[i] >= 0)
        {
            const wp::transform& t = src[indices[i]];
            d[0] = t.p[0];
            d[1] = t.p[1];
            d[2] = t.p[2];
            d[3] = t.q[0];
            d[4] = t.q[1];
            d[5] = t.q[2];
            d[6] = t.q[3];
        }
        else
        {
            std::memset(d, 0, 7 * sizeof(float));
        }
    }
}

inline void gatherSpatialVector(const wp::spatial_vector* src, float* dst, const int* indices, size_t n)
{
    for (size_t i = 0; i < n; ++i)
    {
        float* d = dst + i * 6;
        if (indices[i] >= 0)
        {
            const wp::spatial_vector& sv = src[indices[i]];
            d[0] = sv.w[0];
            d[1] = sv.w[1];
            d[2] = sv.w[2];
            d[3] = sv.v[0];
            d[4] = sv.v[1];
            d[5] = sv.v[2];
        }
        else
        {
            std::memset(d, 0, 6 * sizeof(float));
        }
    }
}

inline void gatherMat33(const wp::mat33* src, float* dst, const int* indices, size_t n)
{
    for (size_t i = 0; i < n; ++i)
    {
        float* d = dst + i * 9;
        if (indices[i] >= 0)
        {
            const wp::mat33& m = src[indices[i]];
            for (int r = 0; r < 3; ++r)
                for (int c = 0; c < 3; ++c)
                    d[r * 3 + c] = m.data[r][c];
        }
        else
        {
            std::memset(d, 0, 9 * sizeof(float));
        }
    }
}

inline void gatherPairedFloat(const float* srcA, const float* srcB, float* dst, const int* indices, size_t n)
{
    for (size_t i = 0; i < n; ++i)
    {
        int idx = indices[i];
        size_t off = i * 2;
        if (idx >= 0)
        {
            dst[off] = srcA[idx];
            dst[off + 1] = srcB[idx];
        }
        else
        {
            dst[off] = dst[off + 1] = 0.0f;
        }
    }
}

inline void gatherCenterOfMass(const wp::vec3* src, float* dst, const int* indices, size_t n)
{
    for (size_t i = 0; i < n; ++i)
    {
        float* out = dst + i * 7;
        if (indices[i] >= 0)
        {
            const wp::vec3& v = src[indices[i]];
            out[0] = v[0];
            out[1] = v[1];
            out[2] = v[2];
        }
        else
        {
            out[0] = out[1] = out[2] = 0.0f;
        }
        out[3] = out[4] = out[5] = 0.0f;
        out[6] = 1.0f;
    }
}

inline void indirectScatterFloat(const float* src, float* dst, const int* srcOffsets, const int* dstIndices, size_t n)
{
    for (size_t i = 0; i < n; ++i)
        dst[dstIndices[i]] = src[srcOffsets[i]];
}

inline void indirectAddFloat(const float* src, float* dst, const int* srcOffsets, const int* dstIndices, size_t n)
{
    for (size_t i = 0; i < n; ++i)
        dst[dstIndices[i]] += src[srcOffsets[i]];
}

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
