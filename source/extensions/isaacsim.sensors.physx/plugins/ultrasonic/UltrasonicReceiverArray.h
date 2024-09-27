// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "USSEnvelope.h"

#include <carb/scenerenderer/SceneRendererTypes.h>

#include <foundation/PxTransform.h>
#include <foundation/PxVec3.h>

#include <vector>

class UltrasonicReceiverArray
{
public:
    std::vector<std::vector<std::vector<float>>> getAdjacentDistances(
        const std::vector<std::vector<uint8_t>>& adjacency,
        const std::vector<bool>& isFiring,
        const std::vector<bool>& isReceiving,
        const std::vector<::physx::PxTransform>& emitterOrigins,
        const std::vector<::physx::PxTransform>& receiverOrigins,
        const std::vector<std::vector<::physx::PxVec3>>& worldPoints,
        const std::vector<std::vector<::physx::PxVec3>>& normals = std::vector<std::vector<::physx::PxVec3>>());

    std::vector<std::vector<USSEnvelope>> getEnvelopeMatrix(const std::vector<std::vector<uint8_t>>& adjacency,
                                                            const std::vector<bool>& isFiring,
                                                            const std::vector<bool>& isReceiving,
                                                            const std::vector<::physx::PxTransform>& emitterOrigins,
                                                            const std::vector<::physx::PxTransform>& receiverOrigins,
                                                            const std::vector<std::vector<::physx::PxVec3>>& worldPoints,
                                                            const std::vector<std::vector<::physx::PxVec3>>& normals,
                                                            const std::vector<std::vector<::physx::PxVec4>>& worldMaterials);

    std::vector<USSEnvelope> getCombinedActiveEnvelopeList(const std::vector<std::vector<uint8_t>>& adjacency,
                                                           const std::vector<bool>& isFiring,
                                                           const std::vector<bool>& isReceiving,
                                                           const std::vector<::physx::PxTransform>& emitterOrigins,
                                                           const std::vector<::physx::PxTransform>& receiverOrigins,
                                                           const std::vector<std::vector<::physx::PxVec3>>& worldPoints);

    std::vector<USSEnvelope> getCombinedEnvelopeList(const std::vector<std::vector<uint8_t>>& adjacency,
                                                     const std::vector<bool>& isFiring,
                                                     const std::vector<bool>& isReceiving,
                                                     const std::vector<::physx::PxTransform>& emitterOrigins,
                                                     const std::vector<::physx::PxTransform>& receiverOrigins,
                                                     const std::vector<std::vector<::physx::PxVec3>>& worldPoints,
                                                     const std::vector<std::vector<::physx::PxVec3>>& normals,
                                                     const std::vector<std::vector<::physx::PxVec4>>& worldMaterials);

    bool shouldProduceEnvelope(const std::vector<std::vector<uint8_t>>& adjacency,
                               const std::vector<bool>& isFiring,
                               const std::vector<bool>& isReceiving,
                               const size_t i,
                               const size_t j);
    float mMetersPerUnit = 1.0;
    bool mUseBRDF = false;
    bool mUseUSSMaterialsForBRDF = false;
    int mNumBins = 224;
    float mMaxDist = 0.0f;
    float mHorizontalFov = 60.0f;
    float mVerticalFov = 30.0f;

    std::vector<carb::scenerenderer::PrimitiveVertex> mReceiverLines;

private:
    std::vector<float> getTotalPathLength(const ::physx::PxTransform& receiverOrigin,
                                          const ::physx::PxTransform& emitterOrigin,
                                          const std::vector<::physx::PxVec3>& worldPoints,
                                          const std::vector<::physx::PxVec3>& normals);

    bool inFieldOfView(const ::physx::PxVec3& r);

    const float invalidEnvelopeFloat = -100.1f;
};
