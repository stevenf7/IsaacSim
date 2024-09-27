// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/scenerenderer/SceneRendererTypes.h>

#include <foundation/PxVec3.h>
#include <foundation/PxVec4.h>

#include <vector>

class BRDF
{
public:
    BRDF(const ::physx::PxVec3& emitterOrigin) : mEmitterOrigin(emitterOrigin)
    {
    }
    ::physx::PxVec3 getMirrorRay(const ::physx::PxVec3& normal, const ::physx::PxVec3& worldPoint) const;

    float getReturnedIntensity(const ::physx::PxVec3& receiverOrigin,
                               const ::physx::PxVec3& normal,
                               const ::physx::PxVec3& worldPoint,
                               const ::physx::PxVec4& worldMaterial,
                               const float incidentIntensity,
                               std::vector<carb::scenerenderer::PrimitiveVertex>* receiverLines = nullptr,
                               bool useUSSMaterials = false) const;

    // return an array of intensities which calls the above getReturnedIntensity
    std::vector<float> getReturnedIntensities(const ::physx::PxVec3& receiverOrigin,
                                              const std::vector<::physx::PxVec3>& normals,
                                              const std::vector<::physx::PxVec3>& worldPoints,
                                              const std::vector<::physx::PxVec4>& worldMaterials,
                                              const std::vector<float>& incidentIntensities,
                                              std::vector<carb::scenerenderer::PrimitiveVertex>* receiverLines = nullptr,
                                              bool useUSSMaterials = false) const;

private:
    ::physx::PxVec3 mEmitterOrigin;
    const float kPi = 3.141592653589f;
    const float kDegToRad = kPi / 180.0f;
    const float kRadToDeg = 180.0f / kPi;
};
