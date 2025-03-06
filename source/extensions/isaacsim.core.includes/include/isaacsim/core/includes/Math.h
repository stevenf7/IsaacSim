// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <DynamicControlTypes.h>
#include <cmath>

namespace isaacsim
{
namespace core
{
namespace includes
{

/**
 * @namespace math
 * @brief Mathematical utility functions for 3D graphics and physics calculations.
 * @details
 * This namespace provides a comprehensive set of mathematical operations commonly used in
 * 3D graphics and physics simulations. It includes:
 * - Vector operations (dot product, cross product, normalization)
 * - Quaternion operations (multiplication, inversion, normalization)
 * - Transform operations (composition, inversion)
 * - Interpolation functions (linear and spherical)
 * - Geometric utilities (basis vectors, look-at calculations)
 *
 * All functions are implemented as inline for performance optimization.
 */
namespace math
{
/**
 * @brief Computes the cross product of two 3D vectors.
 * @details Calculates the vector perpendicular to both input vectors following the right-hand rule.
 *
 * @param[in] b First vector
 * @param[in] c Second vector
 * @return carb::Float3 The cross product vector
 *
 * @note The resulting vector is perpendicular to both input vectors
 */
inline carb::Float3 cross(const carb::Float3& b, const carb::Float3& c)
{
    return carb::Float3{ b.y * c.z - b.z * c.y, b.z * c.x - b.x * c.z, b.x * c.y - b.y * c.x };
}

/**
 * @brief Computes the dot product of two 3D vectors.
 * @details Calculates the scalar product of two vectors, representing their similarity.
 *
 * @param[in] v1 First vector
 * @param[in] v2 Second vector
 * @return float The dot product scalar
 *
 * @note Returns 0 for perpendicular vectors, positive for similar directions, negative for opposite directions
 */
inline float dot(const carb::Float3& v1, const carb::Float3& v2)
{
    return v1.x * v2.x + v1.y * v2.y + v1.z * v2.z;
}

/**
 * @brief Computes the dot product of two 4D vectors.
 * @details Calculates the scalar product of two 4D vectors, useful for quaternion calculations.
 *
 * @param[in] v1 First vector
 * @param[in] v2 Second vector
 * @return float The dot product scalar
 */
inline float dot(const carb::Float4& v1, const carb::Float4& v2)
{
    return v1.x * v2.x + v1.y * v2.y + v1.z * v2.z + v1.w * v2.w;
}

/**
 * @brief Computes the inverse of a quaternion.
 * @details
 * For unit quaternions, the inverse is equal to the conjugate.
 * This function assumes the input quaternion is normalized.
 *
 * @param[in] q Input quaternion
 * @return carb::Float4 The inverse quaternion
 *
 * @note Assumes input quaternion is normalized
 */
inline carb::Float4 inverse(const carb::Float4& q)
{
    return carb::Float4{ -q.x, -q.y, -q.z, q.w };
}

/**
 * @brief Scales a 3D vector by a scalar value.
 * @details Multiplies each component of the vector by the scalar.
 *
 * @param[in] a Vector to scale
 * @param[in] x Scalar value
 * @return carb::Float3 The scaled vector
 */
inline carb::Float3 operator*(const carb::Float3& a, const float x)
{
    return carb::Float3{ a.x * x, a.y * x, a.z * x };
}

/**
 * @brief Scales a 4D vector/quaternion by a scalar value.
 * @details Multiplies each component of the vector by the scalar.
 *
 * @param[in] a Vector to scale
 * @param[in] x Scalar value
 * @return carb::Float4 The scaled vector
 */
inline carb::Float4 operator*(const carb::Float4& a, const float x)
{
    return carb::Float4{ a.x * x, a.y * x, a.z * x, a.w * x };
}

/**
 * @brief Performs quaternion multiplication.
 * @details
 * Implements the Hamilton product for quaternions, representing 3D rotation composition.
 * The order of multiplication matters (non-commutative).
 *
 * @param[in] a First quaternion (applied second)
 * @param[in] b Second quaternion (applied first)
 * @return carb::Float4 The resulting quaternion
 *
 * @note The resulting rotation is b followed by a
 */
inline carb::Float4 operator*(const carb::Float4& a, const carb::Float4& b)
{
    return carb::Float4{ a.w * b.x + b.w * a.x + a.y * b.z - b.y * a.z, a.w * b.y + b.w * a.y + a.z * b.x - b.z * a.x,
                         a.w * b.z + b.w * a.z + a.x * b.y - b.x * a.y, a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z };
}

/**
 * @brief Adds two 3D vectors.
 * @details Component-wise addition of vectors.
 *
 * @param[in] a First vector
 * @param[in] b Second vector
 * @return carb::Float3 The sum vector
 */
inline carb::Float3 operator+(const carb::Float3& a, const carb::Float3& b)
{
    return carb::Float3{ a.x + b.x, a.y + b.y, a.z + b.z };
}

/**
 * @brief Subtracts two 3D vectors.
 * @details Component-wise subtraction of vectors.
 *
 * @param[in] a First vector (minuend)
 * @param[in] b Second vector (subtrahend)
 * @return carb::Float3 The difference vector
 */
inline carb::Float3 operator-(const carb::Float3& a, const carb::Float3& b)
{
    return carb::Float3{ a.x - b.x, a.y - b.y, a.z - b.z };
}

/**
 * @brief Adds two 4D vectors/quaternions.
 * @details Component-wise addition of vectors.
 *
 * @param[in] a First vector
 * @param[in] b Second vector
 * @return carb::Float4 The sum vector
 */
inline carb::Float4 operator+(const carb::Float4& a, const carb::Float4& b)
{
    return carb::Float4{ a.x + b.x, a.y + b.y, a.z + b.z, a.w + b.w };
}

/**
 * @brief Subtracts two 4D vectors/quaternions.
 * @details Component-wise subtraction of vectors.
 *
 * @param[in] a First vector (minuend)
 * @param[in] b Second vector (subtrahend)
 * @return carb::Float4 The difference vector
 */
inline carb::Float4 operator-(const carb::Float4& a, const carb::Float4& b)
{
    return carb::Float4{ a.x - b.x, a.y - b.y, a.z - b.z, a.w - b.w };
}

/**
 * @brief Normalizes a quaternion to unit length.
 * @details
 * Scales the quaternion so its magnitude becomes 1.
 * Returns identity quaternion if input magnitude is 0.
 *
 * @param[in] q Input quaternion
 * @return carb::Float4 Normalized quaternion
 *
 * @note Returns identity quaternion (0,0,0,1) if input magnitude is 0
 */
inline carb::Float4 normalize(const carb::Float4& q)
{
    float lSq = q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w;
    if (lSq > 0.0f)
    {
        float invL = 1.0f / std::sqrt(lSq);
        return q * invL;
    }
    else
    {
        return carb::Float4{ 0.0f, 0.0f, 0.0f, 1.0f };
    }
}

/**
 * @brief Normalizes a 3D vector to unit length.
 * @details
 * Scales the vector so its magnitude becomes 1.
 * Returns zero vector if input magnitude is 0.
 *
 * @param[in] q Input vector
 * @return carb::Float3 Normalized vector
 *
 * @note Returns zero vector if input magnitude is 0
 */
inline carb::Float3 normalize(const carb::Float3& q)
{
    float lSq = q.x * q.x + q.y * q.y + q.z * q.z;
    if (lSq > 0.0f)
    {
        float invL = 1.0f / sqrtf(lSq);
        return q * invL;
    }
    else
    {
        return carb::Float3{ 0.0f, 0.0f, 0.0f };
    }
}

/**
 * @brief Rotates a vector by a quaternion.
 * @details
 * Applies a quaternion rotation to a 3D vector.
 * Uses the quaternion sandwich product: q * v * q^(-1)
 *
 * @param[in] q Rotation quaternion (must be normalized)
 * @param[in] x Vector to rotate
 * @return carb::Float3 Rotated vector
 *
 * @note Assumes input quaternion is normalized
 */
inline carb::Float3 rotate(const carb::Float4& q, const carb::Float3 x)
{
    const carb::Float3 v_q = carb::Float3{ q.x, q.y, q.z };
    return x * (2.0f * q.w * q.w - 1.0f) + cross(v_q, x) * q.w * 2.0f + v_q * dot(v_q, x) * 2.0f;
}

/**
 * @brief Multiplies two transforms to compose them.
 * @details
 * Combines two transforms by applying them in sequence.
 * The order of multiplication matters (non-commutative).
 *
 * @param[in] self First transform (applied second)
 * @param[in] other Second transform (applied first)
 * @return DcTransform The composed transform
 *
 * @note The resulting transform applies other first, then self
 */
inline omni::isaac::dynamic_control::DcTransform operator*(const omni::isaac::dynamic_control::DcTransform& self,
                                                           const omni::isaac::dynamic_control::DcTransform& other)
{
    return omni::isaac::dynamic_control::DcTransform{ rotate(self.r, other.p) + self.p, normalize(self.r * other.r) };
}

/**
 * @brief Computes the inverse of a transform.
 * @details
 * Calculates the inverse transform that, when applied after the original,
 * results in the identity transform.
 *
 * @param[in] transform Transform to invert
 * @return DcTransform The inverse transform
 *
 * @note For a valid transform T, T * inverse(T) equals the identity transform
 */
inline omni::isaac::dynamic_control::DcTransform inverse(const omni::isaac::dynamic_control::DcTransform& transform)
{
    omni::isaac::dynamic_control::DcTransform t;
    t.r = inverse(transform.r);
    t.p = rotate(t.r, transform.p) * -1.0f;
    return t;
}

/**
 * @brief Computes the relative transform from a to b.
 * @details
 * Calculates the transform that, when applied to a, results in b.
 * This is equivalent to inverse(a) * b.
 *
 * @param[in] a Reference transform
 * @param[in] b Target transform
 * @return DcTransform Transform from a to b
 */
inline omni::isaac::dynamic_control::DcTransform transformInv(const omni::isaac::dynamic_control::DcTransform& a,
                                                              const omni::isaac::dynamic_control::DcTransform& b)
{
    carb::Float4 qconj;
    qconj.w = a.r.w;
    qconj.x = -a.r.x;
    qconj.y = -a.r.y;
    qconj.z = -a.r.z;
    float invqnorm = 1.0f / (qconj.w * qconj.w + qconj.x * qconj.x + qconj.y * qconj.y + qconj.z * qconj.z);

    carb::Float4 qinv;
    qinv.w = qconj.w * invqnorm;
    qinv.x = -qconj.x * invqnorm;
    qinv.y = -qconj.y * invqnorm;
    qinv.z = -qconj.z * invqnorm;

    carb::Float4 qv = a.r;
    qv.w = 0;
    qv.x = b.p.x - a.p.x;
    qv.y = b.p.y - a.p.y;
    qv.z = b.p.z - a.p.z;

    carb::Float4 result = (qconj * (qv * qinv));
    carb::Float4 res_quat = (b.r * qconj);
    omni::isaac::dynamic_control::DcTransform res;
    res.p.x = result.x;
    res.p.y = result.y;
    res.p.z = result.z;
    res.r = res_quat;
    return res;
}

/**
 * @brief Computes the local transform of b relative to transform a
 * @details
 * Calculates the transform that represents b's pose in a's local coordinate frame.
 * This is equivalent to inverse(a) * b.
 *
 * @param[in] a Reference transform that defines the local coordinate frame
 * @param[in] b Target transform to be expressed in a's frame
 * @return pxr::GfTransform Transform representing b in a's local frame
 *
 * @note This is the Pixar USD transform version of transformInv()
 */
inline pxr::GfTransform transformInv(const pxr::GfTransform& a, const pxr::GfTransform& b)
{
    pxr::GfRotation qinv = a.GetRotation().GetQuat().GetConjugate();
    pxr::GfTransform trans;
    trans.SetRotation(b.GetRotation() * qinv);
    trans.SetTranslation(qinv.TransformDir(b.GetTranslation() - a.GetTranslation()));
    return trans;
}

/**
 * @brief Gets the X basis vector from a rotation quaternion.
 * @details
 * Extracts the local X axis direction after applying the rotation.
 * Equivalent to rotating the world X axis (1,0,0) by the quaternion.
 *
 * @param[in] q Rotation quaternion (must be normalized)
 * @return carb::Float3 The rotated X basis vector
 *
 * @note Assumes input quaternion is normalized
 */
inline carb::Float3 getBasisVectorX(const carb::Float4& q)
{
    return rotate(q, carb::Float3{ 1.0f, 0.0f, 0.0f });
}

/**
 * @brief Gets the Y basis vector from a rotation quaternion.
 * @details
 * Extracts the local Y axis direction after applying the rotation.
 * Equivalent to rotating the world Y axis (0,1,0) by the quaternion.
 *
 * @param[in] q Rotation quaternion (must be normalized)
 * @return carb::Float3 The rotated Y basis vector
 *
 * @note Assumes input quaternion is normalized
 */
inline carb::Float3 getBasisVectorY(const carb::Float4& q)
{
    return rotate(q, carb::Float3{ 0.0f, 1.0f, 0.0f });
}

/**
 * @brief Gets the Z basis vector from a rotation quaternion.
 * @details
 * Extracts the local Z axis direction after applying the rotation.
 * Equivalent to rotating the world Z axis (0,0,1) by the quaternion.
 *
 * @param[in] q Rotation quaternion (must be normalized)
 * @return carb::Float3 The rotated Z basis vector
 *
 * @note Assumes input quaternion is normalized
 */
inline carb::Float3 getBasisVectorZ(const carb::Float4& q)
{
    return rotate(q, carb::Float3{ 0.0f, 0.0f, 1.0f });
}

/**
 * @brief Linearly interpolates between two 3D vectors.
 * @details
 * Performs linear interpolation between start and end vectors.
 * The parameter t controls the interpolation: 0 returns start, 1 returns end.
 *
 * @param[in] start Starting vector
 * @param[in] end Ending vector
 * @param[in] t Interpolation parameter [0,1]
 * @return carb::Float3 The interpolated vector
 *
 * @note For values of t outside [0,1], extrapolation is performed
 */
inline carb::Float3 lerp(const carb::Float3& start, const carb::Float3& end, const float t)
{
    return start + ((end - start) * t);
}

/**
 * @brief Linearly interpolates between two quaternions.
 * @details
 * Performs linear interpolation between start and end quaternions.
 * Note that this does not maintain constant angular velocity.
 *
 * @param[in] start Starting quaternion
 * @param[in] end Ending quaternion
 * @param[in] t Interpolation parameter [0,1]
 * @return carb::Float4 The interpolated quaternion
 *
 * @note For better rotation interpolation, consider using slerp instead
 */
inline carb::Float4 lerp(const carb::Float4& start, const carb::Float4& end, const float t)
{
    return normalize(start + ((end - start) * t));
}

/**
 * @brief Performs spherical linear interpolation between quaternions.
 * @details
 * Interpolates along the shortest arc on the quaternion sphere.
 * Maintains constant angular velocity throughout the interpolation.
 *
 * @param[in] start Starting quaternion (must be normalized)
 * @param[in] end Ending quaternion (must be normalized)
 * @param[in] t Interpolation parameter [0,1]
 * @return carb::Float4 The interpolated quaternion
 *
 * @note Both input quaternions must be normalized
 * @warning May be unstable for angles close to 180 degrees
 */
inline carb::Float4 slerp(const carb::Float4& start, const carb::Float4& end, const float t)
{
    float dot_value = dot(start, end);
    carb::Float4 s{ start.x, start.y, start.z, start.w };
    if (dot_value < 0)
    {
        s = start * -1.0f;
        dot_value = -dot_value;
    }

    if (dot_value > 0.9995)
    {
        return lerp(s, end, t);
    }

    float theta_0 = acos(dot_value);
    float s_t_0 = sin(theta_0);

    float theta = theta_0 * t;
    float s_t = sin(theta);

    float s1 = s_t / s_t_0;
    float s0 = cos(theta) - dot_value * s1;

    return (s * s0) + (end * s1);
}

/**
 * @brief Linearly interpolates between two transforms.
 * @details
 * Performs separate linear interpolation on position and rotation components.
 * Position uses vector lerp, rotation uses quaternion lerp.
 *
 * @param[in] a Starting transform
 * @param[in] b Ending transform
 * @param[in] t Interpolation parameter [0,1]
 * @return DcTransform The interpolated transform
 */
inline omni::isaac::dynamic_control::DcTransform lerp(const omni::isaac::dynamic_control::DcTransform& a,
                                                      const omni::isaac::dynamic_control::DcTransform& b,
                                                      const float t)
{
    return omni::isaac::dynamic_control::DcTransform{ lerp(a.p, b.p, t), lerp(a.r, b.r, t) };
}

/**
 * @brief Performs spherical linear interpolation between transforms.
 * @details
 * Interpolates position linearly and rotation using slerp.
 * This provides smoother rotation interpolation than regular lerp.
 *
 * @param[in] a Starting transform
 * @param[in] b Ending transform
 * @param[in] t Interpolation parameter [0,1]
 * @return DcTransform The interpolated transform
 */
inline omni::isaac::dynamic_control::DcTransform slerp(const omni::isaac::dynamic_control::DcTransform& a,
                                                       const omni::isaac::dynamic_control::DcTransform& b,
                                                       const float t)
{
    return omni::isaac::dynamic_control::DcTransform{ lerp(a.p, b.p, t), slerp(a.r, b.r, t) };
}

/**
 * @brief Computes a look-at quaternion rotation.
 * @details
 * Creates a rotation that orients an object to look at a target point.
 * The up vector defines the world-space up direction for orientation.
 *
 * @param[in] camera Position of the camera/object
 * @param[in] target Point to look at
 * @param[in] up World-space up vector (typically {0,1,0})
 * @return pxr::GfQuatf The resulting look-at rotation
 *
 * @note The up vector should not be parallel to the look direction
 */
inline pxr::GfQuatf lookAt(const pxr::GfVec3f& camera, const pxr::GfVec3f& target, const pxr::GfVec3f& up)
{
    pxr::GfVec3f F = (target - camera).GetNormalized();
    pxr::GfVec3f R = pxr::GfCross(F, up).GetNormalized();
    pxr::GfVec3f U = pxr::GfCross(R, F);

    float trace = R[0] + U[1] + F[2];
    if (trace > 0.0f)
    {
        float s = 0.5f / sqrtf(trace + 1.0f);
        return pxr::GfQuatf(0.25f / s, pxr::GfVec3f((U[2] - F[1]) * s, (F[0] - R[2]) * s, (R[1] - U[0]) * s));
    }
    else
    {
        if (R[0] > U[1] and R[0] > F[2])
        {
            float s = 2.0f * sqrtf(1.0f + R[0] - U[1] - F[2]);
            return pxr::GfQuatf((U[2] - F[1]) / s, pxr::GfVec3f(0.25f * s, (U[0] + R[1]) / s, (F[0] + R[2]) / s));
        }
        else if (U[1] > F[2])
        {
            float s = 2.0f * sqrtf(1.0f + U[1] - R[0] - F[2]);
            return pxr::GfQuatf((F[0] - R[2]) / s, pxr::GfVec3f((U[0] + R[1]) / s, 0.25f * s, (F[1] + U[2]) / s));
        }
        else
        {
            float s = 2.0f * sqrtf(1.0f + F[2] - R[0] - U[1]);
            return pxr::GfQuatf((R[1] - U[0]) / s, pxr::GfVec3f((F[0] + R[2]) / s, (F[1] + U[2]) / s, 0.25f * s));
        }
    }
}

/**
 * @brief Rounds a number to the nearest multiple of a given value.
 * @details
 * Rounds the input to the nearest multiple of the place value.
 * For example, roundNearest(3.7, 0.5) returns 3.5.
 *
 * @param[in] input Value to round
 * @param[in] place Multiple to round to
 * @return double The rounded value
 *
 * @note If place is 0, returns the input value unchanged
 */
inline double roundNearest(double input, double place)
{
    if (place > 0.0)
    {
        return floor(input * place + 0.5) / place;
    }

    return input;
}

}
}
}
}
