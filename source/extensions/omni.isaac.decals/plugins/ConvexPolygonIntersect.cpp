// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "ConvexPolygonIntersect.h"

#include <cstring>

namespace omni
{
static inline IVec2 operator-(const IVec2& a, const IVec2& b)
{
    return { a.x - b.x, a.y - b.y };
}

static inline int64_t operator^(const IVec2& a, const IVec2& b)
{
    return (int64_t)a.x * (int64_t)b.y - (int64_t)a.y * (int64_t)b.x;
}

static inline bool left(const IVec2& a, const IVec2& b, const IVec2& c)
{
    return ((b - a) ^ (c - a)) > 0;
}

static inline bool intersectIntEdges(IVec2*& result,
                                     const IVec2& b1, // Origin of edge 1
                                     const IVec2& e1, // Displacement of edge 1
                                     const IVec2& b2, // Origin of edge 2
                                     const IVec2& e2 // Displacement of edge 2
)
{
    int64_t det = e1 ^ e2;
    if (det == 0)
        return false;

    IVec2 delta; // Displacement between edge origins
    if (det > 0)
        delta = b2 - b1;
    else
    {
        delta = b1 - b2;
        det = -det;
    }

    const int64_t num1 = delta ^ e2;
    if (num1 < 0 || num1 > det)
        return false;

    const int64_t num2 = delta ^ e1;
    if (num2 < 0 || num2 > det)
        return false;

    const double t = (double)num1 / (double)det;
    *result++ = IVec2({ (int32_t)(b1.x + e1.x * t), (int32_t)(b1.y + e1.y * t) });

    return true;
}

static inline void advance(IVec2*& result, bool inside, const IVec2& vert, size_t& index, size_t& advCount, size_t vertCount)
{
    if (inside)
        *result++ = vert;
    index = (index + 1) % vertCount;
    ++advCount;
}

size_t intersectIntPolygons(IVec2* result, const IVec2* verts1, size_t count1, const IVec2* verts2, size_t count2)
{
    IVec2* curr = result;

    int inFlag = 0; // 0 == unknown, 1 == V1 in, 2 == V2 in

    size_t i1 = 0;
    size_t i2 = 0;

    size_t adv1 = 0;
    size_t adv2 = 0;

    bool p2InP1 = true;
    bool p1InP2 = true;

    do
    {
        const size_t i1Prev = (i1 + count1 - 1) % count1;
        const size_t i2Prev = (i2 + count2 - 1) % count2;
        const IVec2& v1 = verts1[i1];
        const IVec2& v2 = verts2[i2];
        const IVec2& v1Prev = verts1[i1Prev];
        const IVec2& v2Prev = verts2[i2Prev];

        const IVec2 e1 = v1 - v1Prev;
        const IVec2 e2 = v2 - v2Prev;
        const int64_t wedge = e1 ^ e2;
        const bool i2InH1 = left(v1Prev, v1, v2);
        const bool i1InH2 = left(v2Prev, v2, v1);

        p2InP1 &= i2InH1;
        p1InP2 &= i1InH2;

        if (intersectIntEdges(curr, v1Prev, e1, v2Prev, e2))
        {
            if (!inFlag)
                adv1 = adv2 = 0;
            if (i1InH2)
                inFlag = 1;
            else if (i2InH1)
                inFlag = 2;
        }

        if (wedge == 0 && !i1InH2 && !i2InH1)
        {
            if (inFlag == 1)
                advance(curr, false, v2, i2, adv2, count2);
            else
                advance(curr, false, v1, i1, adv1, count1);
        }
        else if (wedge >= 0)
        {
            if (i2InH1)
                advance(curr, inFlag == 1, v1, i1, adv1, count1);
            else
                advance(curr, inFlag == 2, v2, i2, adv2, count2);
        }
        else
        {
            if (i1InH2)
                advance(curr, inFlag == 2, v2, i2, adv2, count2);
            else
                advance(curr, inFlag == 1, v1, i1, adv1, count1);
        }
    } while (adv1 + adv2 < count1 + count2 && adv1 < 2 * count1 && adv2 < 2 * count2);

    if (!inFlag)
    {
        if (p1InP2)
        {
            memcpy(curr, verts1, count1 * sizeof(IVec2));
            curr += count1;
        }
        else if (p2InP1)
        {
            memcpy(curr, verts2, count2 * sizeof(IVec2));
            curr += count2;
        }
    }

    return curr - result;
}

} // namespace omni
