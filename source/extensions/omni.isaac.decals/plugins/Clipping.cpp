// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "ConvexPolygonIntersect.h"

#include <carb/Framework.h>
#include <carb/logging/Log.h>


using namespace carb;

namespace omni
{
namespace isaac
{
namespace decals
{

template <typename T>
inline int minIndex(T a0, T a1, T a2)
{
    return a0 >= a1 ? (a0 >= a2 ? 0 : 2) : (a1 >= a2 ? 1 : 2);
}

inline int nextMod3(int i)
{
    return (1 << i) & 3;
}

inline int prevMod3(int i)
{
    return (3 >> i) ^ 1;
}

template <typename V>
struct BoundsF
{
    BoundsF()
    {
    }
    BoundsF(bool init) : min(init ? -FLT_MAX : FLT_MAX), max(-min)
    {
    }

    void include(const V& point)
    {
        for (size_t i = 0; i < V::dimension; ++i)
        {
            min[i] = std::min(min[i], point[i]);
            max[i] = std::max(max[i], point[i]);
        }
    }

    V min, max;
};

class Int2Proj
{
public:
    Int2Proj(const pxr::GfVec4f& plane) : m_axes({ 0, 1, 2 }), m_bounds(false)
    {
        m_axes.z = minIndex(plane[0] * plane[0], plane[1] * plane[1], plane[2] * plane[2]);
        m_axes.x = nextMod3(m_axes.z);
        m_axes.y = prevMod3(m_axes.z);
        m_pPlane.x = plane[m_axes.x];
        m_pPlane.y = plane[m_axes.y];
        m_pPlane.z = plane[m_axes.z];
        m_pPlane.w = plane[3];
    }

    void bound(const pxr::GfVec3f* verts, const int* indices, size_t count)
    {
        for (size_t i = 0; i < count; ++i)
        {
            const pxr::GfVec3f& v = verts[indices[i]];
            m_bounds.include(pxr::GfVec2f(v[m_axes.x], v[m_axes.y]));
        }

        m_log2Scale = { FLT_MANT_DIG - 1 - ilogb(m_bounds.max[0] - m_bounds.min[0]),
                        FLT_MANT_DIG - 1 - ilogb(m_bounds.max[1] - m_bounds.min[1]) };
    }

    IVec2 project(const pxr::GfVec3f& vert) const
    {
        const pxr::GfVec2f rel = pxr::GfVec2f(vert[m_axes.x], vert[m_axes.y]) - m_bounds.min;
        return IVec2({ (int32_t)std::scalbn(rel[0], m_log2Scale.x), (int32_t)std::scalbn(rel[1], m_log2Scale.y) });
    }

