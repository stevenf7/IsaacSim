// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include <carb/InterfaceUtils.h>
namespace omni
{
namespace isaac
{
namespace core_nodes
{

static constexpr float PI = 3.14159265358979323846f;

inline constexpr float Deg2Rad(float deg)
{
    return (deg / 180.f) * PI;
}

inline float dot(carb::Float3 a, carb::Float3 b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

inline carb::Float3 cross(carb::Float3 a, carb::Float3 b)
{
    return { a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x };
}

inline carb::Float3 operator*(float b, carb::Float3 a)
{
    return { b * a.x, b * a.y, b * a.z };
}

inline carb::Float3 operator+(carb::Float3 a, carb::Float3 b)
{
    return { a.x + b.x, a.y + b.y, a.z + b.z };
}

inline carb::Float4 MultiplyQs(const carb::Float4& q1, const carb::Float4& q2)
{
    carb::Float3 Q1{ q1.x, q1.y, q1.z };
    carb::Float3 Q2{ q2.x, q2.y, q2.z };
    float result_s;
    carb::Float3 result_v;
    result_s = (q1.w * q2.w) - dot(Q1, Q2);
    result_v = (q1.w * Q2) + (q2.w * Q1) + cross(Q1, Q2);

    return { result_v.x, result_v.y, result_v.z, result_s };
}

inline float dot(carb::Float4 a, carb::Float4 b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
}
//-----------------------------------------------------------------------------
inline carb::Float4 ConjugateQ(const carb::Float4& q)
{
    return { -q.x, -q.y, -q.z, q.w };
}

inline carb::Float4 operator/(carb::Float4 a, float b)
{
    return { a.x / b, a.y / b, a.z / b, a.w / b };
}

//-----------------------------------------------------------------------------
inline carb::Float4 ReciprocateQ(const carb::Float4& q)
{
    return (ConjugateQ(q) / dot(q, q));
}

//-----------------------------------------------------------------------------
inline carb::Float4 ConjugateQByQ(const carb::Float4& q1, const carb::Float4& q2)
{
    return MultiplyQs(q2, MultiplyQs(q1, ReciprocateQ(q2)));
}

inline carb::Float3 rotatePointByQuat(const carb::Float3& v, const carb::Float4& q)
{
    carb::Float4 tmpQ{ v.x, v.y, v.z, 0 };

    tmpQ = ConjugateQByQ(tmpQ, q);

    return { tmpQ.x, tmpQ.y, tmpQ.z };
}

} // core_nodes
} // isaac
} // omni
