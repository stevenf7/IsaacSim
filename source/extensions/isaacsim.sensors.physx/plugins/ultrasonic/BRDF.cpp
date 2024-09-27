// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "BRDF.h"

#include <algorithm>
#include <iostream>

float D_GGX(float NoH, float a)
{
    float a2 = a * a;
    float f = (NoH * a2 - NoH) * NoH + 1.0f;
    return a2 / (physx::PxPi * f * f);
}

float F_Schlick(float u, float f0)
{
    return f0 + (1.0f - f0) * pow(1.0f - u, 5.0f);
}

float V_SmithGGXCorrelated(float NoV, float NoL, float a)
{
    float a2 = a * a;
    float GGXL = NoV * sqrt((-NoL * a2 + NoL) * NoL + a2);
    float GGXV = NoL * sqrt((-NoV * a2 + NoV) * NoV + a2);
    return 0.5f / (GGXV + GGXL);
}

float Fd_Lambert()
{
    return 1.0f / physx::PxPi;
}

float clamp(float n, float lower, float upper)
{
    return std::max(lower, std::min(n, upper));
}

float approx_BRDF(const physx::PxVec3& v,
                  const physx::PxVec3& l,
                  const physx::PxVec3& n,
                  float perceptualRoughness,
                  float reflectance,
                  float metallic,
                  float baseColor)
{
    physx::PxVec3 h = (v + l).getNormalized();

    float NoV = abs(n.dot(v)) + 1e-5f;
    float NoL = clamp(n.dot(l), 0.0f, 1.0f);
    float NoH = clamp(n.dot(h), 0.0f, 1.0f);
    float LoH = clamp(l.dot(h), 0.0f, 1.0f);

    // perceptually linear roughness to roughness (see parameterization)
    float roughness = perceptualRoughness * perceptualRoughness;

    float D = D_GGX(NoH, roughness);
    float f0 = 0.16f * reflectance * reflectance * (1.0f - metallic) + metallic;
    float F = F_Schlick(LoH, f0);
    float V = V_SmithGGXCorrelated(NoV, NoL, roughness);

    // specular BRDF
    float Fr = (D * V) * F;

    // diffuse BRDF
    float diffuseColor = (1.0f - metallic) * baseColor;
    float Fd = diffuseColor * Fd_Lambert();

    return (Fd + Fr);
}

/**
 * @brief Incident intensity is attenuated by the cosine of the angle between the mirror and the receiver unit vectors
 * @param[in] normal The normal at the ray's point of contact on the convex hull
 * @param[in] worldPoint Point of contact of the ray on the hull
 * @param[in] worldMaterial USS Material containing 4 floats: perceptualRoughness, reflectance, metallic, base_color
 * @param[in] incidentIntensity the intensity of the beam that will be attenuated
 * @param[in] receiverLines for debug drawing USS beams
 * @param[in] useUSSMaterials whether using more complex uss materials for BRDF calculation
 **/

float BRDF::getReturnedIntensity(const ::physx::PxVec3& receiverOrigin,
                                 const ::physx::PxVec3& normal,
                                 const ::physx::PxVec3& worldPoint,
                                 const ::physx::PxVec4& worldMaterial,
                                 const float incidentIntensity,
                                 std::vector<carb::scenerenderer::PrimitiveVertex>* receiverLines,
                                 bool useUSSMaterials) const
{
    if (useUSSMaterials)
    {
        physx::PxVec3 M = (getMirrorRay(normal, worldPoint)).getNormalized();
        physx::PxVec3 V = (receiverOrigin - worldPoint);
        physx::PxVec3 l = (worldPoint - mEmitterOrigin).getNormalized();
        auto receiverLength = V.magnitude();
        V = V.getNormalized();

        float returnedIntensity = approx_BRDF(
            V, l, normal.getNormalized(), worldMaterial.x, worldMaterial.y, worldMaterial.z, worldMaterial.w);

        // add debug drawing beams
        if (receiverLines && returnedIntensity > 0)
        {
            carb::scenerenderer::PrimitiveVertex data;
            //  emitter to world hit point in green
            auto temp = worldPoint;
            data.position = { temp.x, temp.y, temp.z };
            data.color = carb::ColorRgba({ 0.0f, 1.0f, 0.0f, 1.0f });
            receiverLines->push_back(data);

            temp = mEmitterOrigin;
            data.position = { temp.x, temp.y, temp.z };
            receiverLines->push_back(data);

            // world hit point to mirror beam in red
            temp = worldPoint;
            data.position = { temp.x, temp.y, temp.z };
            data.color = carb::ColorRgba({ 1.0f, 0, 0, 1.0f });
            data.width = 1.0;
            receiverLines->push_back(data);

            temp = worldPoint + M * receiverLength;
            data.position = { temp.x, temp.y, temp.z };
            receiverLines->push_back(data);

            // // world point to normal in blue
            // temp = worldPoint + normal;
            // data.position = { temp.x, temp.y, temp.z };
            // data.color = carb::ColorRgba({ 0.0f, 0.0f, 1.0f , 1.0f });
            // receiverLines->push_back(data);

            // temp = worldPoint;
            // data.position = { temp.x, temp.y, temp.z };
            // receiverLines->push_back(data);

            // world point to receiver in yellow
            temp = worldPoint + V * receiverLength;
            data.position = { temp.x, temp.y, temp.z };
            data.color = carb::ColorRgba({ 1.0f, 1.0f, 0.0f, 1.0f });
            receiverLines->push_back(data);

            temp = worldPoint;
            data.position = { temp.x, temp.y, temp.z };
            receiverLines->push_back(data);
        }

        return returnedIntensity;
    }
    else // use simpler BRDF calculation
    {
        physx::PxVec3 M = (getMirrorRay(normal, worldPoint)).getNormalized();
        physx::PxVec3 V = (receiverOrigin - worldPoint).getNormalized();

        // cos(theta) = M V / (||M||||V||)
        float cosTheta = M.dot(V);
        float returnedIntensity = std::max(0.f, incidentIntensity * cosTheta);
        return returnedIntensity;
    }
}

std::vector<float> BRDF::getReturnedIntensities(const ::physx::PxVec3& receiverOrigin,
                                                const std::vector<::physx::PxVec3>& normals,
                                                const std::vector<::physx::PxVec3>& worldPoints,
                                                const std::vector<::physx::PxVec4>& worldMaterials,
                                                const std::vector<float>& incidentIntensities,
                                                std::vector<carb::scenerenderer::PrimitiveVertex>* receiverLines,
                                                bool useUSSMaterials) const
{
    std::vector<float> returnedIntensities;
    for (size_t i = 0; i < incidentIntensities.size(); i++)
    {
        returnedIntensities.push_back(getReturnedIntensity(receiverOrigin, normals[i], worldPoints[i], worldMaterials[i],
                                                           incidentIntensities[i], receiverLines, useUSSMaterials));
    }
    return returnedIntensities;
}


/**
 * @brief get the reflected ray from the incident ray and the normal
 **/
::physx::PxVec3 BRDF::getMirrorRay(const ::physx::PxVec3& normal, const ::physx::PxVec3& worldPoint) const
{
    ::physx::PxVec3 N = normal.getNormalized();
    // L is the ray pointing outwards from the collision point on surface to the emitter origin
    ::physx::PxVec3 L = mEmitterOrigin - worldPoint;
    float NdotL = N.dot(L);
    ::physx::PxVec3 mirror = (2.f * NdotL * N) - L;
    return mirror;
}
