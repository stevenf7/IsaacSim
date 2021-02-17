// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "vec3.h"

#include <cassert>

struct Matrix33;

template <typename T>
class XQuat
{
public:
    typedef T value_type;

    CUDA_CALLABLE XQuat() : x(0), y(0), z(0), w(1.0)
    {
    }
    CUDA_CALLABLE XQuat(const T* p) : x(p[0]), y(p[1]), z(p[2]), w(p[3])
    {
    }
    CUDA_CALLABLE XQuat(T x_, T y_, T z_, T w_) : x(x_), y(y_), z(z_), w(w_)
    {
    }
    CUDA_CALLABLE XQuat(const Vec3& v, float w) : x(v.x), y(v.y), z(v.z), w(w)
    {
    }
    CUDA_CALLABLE explicit XQuat(const Matrix33& m);

    CUDA_CALLABLE operator T*()
    {
        return &x;
    }
    CUDA_CALLABLE operator const T*() const
    {
        return &x;
    };

    CUDA_CALLABLE void Set(T x_, T y_, T z_, T w_)
    {
        x = x_;
        y = y_;
        z = z_;
        w = w_;
    }

    CUDA_CALLABLE XQuat<T> operator*(T scale) const
    {
        XQuat<T> r(*this);
        r *= scale;
        return r;
    }
    CUDA_CALLABLE XQuat<T> operator/(T scale) const
    {
        XQuat<T> r(*this);
        r /= scale;
        return r;
    }
    CUDA_CALLABLE XQuat<T> operator+(const XQuat<T>& v) const
    {
        XQuat<T> r(*this);
        r += v;
        return r;
    }
    CUDA_CALLABLE XQuat<T> operator-(const XQuat<T>& v) const
    {
        XQuat<T> r(*this);
        r -= v;
        return r;
    }
    CUDA_CALLABLE XQuat<T> operator*(XQuat<T> q) const
    {
        // quaternion multiplication
        return XQuat<T>(w * q.x + q.w * x + y * q.z - q.y * z, w * q.y + q.w * y + z * q.x - q.z * x,
                        w * q.z + q.w * z + x * q.y - q.x * y, w * q.w - x * q.x - y * q.y - z * q.z);
    }

    CUDA_CALLABLE XQuat<T>& operator*=(T scale)
    {
        x *= scale;
        y *= scale;
        z *= scale;
        w *= scale;
        return *this;
    }
    CUDA_CALLABLE XQuat<T>& operator/=(T scale)
    {
        T s(1.0f / scale);
        x *= s;
        y *= s;
        z *= s;
        w *= s;
        return *this;
    }
    CUDA_CALLABLE XQuat<T>& operator+=(const XQuat<T>& v)
    {
        x += v.x;
        y += v.y;
        z += v.z;
        w += v.w;
        return *this;
    }
    CUDA_CALLABLE XQuat<T>& operator-=(const XQuat<T>& v)
    {
        x -= v.x;
        y -= v.y;
        z -= v.z;
        w -= v.w;
        return *this;
    }

    CUDA_CALLABLE bool operator!=(const XQuat<T>& v) const
    {
        return (x != v.x || y != v.y || z != v.z || w != v.w);
    }

    // negate
    CUDA_CALLABLE XQuat<T> operator-() const
    {
        return XQuat<T>(-x, -y, -z, -w);
    }

    CUDA_CALLABLE XVector3<T> GetAxis() const
    {
        return XVector3<T>(x, y, z);
    }

    T x, y, z, w;
};

typedef XQuat<float> Quat;

// lhs scalar scale
template <typename T>
CUDA_CALLABLE XQuat<T> operator*(T lhs, const XQuat<T>& rhs)
{
    XQuat<T> r(rhs);
    r *= lhs;
    return r;
}

template <typename T>
CUDA_CALLABLE bool operator==(const XQuat<T>& lhs, const XQuat<T>& rhs)
{
    return (lhs.x == rhs.x && lhs.y == rhs.y && lhs.z == rhs.z && lhs.w == rhs.w);
}

template <typename T>
CUDA_CALLABLE inline XQuat<T> QuatFromAxisAngle(const Vec3& axis, float angle)
{
    Vec3 v = Normalize(axis);

    float half = angle * 0.5f;
    float w = cosf(half);

    const float sin_theta_over_two = sinf(half);
    v *= sin_theta_over_two;

    return XQuat<T>(v.x, v.y, v.z, w);
}

CUDA_CALLABLE inline float Dot(const Quat& a, const Quat& b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
}

CUDA_CALLABLE inline float Length(const Quat& a)
{
    return sqrtf(Dot(a, a));
}

