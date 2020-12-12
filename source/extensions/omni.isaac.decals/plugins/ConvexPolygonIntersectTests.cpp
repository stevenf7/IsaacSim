// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "ConvexPolygonIntersect.h"

#include <algorithm>
#include <cstring>
#include <float.h>
#include <random>
#include <stdio.h>

#if !defined(alloca)
#    if defined(__GLIBC__) || defined(__sun) || defined(__CYGWIN__) || defined(__APPLE__) || defined(__SWITCH__)
#        include <alloca.h> // alloca (glibc uses <alloca.h>. Note that Cygwin may have _WIN32 defined, so the order matters here)
#    elif defined(_WIN32)
#        include <malloc.h> // alloca
#        if !defined(alloca)
#            define alloca _alloca // for clang with MS Codegen
#        endif
#    else
#        include <stdlib.h> // alloca
#    endif
#endif

#ifdef _MSC_VER
#    pragma warning(disable : 4996)
#endif

namespace omni
{
struct IFrac
{
    IFrac()
    {
    }
    IFrac(int32_t num, int32_t den) : num(num), den(den)
    {
    }

    int32_t num, den;
};

static inline int64_t operator*(int32_t a, const IFrac& b)
{
    return ((int64_t)a * (int64_t)b.num) / (int64_t)b.den;
}

static inline int64_t operator*(const IFrac& a, int32_t b)
{
    return b * a;
}

static inline IVec2 operator*(const IVec2& a, const IFrac& b)
{
    return { (int32_t)(a.x * b), (int32_t)(a.y * b) };
}

static inline IVec2 operator*(const IFrac& a, const IVec2& b)
{
    return b * a;
}

static inline IVec2 operator/(const IVec2& a, int32_t b)
{
    return { a.x / b, a.y / b };
}

static inline IVec2 operator+(const IVec2& a, const IVec2& b)
{
    return { a.x + b.x, a.y + b.y };
}

static inline IVec2 operator-(const IVec2& a, const IVec2& b)
{
    return { a.x - b.x, a.y - b.y };
}

static inline int64_t operator|(const IVec2& a, const IVec2& b)
{
    return (int64_t)a.x * (int64_t)b.x + (int64_t)a.y * (int64_t)b.y;
}

static inline int64_t operator^(const IVec2& a, const IVec2& b)
{
    return (int64_t)a.x * (int64_t)b.y - (int64_t)a.y * (int64_t)b.x;
}

static inline bool left(const IVec2& a, const IVec2& b, const IVec2& c)
{
    return ((b - a) ^ (c - a)) > 0;
}

static int sPass = 0;
static int sFail = 0;

static int sIntersecting = 0;
static int sDisjoint = 0;

#define TEST_LOG(_cond, ...)                                                                                           \
    if (!(_cond))                                                                                                      \
    std::printf(__VA_ARGS__)

static void testIntersection(
    const IVec2* v1, size_t count1, const IVec2* v2, size_t count2, const IVec2* expected, size_t expectedCount)
{
    const size_t bufferSize = count1 + count2;
    IVec2* buffer = (IVec2*)alloca(bufferSize * sizeof(IVec2));

    const size_t count = intersectIntPolygons(buffer, v1, count1, v2, count2);

    const bool vertCountsEqual = count == expectedCount;
    TEST_LOG(vertCountsEqual, "Intersection polygon has size %d, should be %d.\n", (int)count, (int)expectedCount);

    bool pass = vertCountsEqual;
    for (size_t i = 0; i < std::min(count, expectedCount); ++i)
    {
        const bool vertsEqual = buffer[i].x == expected[i].x && buffer[i].y == expected[i].y;
        TEST_LOG(vertsEqual, "Error in clipped vertex %d (%d, %d).\n", (int)i, buffer[i].x, buffer[i].y);
        pass &= vertsEqual;
    }

    sPass += (int)pass;
    sFail += (int)!pass;
}

inline bool rayIntersect(double& tEx,
                         double& tIn,
                         bool& rayCoincidentWithSurface,
                         const IVec2& b1, // Origin of ray
                         const IVec2& e1, // Direction of ray
                         const IVec2& b2, // Point on line
                         const IVec2& e2 // Vector parallel with line
)
{
    rayCoincidentWithSurface = false;

    const int64_t num = (b2 - b1) ^ e2;
    const int64_t den = e1 ^ e2;

    constexpr int64_t eps = 8 << 24;
    if (std::abs(den) < eps)
    {
        if (num < -eps)
            return false;
        if (num <= eps)
            rayCoincidentWithSurface = true;
        return true;
    }

    const double t = (double)num / (double)den;
    if (den > 0)
    {
        if (t < tEx)
            tEx = t;
    }
    else
    {
        if (t > tIn)
            tIn = t;
    }

    return tIn < tEx;
}

static bool testIntersectionShape(IVec2* buffer, size_t& count, const IVec2* v1, size_t count1, const IVec2* v2, size_t count2)
{
    count = intersectIntPolygons(buffer, v1, count1, v2, count2);
    sIntersecting += (int)(count > 0);
    sDisjoint += (int)(count == 0);

    // Separation test
    bool separate = false;
    for (size_t i = 0; !separate && i < count2; ++i)
    {
        const IVec2 v2i = v2[i];
        const IVec2 v2i1 = v2[(i + 1) % count2];
        bool p2Separation = true;
        for (size_t j = 0; p2Separation && j < count1; ++j)
            p2Separation &= !left(v2i, v2i1, v1[j]);
        separate = p2Separation;
    }
    for (size_t i = 0; !separate && i < count1; ++i)
    {
        const IVec2 v1i = v1[i];
        const IVec2 v1i1 = v1[(i + 1) % count1];
        bool p1Separation = true;
        for (size_t j = 0; p1Separation && j < count2; ++j)
            p1Separation &= !left(v1i, v1i1, v2[j]);
        separate = p1Separation;
    }

    const bool separationMatches = separate == (count == 0);
    TEST_LOG(separationMatches, "Separation test gives %s intersection, but intersection has %d vertices.\n",
             separate ? "no" : "", (int)count);

    bool pass = separationMatches;

    // Test shape
    bool edgesMatch = true;
    bool allCoincidencesFound = true;
    for (size_t i = 0; i < count; ++i)
    {
        const IVec2& vi = buffer[i];
        const IVec2 ei = buffer[(i + 1) % count] - vi;

        double tEx = DBL_MAX;
        double tIn = -DBL_MAX;
        bool intersection = true;
        bool coincidenceFound = false;
        for (size_t j = 0; intersection && j < count1; ++j)
        {
            const IVec2& v1j = v1[j];
            const IVec2 e1j = v1[(j + 1) % count1] - v1j;
            bool rayCoincidentWithSurface;
            intersection &= rayIntersect(tEx, tIn, rayCoincidentWithSurface, vi, ei, v1j, e1j);
            coincidenceFound |= rayCoincidentWithSurface;
            if (!intersection)
                printf("Intersection edge %d is outside of polygon 1.\n", (int)i);
        }
        for (size_t j = 0; intersection && j < count2; ++j)
        {
            const IVec2& v2j = v2[j];
            const IVec2 e2j = v2[(j + 1) % count2] - v2j;
            bool rayCoincidentWithSurface;
            intersection &= rayIntersect(tEx, tIn, rayCoincidentWithSurface, vi, ei, v2j, e2j);
            coincidenceFound |= rayCoincidentWithSurface;
            if (!intersection)
                printf("Intersection edge %d is outside of polygon 2.\n", (int)i);
        }

        allCoincidencesFound &= coincidenceFound;
        if (!coincidenceFound)
            printf("Intersection edge %d not coincident with either polygon edge.\n", (int)i);

        if (intersection)
        {
            constexpr double eps = 16;
            const bool edgeMatches = std::abs(tIn * ei.x) < eps && std::abs(tIn * ei.y) < eps &&
                                     std::abs((tEx - 1.0) * ei.x) < eps && std::abs((tEx - 1.0) * ei.y) < eps;
            if (!edgeMatches)
            {
                printf("Intersection edge %d error: tIn = %g, tEx = %g.\n", (int)i, tIn, tEx);
                printf("  ei = (%d, %d).\n", ei.x, ei.y);
                printf(
                    "  in = (%g, %g) ex = (%g, %g).\n", tIn * ei.x, tIn * ei.y, (tEx - 1.0) * ei.x, (tEx - 1.0) * ei.y);
            }
            edgesMatch &= edgeMatches;
        }
    }

    pass &= edgesMatch & allCoincidencesFound;

    sPass += (int)pass;
    sFail += (int)!pass;

    return pass;
}

class HPIntRep
{
public:
    HPIntRep(int xDigits, int yDigits) : xDigits(xDigits), yDigits(yDigits)
    {
    }

