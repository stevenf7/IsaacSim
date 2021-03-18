#pragma once

#include "USSEnvelope.h"

#include <foundation/PxVec3.h>

#include <vector>

class UltrasonicReceiverArray
{
public:
    std::vector<std::vector<std::vector<float>>> getAdjacentDistances(
        const std::vector<std::vector<uint8_t>>& adjacency,
        const std::vector<bool>& isFiring,
        const std::vector<bool>& isReceiving,
        const std::vector<::physx::PxVec3>& emitterOrigins,
        const std::vector<::physx::PxVec3>& receiverOrigins,
        const std::vector<std::vector<::physx::PxVec3>>& worldPoints);

    std::vector<std::vector<USSEnvelope>> getEnvelopeMatrix(const std::vector<std::vector<uint8_t>>& adjacency,
                                                            const std::vector<bool>& isFiring,
                                                            const std::vector<bool>& isReceiving,
                                                            const std::vector<::physx::PxVec3>& emitterOrigins,
                                                            const std::vector<::physx::PxVec3>& receiverOrigins,
                                                            const std::vector<std::vector<::physx::PxVec3>>& worldPoints,
                                                            const std::vector<std::vector<::physx::PxVec3>>& normals);

    std::vector<USSEnvelope> getCombinedActiveEnvelopeList(const std::vector<std::vector<uint8_t>>& adjacency,
                                                           const std::vector<bool>& isFiring,
                                                           const std::vector<bool>& isReceiving,
                                                           const std::vector<::physx::PxVec3>& emitterOrigins,
                                                           const std::vector<::physx::PxVec3>& receiverOrigins,
                                                           const std::vector<std::vector<::physx::PxVec3>>& worldPoints);

    std::vector<USSEnvelope> getCombinedEnvelopeList(const std::vector<std::vector<uint8_t>>& adjacency,
                                                     const std::vector<bool>& isFiring,
                                                     const std::vector<bool>& isReceiving,
                                                     const std::vector<::physx::PxVec3>& emitterOrigins,
                                                     const std::vector<::physx::PxVec3>& receiverOrigins,
                                                     const std::vector<std::vector<::physx::PxVec3>>& worldPoints,
                                                     const std::vector<std::vector<::physx::PxVec3>>& normals);

    bool shouldProduceEnvelope(const std::vector<std::vector<uint8_t>>& adjacency,
                               const std::vector<bool>& isFiring,
                               const std::vector<bool>& isReceiving,
                               const size_t i,
                               const size_t j);
    float mMetersPerUnit = 1.0;
    bool mUseBRDF = false;
    int mNumBins = 224;
    float mMaxDist = 0.0f;

private:
    std::vector<float> getTotalPathLength(const ::physx::PxVec3& receiverOrigin,
                                          const ::physx::PxVec3& emitterOrigin,
                                          const std::vector<::physx::PxVec3>& worldPoints);
    const float invalidEnvelopeFloat = -100.1f;
};
