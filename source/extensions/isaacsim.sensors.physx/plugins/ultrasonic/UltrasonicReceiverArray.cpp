// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// ultrasonic includes
#include "UltrasonicReceiverArray.h"

#include "BRDF.h"

// STL includes
#include <algorithm>
#include <iostream>
#include <utility>
#include <vector>


// produce the vector of combined envelopes, one for each receiver
/*std::vector<USSEnvelope> UltrasonicReceiverArray::getCombinedActiveEnvelopeList(

    const std::vector<std::vector<uint8_t>>& adjacency,
    const std::vector<bool>& isFiring,
    const std::vector<bool>& isReceiving,
    const std::vector<::physx::PxVec3>& emitterOrigins,
    const std::vector<::physx::PxVec3>& receiverOrigins,
    const std::vector<std::vector<::physx::PxVec3>>& worldPoints)
{
    std::vector<USSEnvelope> envelopeList = getCombinedEnvelopeList(
        mNumBins, mMaxDist, adjacency, isFiring, isReceiving, emitterOrigins, receiverOrigins, worldPoints);
    std::vector<USSEnvelope> activeEnvelopeList;
    for (size_t i = 0; i < envelopeList.size(); i++)
    {
        if (isReceiving[i])
        {
            activeEnvelopeList.push_back(envelopeList[i]);
        }
    }
    return envelopeList;
}*/

// produce the vector of combined envelopes, one for each receiver
std::vector<USSEnvelope> UltrasonicReceiverArray::getCombinedEnvelopeList(

    const std::vector<std::vector<uint8_t>>& adjacency,
    const std::vector<bool>& isFiring,
    const std::vector<bool>& isReceiving,
    const std::vector<::physx::PxTransform>& emitterOrigins,
    const std::vector<::physx::PxTransform>& receiverOrigins,
    const std::vector<std::vector<::physx::PxVec3>>& worldPoints,
    const std::vector<std::vector<::physx::PxVec3>>& normals,
    const std::vector<std::vector<::physx::PxVec4>>& worldMaterials)
{
    std::vector<std::vector<USSEnvelope>> envelopeMatrix = getEnvelopeMatrix(
        adjacency, isFiring, isReceiving, emitterOrigins, receiverOrigins, worldPoints, normals, worldMaterials);
    std::vector<USSEnvelope> envelopeList(receiverOrigins.size(), USSEnvelope(mNumBins, mMaxDist));
    for (size_t i = 0; i < envelopeMatrix.size(); i++)
    {
        for (size_t j = 0; j < envelopeMatrix[i].size(); j++)
        {
            if (envelopeMatrix[i][j].isValid)
            {
                envelopeList[i] = envelopeList[i] + envelopeMatrix[i][j];
            }
        }
    }
    return envelopeList;
}

// produce the 2d vector of envelopes where the first index represents the
// receiver index and the second index represents the emitter index
std::vector<std::vector<USSEnvelope>> UltrasonicReceiverArray::getEnvelopeMatrix(

    const std::vector<std::vector<uint8_t>>& adjacency,
    const std::vector<bool>& isFiring,
    const std::vector<bool>& isReceiving,
    const std::vector<::physx::PxTransform>& emitterOrigins,
    const std::vector<::physx::PxTransform>& receiverOrigins,
    const std::vector<std::vector<::physx::PxVec3>>& worldPoints,
    const std::vector<std::vector<::physx::PxVec3>>& normals,
    const std::vector<std::vector<::physx::PxVec4>>& worldMaterials)
{
    std::vector<std::vector<USSEnvelope>> envelopeMatrix(
        receiverOrigins.size(), std::vector<USSEnvelope>(emitterOrigins.size(), USSEnvelope(mNumBins, mMaxDist)));
    auto totalPathLengths =
        getAdjacentDistances(adjacency, isFiring, isReceiving, emitterOrigins, receiverOrigins, worldPoints, normals);

    // receiver origins are indexed by i
    for (size_t i = 0; i < totalPathLengths.size(); i++)
    {
        BRDF brdf(emitterOrigins[i].p);
        // emitter origins are indexed by j
        for (size_t j = 0; j < totalPathLengths[i].size(); j++)
        {
            if (shouldProduceEnvelope(adjacency, isFiring, isReceiving, i, j) && !mUseBRDF)
            {
                // no attenuation of intensity based on angle, for now
                std::vector<float> intensities(totalPathLengths[i][j].size(), 1.f);
                envelopeMatrix[i][j].updateEnvelope(totalPathLengths[i][j], intensities);
            }
            else if (shouldProduceEnvelope(adjacency, isFiring, isReceiving, i, j) && mUseBRDF)
            {
                // no attenuation of intensity based on angle, for now
                std::vector<float> intensities(totalPathLengths[i][j].size(), 1.f);

                std::vector<float> attenuatedIntensities =
                    brdf.getReturnedIntensities(receiverOrigins[i].p, normals[j], worldPoints[j], worldMaterials[j],
                                                intensities, &mReceiverLines, mUseUSSMaterialsForBRDF);

                envelopeMatrix[i][j].updateEnvelope(totalPathLengths[i][j], attenuatedIntensities);
            }
            else
            {
                // give the envelope a negative value so we know there's an issue if debugging
                envelopeMatrix[i][j] = USSEnvelope(mNumBins, invalidEnvelopeFloat);
                envelopeMatrix[i][j].isValid = false;
            }
        }
    }
    return envelopeMatrix;
}