    IVec2 operator()(int32_t x, int32_t y)
    {
        return IVec2({ x << xDigits, y << yDigits });
    }

    IVec2 operator()(const IFrac& x, const IFrac& y)
    {
        return IVec2({ (int32_t)(((int64_t)x.num << xDigits) / (int64_t)x.den),
                       (int32_t)(((int64_t)y.num << yDigits) / (int64_t)y.den) });
    }

    void frac(int32_t& xi, IFrac& xf, int32_t& yi, IFrac& yf, const IVec2& v)
    {
        xi = v.x >> xDigits;
        xf = { v.x & ((1 << xDigits) - 1), 1 << xDigits };
        yi = v.y >> yDigits;
        yf = { v.y & ((1 << yDigits) - 1), 1 << yDigits };
    }

private:
    int xDigits, yDigits;
};

struct Bounds2I
{
    Bounds2I()
    {
    }
    Bounds2I(bool init)
    {
        if (!init)
            min = { INT32_MAX, INT32_MAX };
        else
            min = { -INT32_MAX, -INT32_MAX };
        max = { -min.x, -min.y };
    }

    void include(const IVec2& point)
    {
        min.x = std::min(min.x, point.x);
        min.y = std::min(min.y, point.y);
        max.x = std::max(max.x, point.x);
        max.y = std::max(max.y, point.y);
    }

