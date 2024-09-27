// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "UltrasonicReceiver.h"

#include <algorithm>
#include <iostream>


std::vector<float> UltrasonicReceiver::getIndirectIntensities(const ::physx::PxVec3& emitterOrigin,
                                                              const std::vector<::physx::PxVec3>& worldPoints)
{
    std::vector<float> res;
    for (size_t i = 0; i < worldPoints.size(); i++)
    {
        ::physx::PxVec3 D = worldPoints[i] - emitterOrigin;
        ::physx::PxVec3 V_r = worldPoints[i] - mReceiverOrigin;
        float DVr = D.dot(V_r);
        std::cout << "D  = " << D[0] << " " << D[1] << " " << D[2] << std::endl
                  << "V_r = " << V_r[0] << " " << V_r[1] << " " << V_r[2] << std::endl
                  << "D V_r = " << DVr << std::endl
                  << "mag(D) = " << D.magnitude() << std::endl
                  << "mag(V_r) = " << V_r.magnitude() << std::endl;
        float cosTheta = D.dot(V_r) / (D.magnitude() * V_r.magnitude());
        res.push_back(std::max(cosTheta, 0.f));
    }
    return res;
}

std::vector<float> UltrasonicReceiver::getTotalPathLength(const ::physx::PxVec3& emitterOrigin,
                                                          const std::vector<::physx::PxVec3>& worldPoints)
{

    std::vector<float> echo;
    for (size_t i = 0; i < worldPoints.size(); i++)
    {
        ::physx::PxVec3 D = worldPoints[i] - emitterOrigin;
        ::physx::PxVec3 V_r = worldPoints[i] - mReceiverOrigin;
        auto totalDist = D.magnitude() + V_r.magnitude();
        std::cout << "D  = " << D[0] << " " << D[1] << " " << D[2] << std::endl
                  << "V_r = " << V_r[0] << " " << V_r[1] << " " << V_r[2] << std::endl
                  << "mag(D) = " << D.magnitude() << std::endl
                  << "mag(V_r) = " << V_r.magnitude() << std::endl;
        echo.push_back(totalDist);
    }
    return echo;
}