    pxr::GfVec3f extrude(const IVec2& vert) const
    {
        const pxr::GfVec2f proj =
            pxr::GfVec2f(std::scalbn((float)vert.x, -m_log2Scale.x), std::scalbn((float)vert.y, -m_log2Scale.y)) +
            m_bounds.min;
        pxr::GfVec3f result;
        result[m_axes.x] = proj[0];
        result[m_axes.y] = proj[1];
        result[m_axes.z] = -(proj[0] * m_pPlane.x + proj[1] * m_pPlane.y + m_pPlane.w) / m_pPlane.z;
        return result;
    }

private:
    Int3 m_axes;
    Float4 m_pPlane;
    BoundsF<pxr::GfVec2f> m_bounds;
    IVec2 m_log2Scale;
};

size_t intersectProjectedPolygons(pxr::GfVec3f* resultBuffer,
                                  size_t resultBufferSize,
                                  const pxr::GfVec4f& plane, // x * plane[0] + y * plane[1] + z * plane[2] + plane[3] =
                                                             // 0
                                  const pxr::GfVec3f* vertexBuffer1,
                                  const int* indexBuffer1,
                                  size_t vertexCount1,
                                  const pxr::GfVec3f* vertexBuffer2,
                                  const int* indexBuffer2,
                                  size_t vertexCount2)
{
    // Stack allocation
    void* stack = alloca(2 * (vertexCount1 + vertexCount2) * sizeof(Int2));

    // Integer representation of vertex buffers
    IVec2* v1 = reinterpret_cast<IVec2*>(stack);
    IVec2* v2 = v1 + vertexCount1;
    IVec2* vI = v2 + vertexCount2;

    // Create projector
    Int2Proj proj(plane);
    proj.bound(vertexBuffer1, indexBuffer1, vertexCount1);
    proj.bound(vertexBuffer2, indexBuffer2, vertexCount2);

    // Convert to integers
    for (size_t i = 0; i < vertexCount1; ++i)
        v1[i] = proj.project(vertexBuffer1[indexBuffer1[i]]);

    for (size_t i = 0; i < vertexCount2; ++i)
        v2[i] = proj.project(vertexBuffer2[indexBuffer2[i]]);

    // Intersect
    size_t vertexCountI = intersectIntPolygons(vI, v1, vertexCount1, v2, vertexCount2);
    if (vertexCountI > resultBufferSize)
        vertexCountI = resultBufferSize;

    // Extrude back to plane
    for (size_t i = 0; i < vertexCountI; ++i)
        *resultBuffer++ = proj.extrude(*vI++);

    return vertexCountI;
}

#define CLIP_TEST(_cond, ...)                                                                                          \
    if (!(_cond))                                                                                                      \
    CARB_LOG_ERROR(__VA_ARGS__)

static void testRoundTrip(const pxr::GfVec3f* vb, const int* ib, size_t count, const Int2Proj& proj)
{
    for (size_t i = 0; i < count; ++i)
    {
        const pxr::GfVec3f v = vb[ib[i]];
        const pxr::GfVec3f error = proj.extrude(proj.project(v)) - v;
        const float relErrorMagnitude = sqrt(error.GetLengthSq() / v.GetLengthSq());
        CLIP_TEST(relErrorMagnitude <= 0.0f, "Large error in extruded projected vector: %g", relErrorMagnitude);
    }
}

static void testIntersection(const pxr::GfVec3f* vb1,
                             const int* ib1,
                             size_t count1,
                             const pxr::GfVec3f* vb2,
                             const int* ib2,
                             size_t count2,
                             const pxr::GfVec4f& plane,
                             const pxr::GfVec3f* expected,
                             size_t expectedCount)
{
    using pxr::GfVec3f;

    const size_t bufferSize = count1 + count2;
    GfVec3f* buffer = (GfVec3f*)alloca(bufferSize * sizeof(GfVec3f));

    const size_t count = intersectProjectedPolygons(buffer, bufferSize, plane, vb1, ib1, count1, vb2, ib2, count2);

    CLIP_TEST(count == expectedCount, "Intersection polygon has size %d, should be %d.", (int)count, (int)expectedCount);

    for (size_t i = 0; i < std::min(count, expectedCount); ++i)
    {
        const pxr::GfVec3f error = buffer[i] - expected[i];
        const float relErrorMagnitude = sqrt(error.GetLengthSq() / expected[i].GetLengthSq());
        CLIP_TEST(relErrorMagnitude <= FLT_EPSILON, "Large error in clipped vertex %d (%g, %g, %g): %g", (int)i,
                  buffer[i][0], buffer[i][1], buffer[i][2], relErrorMagnitude);
    }
}

static void scaleAboutCenter(pxr::GfVec3f* v, size_t count, float scale)
{
    BoundsF<pxr::GfVec3f> bounds(false);
    for (size_t i = 0; i < count; ++i)
        bounds.include(v[i]);

    const pxr::GfVec3f center = 0.5f * (bounds.max - bounds.min);
    for (size_t i = 0; i < count; ++i)
        v[i] = (v[i] - center) * scale + center;
}

void testClipping()
{
    using pxr::GfVec3f;

    // Polygons
    const GfVec3f v1[] = {
        { 16.0f, -3.0f, 0.0f }, { 28.0f, 16.0f, 0.0f }, { 16.0f, 32.0f, 0.0f }, { 0.0f, 22.0f, 0.0f }, { 3.0f, 10.0f, 0.0f }
    };
    const int i1[] = { 0, 1, 2, 3, 4 };
    constexpr size_t count1 = sizeof(v1) / sizeof(v1[0]);

    const GfVec3f v2[] = { { 0.0f, 16.0f, 0.0f },  { 5.0f, 8.0f, 0.0f },   { 13.0f, 0.0f, 0.0f },
                           { 19.0f, 2.0f, 0.0f },  { 24.0f, 10.0f, 0.0f }, { 24.0f, 26.0f, 0.0f },
                           { 19.0f, 29.0f, 0.0f }, { 13.0f, 32.0f, 0.0f }, { 7.0f, 32.0f, 0.0f },
                           { 3.0f, 29.0f, 0.0f } };
    const int i2[] = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 };
    constexpr size_t count2 = sizeof(v2) / sizeof(v2[0]);

    const pxr::GfVec4f zPlane(0.0f, 0.0f, 1.0f, 0.0f);

    // Test projection
    Int2Proj proj(zPlane);
    proj.bound(v1, i1, count1);
    proj.bound(v2, i2, count2);
    testRoundTrip(v1, i1, count1, proj);
    testRoundTrip(v2, i2, count2, proj);

    // Test intersection function
    const GfVec3f v1v2[] = { { 5.0f, 8.0f, 0.0f },
                             { 13.0f, 0.0f, 0.0f },
                             { 19.0f, 2.0f, 0.0f },
                             { 24.0f, 10.0f, 0.0f },
                             { 24.0f, 64.0f / 3, 0.0f },
                             { 17.8f, 29.6f, 0.0f },
                             { 44.0f / 3, 187.0f / 6, 0.0f },
                             { 144.0f / 89, 2048.0f / 89, 0.0f },
                             { 18.0f / 25, 478.0f / 25, 0.0f },
                             { 5.0f / 2, 12.0f, 0.0f } };
    const size_t v1v2Count = sizeof(v1v2) / sizeof(v1v2[0]);
    testIntersection(v1, i1, count1, v2, i2, count2, zPlane, v1v2, v1v2Count);

    // Test self-intersection
    testIntersection(v1, i1, count1, v1, i1, count1, zPlane, v1, count1);
    testIntersection(v2, i2, count2, v2, i2, count2, zPlane, v2, count2);

    // Test proper subsets
    GfVec3f v1Small[count1];
    memcpy(v1Small, v1, sizeof(v1));
    scaleAboutCenter(v1Small, count1, 0.5f);
    testIntersection(v1Small, i1, count1, v2, i2, count2, zPlane, v1Small, count1);

    GfVec3f v2Small[count2];
    memcpy(v2Small, v2, sizeof(v2));
    scaleAboutCenter(v2Small, count2, 0.5f);
    testIntersection(v1, i1, count1, v2Small, i2, count2, zPlane, v2Small, count2);

    // Test empty intersection
    GfVec3f v2Shift[count2];
    for (size_t i = 0; i < count2; ++i)
        v2Shift[i] = v2[i] + GfVec3f(26.0f, -9.0f, 0.0f);
    testIntersection(v1, i1, count1, v2Shift, i2, count2, zPlane, nullptr, 0);
}

} // namespace omni
} // namespace isaac
} // namespace decals
