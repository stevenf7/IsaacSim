#include "BRDF.h"

#include <algorithm>
#include <iostream>

/**
 * @brief Incident intensity is attenuated by the cosine of the angle between the mirror and the receiver unit vectors
 * @param[in] normal The normal at the ray's point of contact on the convex hull
 * @param[in] worldPoint Point of contact of the ray on the hull
 * @param[in] incidentIntensity the intensity of the beam that will be attenuated
 **/
float BRDF::getReturnedIntensity(const ::physx::PxVec3& receiverOrigin,
                                 const ::physx::PxVec3& normal,
                                 const ::physx::PxVec3& worldPoint,
                                 const float incidentIntensity) const
{
    ::physx::PxVec3 M = (getMirrorRay(normal, worldPoint)).getNormalized();
    ::physx::PxVec3 V = (receiverOrigin - worldPoint).getNormalized();

    // cos(theta) = M V / (||M||||V||)
    float cosTheta = M.dot(V);
    float returnedIntensity = std::max(0.f, incidentIntensity * cosTheta);
    return returnedIntensity;
}

std::vector<float> BRDF::getReturnedIntensities(const ::physx::PxVec3& receiverOrigin,
                                                const std::vector<::physx::PxVec3>& normals,
                                                const std::vector<::physx::PxVec3>& worldPoints,
                                                const std::vector<float>& incidentIntensities) const
{
    std::vector<float> returnedIntensities;
    for (size_t i = 0; i < incidentIntensities.size(); i++)
    {
        returnedIntensities.push_back(
            getReturnedIntensity(receiverOrigin, normals[i], worldPoints[i], incidentIntensities[i]));
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