CUDA_CALLABLE inline Quat QuatFromRollPitchYaw(float roll, float pitch, float yaw)
{
    Quat q;
    // Abbreviations for the various angular functions
    float cy = cos(yaw * 0.5f);
    float sy = sin(yaw * 0.5f);
    float cr = cos(roll * 0.5f);
    float sr = sin(roll * 0.5f);
    float cp = cos(pitch * 0.5f);
    float sp = sin(pitch * 0.5f);

    q.w = (float)(cy * cr * cp + sy * sr * sp);
    q.x = (float)(cy * sr * cp - sy * cr * sp);
    q.y = (float)(cy * cr * sp + sy * sr * cp);
    q.z = (float)(sy * cr * cp - cy * sr * sp);

    return q;
}

CUDA_CALLABLE inline void RollPitchYawFromQuat(const Quat& q, float& bank, float& attitude, float& heading)
{
    float sqw = q.w * q.w;
    float sqx = q.x * q.x;
    float sqy = q.y * q.y;
    float sqz = q.z * q.z;
    float unit = sqx + sqy + sqz + sqw; // if normalised is one, otherwise is correction factor
    float test = q.x * q.y + q.z * q.w;

    if (test > 0.499f * unit)
    { // singularity at north pole
        heading = 2.f * atan2(q.x, q.w);
        attitude = kPi / 2.f;
        bank = 0.f;
        return;
    }

    if (test < -0.499f * unit)
    { // singularity at south pole
        heading = -2.f * atan2(q.x, q.w);
        attitude = -kPi / 2.f;
        bank = 0.f;
        return;
    }

    heading = atan2(2.f * q.x * q.y + 2.f * q.w * q.z, sqx - sqy - sqz + sqw);
    attitude = asin(-2.f * q.x * q.z + 2.f * q.y * q.w);
    bank = atan2(2.f * q.y * q.z + 2.f * q.x * q.w, -sqx - sqy + sqz + sqw);
}

CUDA_CALLABLE inline Quat rpy2quat(float roll, float pitch, float yaw)
{
    Quat q;
    // Abbreviations for the various angular functions
    float cy = cos(yaw * 0.5f);
    float sy = sin(yaw * 0.5f);
    float cr = cos(roll * 0.5f);
    float sr = sin(roll * 0.5f);
    float cp = cos(pitch * 0.5f);
    float sp = sin(pitch * 0.5f);

    q.w = (float)(cy * cr * cp + sy * sr * sp);
    q.x = (float)(cy * sr * cp - sy * cr * sp);
    q.y = (float)(cy * cr * sp + sy * sr * cp);
    q.z = (float)(sy * cr * cp - cy * sr * sp);

    return q;
}

CUDA_CALLABLE inline void quat2rpy(const Quat& q1, float& bank, float& attitude, float& heading)
{
    float sqw = q1.w * q1.w;
    float sqx = q1.x * q1.x;
    float sqy = q1.y * q1.y;
    float sqz = q1.z * q1.z;
    float unit = sqx + sqy + sqz + sqw; // if normalised is one, otherwise is correction factor
    float test = q1.x * q1.y + q1.z * q1.w;

    if (test > 0.499f * unit)
    { // singularity at north pole
        heading = 2.f * atan2(q1.x, q1.w);
        attitude = kPi / 2.f;
        bank = 0.f;
        return;
    }

    if (test < -0.499f * unit)
    { // singularity at south pole
        heading = -2.f * atan2(q1.x, q1.w);
        attitude = -kPi / 2.f;
        bank = 0.f;
        return;
    }

    heading = atan2(2.f * q1.x * q1.y + 2.f * q1.w * q1.z, sqx - sqy - sqz + sqw);
    attitude = asin(-2.f * q1.x * q1.z + 2.f * q1.y * q1.w);
    bank = atan2(2.f * q1.y * q1.z + 2.f * q1.x * q1.w, -sqx - sqy + sqz + sqw);
}

CUDA_CALLABLE inline void zUpQuat2rpy(const Quat& q1, float& roll, float& pitch, float& yaw)
{
    // roll (x-axis rotation)
    float sinr_cosp = 2.0f * (q1.w * q1.x + q1.y * q1.z);
    float cosr_cosp = 1.0f - 2.0f * (q1.x * q1.x + q1.y * q1.y);
    roll = atan2(sinr_cosp, cosr_cosp);

    // pitch (y-axis rotation)
    float sinp = +2.0f * (q1.w * q1.y - q1.z * q1.x);
    if (fabs(sinp) >= 1)
        pitch = (float)copysign(kPi / 2.0f, sinp);
    else
        pitch = asin(sinp);

    // yaw (z-axis rotation)
    float siny_cosp = 2.0f * (q1.w * q1.z + q1.x * q1.y);
    float cosy_cosp = 1.0f - 2.0f * (q1.y * q1.y + q1.z * q1.z);
    yaw = atan2(siny_cosp, cosy_cosp);
}

