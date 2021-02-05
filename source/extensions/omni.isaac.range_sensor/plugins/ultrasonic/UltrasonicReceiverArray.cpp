#include "UltrasonicReceiverArray.h"

#include <algorithm>
#include <iostream>
#include <utility>
#include <vector>


// produce the vector of combined envelopes, one for each receiver
std::vector<USSEnvelope> UltrasonicReceiverArray::getCombinedEnvelopeList(
    const int numBins,
    const float maxDist,
    const std::vector<std::vector<uint8_t>>& adjacency,
    const std::vector<bool>& isFiring,
    const std::vector<bool>& isReceiving,
    const std::vector<::physx::PxVec3>& emitterOrigins,
    const std::vector<::physx::PxVec3>& receiverOrigins,
    const std::vector<std::vector<::physx::PxVec3>>& worldPoints)
{
    std::vector<std::vector<USSEnvelope>> envelopeMatrix = getEnvelopeMatrix(
        numBins, maxDist, adjacency, isFiring, isReceiving, emitterOrigins, receiverOrigins, worldPoints);
    std::vector<USSEnvelope> envelopeList(receiverOrigins.size(), USSEnvelope(numBins, maxDist));
    for (size_t i = 0; i < envelopeMatrix.size(); i++)
    {
        for (size_t j = 0; j < envelopeMatrix[i].size(); j++)
        {
            envelopeList[i] = envelopeList[i] + envelopeMatrix[i][j];
        }
    }
    return envelopeList;
}

// produce the 2d vector of envelopes where the first index represents the
// receiver index and the second index represents the emitter index
std::vector<std::vector<USSEnvelope>> UltrasonicReceiverArray::getEnvelopeMatrix(
    const int numBins,
    const float maxDist,
    const std::vector<std::vector<uint8_t>>& adjacency,
    const std::vector<bool>& isFiring,
    const std::vector<bool>& isReceiving,
    const std::vector<::physx::PxVec3>& emitterOrigins,
    const std::vector<::physx::PxVec3>& receiverOrigins,
    const std::vector<std::vector<::physx::PxVec3>>& worldPoints)
{
    std::vector<std::vector<USSEnvelope>> envelopeMatrix(
        receiverOrigins.size(), std::vector<USSEnvelope>(emitterOrigins.size(), USSEnvelope(numBins, maxDist)));
    auto totalPathLengths =
        getAdjacentDistances(adjacency, isFiring, isReceiving, emitterOrigins, receiverOrigins, worldPoints);
    for (size_t i = 0; i < totalPathLengths.size(); i++)
    {
        for (size_t j = 0; j < totalPathLengths[i].size(); j++)
        {
            // no attenuation of intensity based on angle, for now
            std::vector<float> intensities(totalPathLengths[i][j].size(), 1.f);
            envelopeMatrix[i][j].updateEnvelope(totalPathLengths[i][j], intensities);
        }
    }
    return envelopeMatrix;
}

std::vector<std::vector<std::vector<float>>> UltrasonicReceiverArray::getAdjacentDistances(
    const std::vector<std::vector<uint8_t>>& adjacency,
    const std::vector<bool>& isFiring,
    const std::vector<bool>& isReceiving,
    const std::vector<::physx::PxVec3>& emitterOrigins,
    const std::vector<::physx::PxVec3>& receiverOrigins,
    const std::vector<std::vector<::physx::PxVec3>>& worldPoints)
{
    std::vector<std::vector<std::vector<float>>> totalPathLengths(
        receiverOrigins.size(), std::vector<std::vector<float>>(emitterOrigins.size(), std::vector<float>()));
    for (size_t i = 0; i < receiverOrigins.size(); i++)
    {
        for (size_t j = 0; j < emitterOrigins.size(); j++)
        {
            if (shouldProduceEnvelope(adjacency, isFiring, isReceiving, i, j))
            {
                totalPathLengths[i][j] = getTotalPathLength(receiverOrigins[i], emitterOrigins[j], worldPoints[j]);
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

    /*std::cout << "receiverIndex = " << receiverIndex << std::endl;
    std::cout << "emitterIndex = " << emitterIndex << std::endl;
    std::cout << "isAdjacent = " << isAdjacent << std::endl;
    std::cout << "isReceiving[receiverIndex] = " << isReceiving[receiverIndex] << std::endl;
    std::cout << "isFiring[emitterIndex] = " << isFiring[emitterIndex] << std::endl;*/
    return (isReceiving[receiverIndex] && isFiring[emitterIndex] && isAdjacent);
}


std::vector<float> UltrasonicReceiverArray::getTotalPathLength(const ::physx::PxVec3& receiverOrigin,
                                                               const ::physx::PxVec3& emitterOrigin,
                                                               const std::vector<::physx::PxVec3>& worldPoints)
{

    std::vector<float> echo;
    for (size_t i = 0; i < worldPoints.size(); i++)
    {
        ::physx::PxVec3 D = worldPoints[i] - emitterOrigin;
        ::physx::PxVec3 V_r = worldPoints[i] - receiverOrigin;
        auto totalDist = D.magnitude() + V_r.magnitude();
        /*
        std::cout << "D  = " << D[0] << " " << D[1] << " " << D[2] << std::endl
                  << "V_r = " << V_r[0] << " " << V_r[1] << " " << V_r[2] << std::endl
                  << "mag(D) = " << D.magnitude() << std::endl
                  << "mag(V_r) = " << V_r.magnitude() << std::endl;*/
        echo.push_back(totalDist);
    }
    return echo;
}