    IVec2 min, max;
};

// RNG which should be consistent across platforms
class Random
{
public:
    Random() : m_rng(m_dev()), m_dist(0, m_max)
    {
        m_rng.seed();
    }

    int val()
    {
        return m_dist(m_rng);
    }

    int max()
    {
        return m_max;
    }

private:
    static constexpr int m_max = 0x7fff;

    std::random_device m_dev;
    std::mt19937 m_rng;
    std::uniform_int_distribution<std::mt19937::result_type> m_dist;
};

static void transformAboutCenter(IVec2* v, size_t count, const IFrac& scale, float angle, const IVec2& offset)
{
    Bounds2I bounds(false);
    for (size_t i = 0; i < count; ++i)
        bounds.include(v[i]);

    const IVec2 center = (bounds.max - bounds.min) / 2;
    for (size_t i = 0; i < count; ++i)
    {
        IVec2 r = v[i] - center; // Relative to center
        r = r * scale; // apply scale
        const IFrac c((int32_t)scalbn(cos(angle) + 1.0f, 24) - (1 << 24), 1 << 24);
        const IFrac s((int32_t)scalbn(sin(angle) + 1.0f, 24) - (1 << 24), 1 << 24);
        r = IVec2({ (int32_t)(r.x * c - r.y * s), (int32_t)(r.x * s + r.y * c) }); // apply rotation
        r = r + offset; // apply offset
        v[i] = r + center; // Back to original frame
    }
}

int runConvexPolygonIntersectTests()
{
    int result = 0;

    sPass = sFail = 0;
    sIntersecting = sDisjoint = 0;
    printf("Running convex polygon intersection tests...\n");

    HPIntRep iRep(19, 18);

    // Polygons
    const IVec2 v1[] = { iRep(16, -3), iRep(28, 16), iRep(16, 32), iRep(0, 22), iRep(3, 10) };
    constexpr size_t count1 = sizeof(v1) / sizeof(v1[0]);

    const IVec2 v2[] = { iRep(0, 16),  iRep(5, 8),   iRep(13, 0),  iRep(19, 2), iRep(24, 10),
                         iRep(24, 26), iRep(19, 29), iRep(13, 32), iRep(7, 32), iRep(3, 29) };
    constexpr size_t count2 = sizeof(v2) / sizeof(v2[0]);

    // Test intersection function
    const IVec2 v1v2[] = { iRep({ 5, 1 }, { 8, 1 }),    iRep({ 13, 1 }, { 0, 1 }),       iRep({ 19, 1 }, { 2, 1 }),
                           iRep({ 24, 1 }, { 10, 1 }),  iRep({ 24, 1 }, { 64, 3 }),      iRep({ 89, 5 }, { 148, 5 }),
                           iRep({ 44, 3 }, { 187, 6 }), iRep({ 144, 89 }, { 2048, 89 }), iRep({ 18, 25 }, { 478, 25 }),
                           iRep({ 5, 2 }, { 12, 1 }) };
    const size_t v1v2Count = sizeof(v1v2) / sizeof(v1v2[0]);
    testIntersection(v1, count1, v2, count2, v1v2, v1v2Count);

    // Test self-intersection
    testIntersection(v1, count1, v1, count1, v1, count1);
    testIntersection(v2, count2, v2, count2, v2, count2);

    // Test proper subsets
    IVec2 v1Prime[count1];
    memcpy(v1Prime, v1, sizeof(v1));
    transformAboutCenter(v1Prime, count1, IFrac(1, 2), 0.0f, { 0, 0 });
    testIntersection(v1Prime, count1, v2, count2, v1Prime, count1);

    IVec2 v2Prime[count2];
    memcpy(v2Prime, v2, sizeof(v2));
    transformAboutCenter(v2Prime, count2, IFrac(1, 2), 0.0f, { 0, 0 });
    testIntersection(v1, count1, v2Prime, count2, v2Prime, count2);

    // Test empty intersection
    for (size_t i = 0; i < count2; ++i)
        v2Prime[i] = v2[i] + iRep(26, -9);
    testIntersection(v1, count1, v2Prime, count2, nullptr, 0);

    printf("Basic tests: %d passed, %d failed.\n", sPass, sFail);
    result += sFail;

    // Randomized testing
    sPass = sFail = 0;
    Random rnd;
    constexpr int kTestCount = 1000;
    IVec2 buffer[count1 + count2];
    for (int i = 0; i < kTestCount; ++i)
    {
        // scale from 1/10 to 10
        const IFrac scale1((int32_t)scalbn(pow(10.0f, 2 * (float)rnd.val() / rnd.max() - 1.0f), 24), 1 << 24);
        const IFrac scale2((int32_t)scalbn(pow(10.0f, 2 * (float)rnd.val() / rnd.max() - 1.0f), 24), 1 << 24);
        // angle on circle
        const float angle1 = 3.1415927f * 2 * (float)rnd.val() / rnd.max() - 1.0f;
        const float angle2 = 3.1415927f * 2 * (float)rnd.val() / rnd.max() - 1.0f;
        // translate from -32 to 32 in x and y
        const IVec2 offset1 = iRep(IFrac((int32_t)scalbn((float)rnd.val() / rnd.max(), 30) - (1 << 29), 1 << 24),
                                   IFrac((int32_t)scalbn((float)rnd.val() / rnd.max(), 30) - (1 << 29), 1 << 24));
        const IVec2 offset2 = iRep(IFrac((int32_t)scalbn((float)rnd.val() / rnd.max(), 30) - (1 << 29), 1 << 24),
                                   IFrac((int32_t)scalbn((float)rnd.val() / rnd.max(), 30) - (1 << 29), 1 << 24));

        memcpy(v1Prime, v1, sizeof(v1));
        transformAboutCenter(v1Prime, count1, scale1, angle1, offset1);
        memcpy(v2Prime, v2, sizeof(v2));
        transformAboutCenter(v2Prime, count2, scale2, angle2, offset2);

        size_t count;
        if (!testIntersectionShape(buffer, count, v1Prime, count1, v2Prime, count2) && count > 0)
        {
            char fname[100];
            sprintf(fname, "int_test_fail_%03d", i);
            FILE* f = fopen(fname, "w");
            if (f)
            {
                for (size_t k = 0; k < count1 + count2; ++k)
                {
                    if (k <= count1)
                        fprintf(f, "%d\t%d\t", v1Prime[k % count1].x, v1Prime[k % count1].y);
                    else
                        fprintf(f, "\t\t");
                    if (k <= count2)
                        fprintf(f, "%d\t%d\t", v2Prime[k % count2].x, v2Prime[k % count2].y);
                    else
                        fprintf(f, "\t\t");
                    if (k <= count)
                        fprintf(f, "%d\t%d\n", buffer[k % count].x, buffer[k % count].y);
                    else
                        fprintf(f, "\t\n");
                }
                fclose(f);
            }
        }
    }

    printf("Shape tests: %d passed, %d failed (%d intersecting, %d disjoint).\n", sPass, sFail, sIntersecting, sDisjoint);
    result += sFail;

    return result;
}

} // namespace omni

#ifdef RUN_POLY_INTERSECT_TESTS
// g++ -std=c++14 -o poly_tests.x -DRUN_POLY_INTERSECT_TESTS ConvexPolygonIntersectTests.cpp ConvexPolygonIntersect.cpp
int main()
{
    return omni::runConvexPolygonIntersectTests();
}
#endif // ifdef RUN_POLY_INTERSECT_TESTS
