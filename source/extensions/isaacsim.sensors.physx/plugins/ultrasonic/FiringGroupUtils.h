// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <pxr/base/gf/vec2i.h>
#include <pxr/usd/usd/inherits.h>

#include <sstream>
#include <vector>

namespace isaacsim
{
namespace sensors
{
namespace physx
{

std::vector<::physx::PxTransform> extractOrigins(std::vector<std::unique_ptr<UltrasonicEmitter>>& emitters)
{
    std::vector<::physx::PxTransform> adjacency;
    for (size_t i = 0; i < emitters.size(); i++)
    {
        adjacency.push_back(emitters[i]->getPose());
    }
    return adjacency;
}

std::vector<std::vector<uint8_t>> extractAdjacencyVectors(std::vector<std::unique_ptr<UltrasonicEmitter>>& emitters)
{
    std::vector<std::vector<uint8_t>> adjacency(emitters.size());
    for (size_t i = 0; i < emitters.size(); i++)
    {
        for (size_t j = 0; j < emitters[i]->mAdjacencyList.size(); j++)
        {
            if ((emitters[i]->mAdjacencyList[j] >= 0) &&
                (static_cast<size_t>(emitters[i]->mAdjacencyList[j]) < emitters.size()))
            {
                adjacency[i].push_back(static_cast<uint8_t>(emitters[i]->mAdjacencyList[j]));
            }
            else
            {
                printf("Adjacency list contained an emitter that does not exist: %d\n", emitters[i]->mAdjacencyList[j]);
            }
        }
    }
    return adjacency;
}


// List of (emitter index, firing mode) pairs for each sensor in this group to emit from
std::vector<bool> modesToBooleanVector(const pxr::VtArray<pxr::GfVec2i>& modes,
                                       const size_t current_mode,
                                       const size_t num_emitters)
{
    std::vector<bool> modeVector(modes.size(), false);
    for (size_t i = 0; i < modes.size(); i++)
    {
        if (static_cast<size_t>(modes[i][1]) == current_mode)
        {
            if ((static_cast<size_t>(modes[i][0]) >= 0) && (static_cast<size_t>(modes[i][0]) < num_emitters))
            {
                // modes[i][0] is the emitter/receiver index
                modeVector[modes[i][0]] = true;
            }
            else
            {
                std::stringstream errMsg;
                errMsg << "Mode contained an emitter that does not exist: (" << modes[i][0] << ", " << modes[i][1]
                       << ")" << std::endl;
                throw std::out_of_range(errMsg.str());
            }
        }
    }
    return modeVector;
}


}
}
}