std::vector<std::vector<std::vector<float>>> UltrasonicReceiverArray::getAdjacentDistances(
    const std::vector<std::vector<uint8_t>>& adjacency,
    const std::vector<bool>& isFiring,
    const std::vector<bool>& isReceiving,
    const std::vector<::physx::PxTransform>& emitterOrigins,
    const std::vector<::physx::PxTransform>& receiverOrigins,
    const std::vector<std::vector<::physx::PxVec3>>& worldPoints,
    const std::vector<std::vector<::physx::PxVec3>>& normals)
{
    std::vector<std::vector<std::vector<float>>> totalPathLengths(
        receiverOrigins.size(), std::vector<std::vector<float>>(emitterOrigins.size(), std::vector<float>()));
    for (size_t i = 0; i < receiverOrigins.size(); i++)
    {
        for (size_t j = 0; j < emitterOrigins.size(); j++)
        {
            if (shouldProduceEnvelope(adjacency, isFiring, isReceiving, i, j))
            {
                totalPathLengths[i][j] =
                    getTotalPathLength(receiverOrigins[i], emitterOrigins[j], worldPoints[j], normals[j]);
            }
        }
    }
    return totalPathLengths;
}

bool UltrasonicReceiverArray::shouldProduceEnvelope(const std::vector<std::vector<uint8_t>>& adjacency,
                                                    const std::vector<bool>& isFiring,
                                                    const std::vector<bool>& isReceiving,
                                                    const size_t receiverIndex,
                                                    const size_t emitterIndex)
{

    bool isAdjacent = std::find(adjacency[receiverIndex].begin(), adjacency[receiverIndex].end(), emitterIndex) !=
                      adjacency[receiverIndex].end();

    return (isReceiving[receiverIndex] && isFiring[emitterIndex] && isAdjacent);
}


std::vector<float> UltrasonicReceiverArray::getTotalPathLength(const ::physx::PxTransform& receiverOrigin,
                                                               const ::physx::PxTransform& emitterOrigin,
                                                               const std::vector<::physx::PxVec3>& worldPoints,
                                                               const std::vector<::physx::PxVec3>& normals)
{
    const ::physx::PxTransform receiverInv = receiverOrigin.getInverse();
    const ::physx::PxTransform delta = receiverInv * emitterOrigin;
    bool isCross = delta.p.magnitude() > 1e-3f || delta.q.getAngle() > 1e-3f;

    std::vector<float> echo;
    for (size_t i = 0; i < worldPoints.size(); i++)
    {
        ::physx::PxVec3 D = worldPoints[i] - emitterOrigin.p;
        ::physx::PxVec3 V_r = receiverInv.transform(worldPoints[i]);

        if (isCross && !inFieldOfView(V_r))
        {
            // Set a value larger than 2x max range so it's ignored
            // echo.push_back(mMaxDist * 10.0f);
        }
        else
        {
            const float totalDist = (D.magnitude() + V_r.magnitude()) * mMetersPerUnit;
            echo.push_back(totalDist);
        }
    }
    return echo;
}

bool UltrasonicReceiverArray::inFieldOfView(const ::physx::PxVec3& r)
{
    const float r2NormSquared = r.x * r.x + r.y * r.y;
    const float r2Norm = sqrt(r2NormSquared);
    if (r2Norm > 0.0f && std::abs(atan2f(r.y / r2Norm, r.x / r2Norm)) > mHorizontalFov)
    {
        return false;
    }
    // CARB_LOG_WARN("Horizontal %f | %f", atan2f(r.y / r2Norm, r.x / r2Norm), mHorizontalFov);
    const float r3Norm = sqrt(r2NormSquared + r.z * r.z);
    if (r3Norm > 0.0f && std::abs(asinf(r.z / r3Norm)) > mVerticalFov)
    {
        return false;
    }
    // CARB_LOG_WARN("Vertical %f | %f", asinf(r.z / r3Norm), mVerticalFov);
    return true;
}
