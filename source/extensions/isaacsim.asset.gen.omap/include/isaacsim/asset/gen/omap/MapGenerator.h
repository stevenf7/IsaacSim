// Copyright (c) 2021-2025, NVIDIA CORPORATION. All rights reserved.
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
 * @brief Generator class for creating occupancy maps from USD stages
 */
class DllExport MapGenerator
{
public:
    /**
     * @brief Constructs a new MapGenerator
     * @param physx Pointer to PhysX interface
     * @param stage Pointer to USD stage
     */
    MapGenerator(omni::physx::IPhysx* physx, pxr::UsdStageWeakPtr stage);
    ~MapGenerator();

    /**
     * @brief Updates the generator settings
     * @param cellSize Size of each cell in meters
     * @param occupiedValue Value for occupied cells
     * @param unoccupiedValue Value for unoccupied cells
     * @param unknownValue Value for unknown cells
     */
    void updateSettings(float cellSize, float occupiedValue, float unoccupiedValue, float unknownValue);

    /**
     * @brief Sets the transform for map generation
     * @param inputOrigin Origin point in world coordinates
     * @param minPoint Minimum bounds relative to origin
     * @param maxPoint Maximum bounds relative to origin
     */
    void setTransform(carb::Float3 inputOrigin, carb::Float3 minPoint, carb::Float3 maxPoint);

    /**
     * @brief Generates a 2D occupancy map
     */
    void generate2d();

    /**
     * @brief Generates a 3D occupancy map
     */
    void generate3d();

    /**
     * @brief Gets positions of occupied cells
     * @return Vector of 3D positions
     */
    std::vector<carb::Float3> getOccupiedPositions();

    /**
     * @brief Gets positions of free cells
     * @return Vector of 3D positions
     */
    std::vector<carb::Float3> getFreePositions();

    /**
     * @brief Gets minimum bounds of the map
     * @return Minimum bounds as Float3
     */
    carb::Float3 getMinBound();

    /**
     * @brief Gets maximum bounds of the map
     * @return Maximum bounds as Float3
     */
    carb::Float3 getMaxBound();

    /**
     * @brief Gets dimensions of the map in cells
     * @return Dimensions as Int3
     */
    carb::Int3 getDimensions();

    /**
     * @brief Gets the occupancy buffer
     * @return Vector of cell values
     */
    std::vector<float> getBuffer();

    /**
     * @brief Gets colored byte buffer for visualization
     * @param occupied Color for occupied cells
     * @param unoccupied Color for unoccupied cells
     * @param unknown Color for unknown cells
     * @return Vector of RGBA values
     */
    std::vector<char> getColoredByteBuffer(const carb::Int4& occupied,
                                           const carb::Int4& unoccupied,
                                           const carb::Int4& unknown);

private:
    float m_cellSize = 0.05f;
    omni::physx::IPhysx* m_physx = nullptr;
    pxr::UsdStageWeakPtr m_stage = nullptr;
    pxr::UsdPrim m_parentPrim;
    octomap::OcTree* m_tree = nullptr;
    ::physx::PxScene* m_physxScenePtr = nullptr;
    carb::Float3 m_inputOrigin;
    carb::Float3 m_inputMinPoint;
    carb::Float3 m_inputMaxPoint;
    float m_occupiedValue = 1.0f;
    float m_unoccupiedValue = 0.0f;
    float m_unknownValue = 0.5f;
};

}
}
}
}