CUDA_CALLABLE inline void getEulerZYX(const Quat& q, float& yawZ, float& pitchY, float& rollX)
{
    float squ;
    float sqx;
    float sqy;
    float sqz;
    float sarg;
    sqx = q.x * q.x;
    sqy = q.y * q.y;
    sqz = q.z * q.z;
    squ = q.w * q.w;

    rollX = atan2(2 * (q.y * q.z + q.w * q.x), squ - sqx - sqy + sqz);
    sarg = (-2.0f) * (q.x * q.z - q.w * q.y);
    pitchY = sarg <= (-1.0f) ? (-0.5f) * kPi : (sarg >= (1.0f) ? (0.5f) * kPi : asinf(sarg));
    yawZ = atan2(2 * (q.x * q.y + q.w * q.z), squ + sqx - sqy - sqz);
}

// rotate vector by quaternion (q, w)
CUDA_CALLABLE inline Vec3 Rotate(const Quat& q, const Vec3& x)
{
    return x * (2.0f * q.w * q.w - 1.0f) + Cross(Vec3(q), x) * q.w * 2.0f + Vec3(q) * Dot(Vec3(q), x) * 2.0f;
}

CUDA_CALLABLE inline Vec3 operator*(const Quat& q, const Vec3& v)
{
    return Rotate(q, v);
}

CUDA_CALLABLE inline Vec3 GetBasisVector0(const Quat& q)
{
    return Rotate(q, Vec3(1.0f, 0.0f, 0.0f));
}
CUDA_CALLABLE inline Vec3 GetBasisVector1(const Quat& q)
{
    return Rotate(q, Vec3(0.0f, 1.0f, 0.0f));
}
CUDA_CALLABLE inline Vec3 GetBasisVector2(const Quat& q)
{
    return Rotate(q, Vec3(0.0f, 0.0f, 1.0f));
}

// rotate vector by inverse transform in (q, w)
CUDA_CALLABLE inline Vec3 RotateInv(const Quat& q, const Vec3& x)
{
    return x * (2.0f * q.w * q.w - 1.0f) - Cross(Vec3(q), x) * q.w * 2.0f + Vec3(q) * Dot(Vec3(q), x) * 2.0f;
}

CUDA_CALLABLE inline Quat Inverse(const Quat& q)
{
    return Quat(-q.x, -q.y, -q.z, q.w);
}

CUDA_CALLABLE inline Quat Normalize(const Quat& q)
{
    float lSq = q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w;

    if (lSq > 0.0f)
    {
        float invL = 1.0f / sqrtf(lSq);

        return q * invL;
    }
    else
        return Quat();
}

//
// given two quaternions and a time-step returns the corresponding angular velocity vector
//
CUDA_CALLABLE inline Vec3 DifferentiateQuat(const Quat& q1, const Quat& q0, float invdt)
{
    Quat dq = q1 * Inverse(q0);

    float sinHalfTheta = Length(dq.GetAxis());
    float theta = asinf(sinHalfTheta) * 2.0f;

    if (fabsf(theta) < 0.001f)
    {
        // use linear approximation approx for small angles
        Quat dqdt = (q1 - q0) * invdt;
        Quat omega = dqdt * Inverse(q0);

        return Vec3(omega.x, omega.y, omega.z) * 2.0f;
    }
    else
    {
        // use inverse exponential map
        Vec3 axis = Normalize(dq.GetAxis());
        return axis * theta * invdt;
    }
}


CUDA_CALLABLE inline Quat IntegrateQuat(const Vec3& omega, const Quat& q0, float dt)
{
    Vec3 axis;
    float w = Length(omega);

    if (w * dt < 0.001f)
    {
        // sinc approx for small angles
        axis = omega * (0.5f * dt - (dt * dt * dt) / 48.0f * w * w);
    }
    else
    {
        axis = omega * (sinf(0.5f * w * dt) / w);
    }

    Quat dq;
    dq.x = axis.x;
    dq.y = axis.y;
    dq.z = axis.z;
    dq.w = cosf(w * dt * 0.5f);

    Quat q1 = dq * q0;

    // explicit re-normalization here otherwise we do some see energy drift
    return Normalize(q1);
}
