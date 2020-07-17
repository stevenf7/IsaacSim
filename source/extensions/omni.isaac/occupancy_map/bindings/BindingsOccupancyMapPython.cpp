// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/occupancy_map/OccupancyMap.h>
#include <pybind11/pybind11/chrono.h>
#include <pybind11/pybind11/functional.h>
#include <pybind11/pybind11/pybind11.h>
#include <pybind11/pybind11/stl.h>

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

    m.doc() = "Isaac motion planning bindings";

    defineInterfaceClass<OccupancyMap>(
        m, "OccupancyMap", "acquire_occupancy_map_interface", "release_occupancy_map_interface")

        .def("generateMap", wrapInterfaceFunction(&OccupancyMap::generateMap))
        .def("getOccupiedPositions", wrapInterfaceFunction(&OccupancyMap::getOccupiedPositions))
        .def("getFreePositions", wrapInterfaceFunction(&OccupancyMap::getFreePositions))
        .def("getMinBound", wrapInterfaceFunction(&OccupancyMap::getMinBound))
        .def("getMaxBound", wrapInterfaceFunction(&OccupancyMap::getMaxBound));
}
}
