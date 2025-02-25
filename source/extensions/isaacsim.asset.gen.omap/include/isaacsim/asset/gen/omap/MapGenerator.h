// Copyright (c) 2021-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <carb/Defines.h>
#include <carb/Types.h>
#if defined(_WIN32)
#    include <PxPhysicsAPI.h>
#else
#    pragma GCC diagnostic push
#    pragma GCC diagnostic ignored "-Wpragmas"
#    include <PxPhysicsAPI.h>
#    pragma GCC diagnostic pop
#endif

namespace octomap
{
class OcTree;
}

namespace physx
{
class PxShape;
class PxRigidStatic;
class PxMaterial;
class PxScene;
}

namespace omni
{
namespace physx
{
class IPhysx;
}
}
namespace isaacsim
{
namespace asset
{
namespace gen
{
namespace omap
{
#ifdef _MSC_VER
#    if OMGENERATOREXPORT
#        define DllExport __declspec(dllexport)
#    else
#        define DllExport __declspec(dllimport)
#    endif
#else
#    define DllExport
#endif

/**
 * @class MapGenerator
 * @brief Generator class for creating 2D and 3D occupancy maps from USD stages
 * @details
 * The MapGenerator class provides functionality to generate occupancy maps from USD stage data.
 * It supports both 2D and 3D map generation with configurable cell sizes and occupancy values.
 * The generator uses PhysX for collision detection and octomap for spatial representation.
 *
 * @note This class requires valid PhysX and USD stage pointers to function properly
 */
class DllExport MapGenerator
{
public:
    /**
     * @brief Constructs a new MapGenerator instance
     * @details Initializes the generator with PhysX interface and USD stage references
     *
     * @param[in] physx Pointer to the PhysX interface for collision detection
     * @param[in] stage Pointer to the USD stage containing the scene geometry
     *
     * @pre physx pointer must be valid and initialized
     * @pre stage must be a valid USD stage
     */
    MapGenerator(omni::physx::IPhysx* physx, pxr::UsdStageWeakPtr stage);

    /**
     * @brief Destructor for MapGenerator
     */
    ~MapGenerator();

    /**
     * @brief Updates the generator's occupancy map settings
     * @details Configures the cell size and values used for different occupancy states
     *
     * @param[in] cellSize Size of each occupancy grid cell in meters
     * @param[in] occupiedValue Numerical value assigned to occupied cells
     * @param[in] unoccupiedValue Numerical value assigned to unoccupied cells
     * @param[in] unknownValue Numerical value assigned to cells with unknown occupancy
     *
     * @pre cellSize must be positive
     */
    void updateSettings(float cellSize, float occupiedValue, float unoccupiedValue, float unknownValue);

    /**
     * @brief Sets the transformation parameters for map generation
     * @details Defines the origin and bounds of the area to be mapped
     *
     * @param[in] inputOrigin Origin point in world coordinates
     * @param[in] minPoint Minimum bounds relative to origin
     * @param[in] maxPoint Maximum bounds relative to origin
     *
     * @pre minPoint components must be less than maxPoint components
     */
    void setTransform(carb::Float3 inputOrigin, carb::Float3 minPoint, carb::Float3 maxPoint);

    /**
     * @brief Generates a 2D occupancy map
     * @details Creates a 2D projection of the scene's occupancy
     */
    void generate2d();

    /**
     * @brief Generates a 3D occupancy map
     * @details Creates a full 3D volumetric representation of the scene's occupancy
     */
    void generate3d();

    /**
     * @brief Retrieves positions of all occupied cells
     * @return Vector of 3D positions for occupied cells
     */
    std::vector<carb::Float3> getOccupiedPositions();

    /**
     * @brief Retrieves positions of all free (unoccupied) cells
     * @return Vector of 3D positions for free cells
     */
    std::vector<carb::Float3> getFreePositions();

    /**
     * @brief Gets the minimum boundary point of the map
     * @return Minimum boundary coordinates as Float3
     */
    carb::Float3 getMinBound();

    /**
     * @brief Gets the maximum boundary point of the map
     * @return Maximum boundary coordinates as Float3
     */
    carb::Float3 getMaxBound();

    /**
     * @brief Gets the dimensions of the map in cell units
     * @return Number of cells in each dimension as Int3
     */
    carb::Int3 getDimensions();

    /**
     * @brief Retrieves the raw occupancy buffer
     * @return Vector of occupancy values for all cells
     */
    std::vector<float> getBuffer();

    /**
     * @brief Generates a colored visualization buffer
     * @details Creates an RGBA buffer for visualization purposes
     *
     * @param[in] occupied Color for occupied cells (RGBA)
     * @param[in] unoccupied Color for unoccupied cells (RGBA)
     * @param[in] unknown Color for unknown cells (RGBA)
     * @return Vector of bytes representing RGBA values
     */
    std::vector<char> getColoredByteBuffer(const carb::Int4& occupied,
                                           const carb::Int4& unoccupied,
                                           const carb::Int4& unknown);

private:
    /**
     * @brief Cell size in meters
     */
    float m_cellSize = 0.05f;

    /**
     * @brief Pointer to PhysX interface
     */
    omni::physx::IPhysx* m_physx = nullptr;

    /**
     * @brief Weak pointer to USD stage
     */
    pxr::UsdStageWeakPtr m_stage = nullptr;

    /**
     * @brief Parent USD primitive
     */
    pxr::UsdPrim m_parentPrim;

    /**
     * @brief Pointer to octomap tree structure
     */
    octomap::OcTree* m_tree = nullptr;

    /**
     * @brief Pointer to PhysX scene
     */
    ::physx::PxScene* m_physxScenePtr = nullptr;

    /**
     * @brief Origin point for map generation
     */
    carb::Float3 m_inputOrigin;

    /**
     * @brief Minimum point relative to origin
     */
    carb::Float3 m_inputMinPoint;

    /**
     * @brief Maximum point relative to origin
     */
    carb::Float3 m_inputMaxPoint;

    /**
     * @brief Value assigned to occupied cells
     */
    float m_occupiedValue = 1.0f;

    /**
     * @brief Value assigned to unoccupied cells
     */
    float m_unoccupiedValue = 0.0f;

    /**
     * @brief Value assigned to unknown cells
     */
    float m_unknownValue = 0.5f;
};

}
}
}
}
