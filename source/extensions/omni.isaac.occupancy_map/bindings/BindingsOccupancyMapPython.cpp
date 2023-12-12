// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/occupancy_map/MapGenerator.h>
#include <omni/isaac/occupancy_map/OccupancyMap.h>
#include <omni/physx/IPhysx.h>
#include <pybind11/chrono.h>
#include <pybind11/functional.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>


CARB_BINDINGS("omni.isaac.occupancy_map.python")

namespace omni
{
namespace isaac
{
namespace occupancy_map
{
}
}
}


namespace
{

namespace py = pybind11;

PYBIND11_MODULE(_occupancy_map, m)
{
    using namespace carb;
    using namespace omni::isaac::occupancy_map;
    // We use carb data types, must import bindings for them
    auto carb_module = py::module::import("carb");

    m.doc() = "Isaac Sim Occupany map generator bindings";


    py::class_<MapGenerator>(m, "Generator", R"pbdoc(

        This class is used to generate an occupancy map for a USD stage. 
        Assuming the stage has collision geometry information, the following code can be used to generate the occupancy map information
        
        Example:
            
            .. highlight:: python
            .. code-block:: python

                import omni
                from omni.isaac.occupancy_map import _occupancy_map

                physx = omni.physx.acquire_physx_interface()
                stage_id = omni.usd.get_context().get_stage_id()

                generator = _occupancy_map.Generator(physx, stage_id)
                # 0.05m cell size, output buffer will have 4 for occupied cells, 5 for unoccupied, and 6 for cells that cannot be seen
                # this assumes your usd stage units are in m, and not cm
                generator.update_settings(.05, 4, 5, 6)
                # Set location to map from and the min and max bounds to map to
                generator.set_transform((0, 0, 0), (-2, -2, 0), (2, 2, 0))
                generator.generate2d()
                # Get locations of the occupied cells in the stage
                points = generator.get_occupied_positions()
                # Get computed 2d occupancy buffer
                buffer = generator.get_buffer()
                # Get dimensions for 2d buffer
                dims = generator.get_dimensions()
    
        )pbdoc")
        .def(py::init(
                 [](omni::physx::IPhysx* physXPtr, const long int stageId)
                 {
                     pxr::UsdStageWeakPtr stage =
                         pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
                     return new MapGenerator(physXPtr, stage);
                 }),
             R"pbdoc(

                 Args:
                    arg0 Pointer to PhysX interface
                    arg1 Stage ID for the USD stage to map

            )pbdoc")
        .def("update_settings", &MapGenerator::updateSettings, R"pbdoc(
                Updates settings used for generating the occupancy map

                Args:
                    arg0 (:obj:`float`): Size of the cell in stage units, resolution of the grid
                    arg1 (:obj:`float`): Value used to denote an occupied cell
                    arg2 (:obj:`float`): Value used to denote an unoccupied cell
                    arg3 (:obj:`float`): Value used to denote unknown areas that could not be reached from the starting location

            )pbdoc")
        .def("set_transform", &MapGenerator::setTransform, R"pbdoc(
                Set origin and bounds for mapping

                Args:
                    arg0 (:obj:`carb.Float3`): Origin in stage to start mapping from, must be in unoccupied space
                    arg1 (:obj:`carb.Float3`): Minimum bound to map up to
                    arg2 (:obj:`carb.Float3`): Maximum bound to map up to
        )pbdoc")
        .def("generate2d", &MapGenerator::generate2d, R"pbdoc(
                Main function that generates a map based on the settings and transform set. Assumes that a 2d map is generated and flattens the computed data
        )pbdoc")
        .def("generate3d", &MapGenerator::generate3d, R"pbdoc(
                Main function that generates a map based on the settings and transform set. Assumes 3d generation, map is not flattened
        )pbdoc")
        .def("get_occupied_positions", &MapGenerator::getOccupiedPositions, R"pbdoc(

                Returns:
                    :obj:`list` of :obj:`carb.Float3`: List of 3d points in stage coordinates from the generated map, containing occupied locations.
        )pbdoc")
        .def("get_free_positions", &MapGenerator::getFreePositions, R"pbdoc(
                Returns:
                    :obj:`list` of :obj:`carb.Float3`: List of 3d points in stage coordinates from the generated map, containing free locations.
        )pbdoc")
        .def("get_min_bound", &MapGenerator::getMinBound, R"pbdoc(
                Returns:
                    :obj:`carb.Float3`: Minimum bound for generated occupancy map instage coordinates
        )pbdoc")
        .def("get_max_bound", &MapGenerator::getMaxBound, R"pbdoc(
                Returns:
                    :obj:`carb.Float3`: Maximum bound for generated occupancy map instage coordinates
        )pbdoc")
        .def("get_dimensions", &MapGenerator::getDimensions, R"pbdoc(
                Returns:
                    :obj:`carb.Int3`: Dimensions for output buffer
        )pbdoc")
        .def("get_buffer", &MapGenerator::getBuffer, R"pbdoc(
                Returns:
                    :obj:`list` of :obj:`float`: 2D array containing values for each cell in the occupancy map. 
        )pbdoc")
        .def("get_colored_byte_buffer", &MapGenerator::getColoredByteBuffer, R"pbdoc(
                Convenience function to generate an image from the occupancy map

                Args:
                    arg0 (:obj:`carb.Int4`): RGBA Value used to denote an occupied cell
                    arg1 (:obj:`carb.Int4`): RGBA Value used to denote an unoccupied cell
                    arg2 (:obj:`carb.Int4`): RGBA Value used to denote unknown areas that could not be reached from the starting location
                Returns:
                    :obj:`list` of :obj:`int`: Flattened buffer containing list of RGBA values for each pixel. Can be used to render as image directly
        )pbdoc");


    defineInterfaceClass<OccupancyMap>(
        m, "OccupancyMap", "acquire_occupancy_map_interface", "release_occupancy_map_interface")

        .def("generate", wrapInterfaceFunction(&OccupancyMap::generateMap))
        .def("update", wrapInterfaceFunction(&OccupancyMap::update))
        .def("set_transform", wrapInterfaceFunction(&OccupancyMap::setTransform))
        .def("set_cell_size", wrapInterfaceFunction(&OccupancyMap::setCellSize))
        .def("get_occupied_positions", wrapInterfaceFunction(&OccupancyMap::getOccupiedPositions))
        .def("get_free_positions", wrapInterfaceFunction(&OccupancyMap::getFreePositions))
        .def("get_min_bound", wrapInterfaceFunction(&OccupancyMap::getMinBound))
        .def("get_max_bound", wrapInterfaceFunction(&OccupancyMap::getMaxBound))
        .def("get_dimensions", wrapInterfaceFunction(&OccupancyMap::getDimensions))
        .def("get_buffer", wrapInterfaceFunction(&OccupancyMap::getBuffer))
        .def("get_colored_byte_buffer", wrapInterfaceFunction(&OccupancyMap::getColoredByteBuffer));
}
}
