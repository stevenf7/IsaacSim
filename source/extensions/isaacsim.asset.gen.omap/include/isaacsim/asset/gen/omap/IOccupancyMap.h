// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

namespace isaacsim
{
namespace asset
{
namespace gen
{
namespace omap
{

/**
 * @brief Interface for occupancy map generation
 */
struct OccupancyMap
{
    CARB_PLUGIN_INTERFACE("isaacsim::asset::gen::omap::OccupancyMap", 0, 1);

    /**
     * @brief Generates the occupancy map
     */
    void(CARB_ABI* generateMap)();

    /**
     * @brief Updates the visualization
     */
    void(CARB_ABI* update)();

    /**
     * @brief Sets the transform for map generation
     * @param inputOrigin Origin point in world coordinates
     * @param minPoint Minimum bounds relative to origin
     * @param maxPoint Maximum bounds relative to origin
     */
    void(CARB_ABI* setTransform)(carb::Float3 inputOrigin, carb::Float3 minPoint, carb::Float3 maxPoint);

    /**
     * @brief Sets the cell size for the map
     * @param cellSize Size of each cell in meters
     */
    void(CARB_ABI* setCellSize)(float cellSize);

    /**
     * @brief Gets positions of occupied cells
     * @return Vector of 3D positions
     */
    std::vector<carb::Float3>(CARB_ABI* getOccupiedPositions)();

    /**
     * @brief Gets positions of free cells
     * @return Vector of 3D positions
     */
    std::vector<carb::Float3>(CARB_ABI* getFreePositions)();

    /**
     * @brief Gets minimum bounds of the map
     * @return Minimum bounds as Float3
     */
    carb::Float3(CARB_ABI* getMinBound)();

    /**
     * @brief Gets maximum bounds of the map
     * @return Maximum bounds as Float3
     */
    carb::Float3(CARB_ABI* getMaxBound)();

    /**
     * @brief Gets dimensions of the map in cells
     * @return Dimensions as Int3
     */
    carb::Int3(CARB_ABI* getDimensions)();

    /**
     * @brief Gets the occupancy buffer
     * @return Vector of cell values
     */
    std::vector<float>(CARB_ABI* getBuffer)();

    /**
     * @brief Gets colored byte buffer for visualization
     * @param occupied Color for occupied cells
     * @param unoccupied Color for unoccupied cells
     * @param unknown Color for unknown cells
     * @return Vector of RGBA values
     */
    std::vector<char>(CARB_ABI* getColoredByteBuffer)(const carb::Int4& occupied,
                                                      const carb::Int4& unoccupied,
                                                      const carb::Int4& unknown);
};

} // namespace omap
} // namespace gen
} // namespace asset
} // namespace isaacsim
