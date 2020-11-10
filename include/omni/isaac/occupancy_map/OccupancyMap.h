// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>


namespace omni
{
namespace isaac
{
namespace occupancy_map
{

struct OccupancyMap
{


    CARB_PLUGIN_INTERFACE("omni::isaac::occupancy_map::OccupancyMap", 0, 1);

    void(CARB_ABI* generateMap)(
        float gridResolution, float rayResolution, float minSearchDistance, float occupancyThreshold, size_t maxRays);
    void(CARB_ABI* update)();
    void(CARB_ABI* setTransform)(carb::Float3 inputOrigin, carb::Float2 minPoint, carb::Float2 maxPoint);
    std::vector<carb::Float3>(CARB_ABI* getOccupiedPositions)();
    std::vector<carb::Float3>(CARB_ABI* getFreePositions)();
    carb::Float3(CARB_ABI* getMinBound)();
    carb::Float3(CARB_ABI* getMaxBound)();
};
}
}
}
