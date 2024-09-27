// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <foundation/PxVec3.h>

#include <vector>

class UltrasonicReceiver
{
public:
    UltrasonicReceiver(const ::physx::PxVec3& receiverOrigin) : mReceiverOrigin(receiverOrigin){};
    std::vector<float> getIndirectIntensities(const ::physx::PxVec3& emitterOrigin,
                                              const std::vector<::physx::PxVec3>& worldPoints);
    std::vector<float> getTotalPathLength(const ::physx::PxVec3& emitterOrigin,
                                          const std::vector<::physx::PxVec3>& worldPoints);

private:
    const ::physx::PxVec3& mReceiverOrigin;
};
