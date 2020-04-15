// Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/lidar/LidarInterface.h>
#include <pybind11/pybind11/numpy.h>

CARB_BINDINGS("omni.isaac.lidar.python")

namespace
{
PYBIND11_MODULE(_lidar, m)
{
    using namespace carb;
    using namespace omni::isaac::lidar;

    m.doc() = "Isaac Lidar bindings";

    defineInterfaceClass<LidarInterface>(m, "LidarInterface", "acquire_lidar_interface", "release_lidar_interface")
        .def("get_num_cols", wrapInterfaceFunction(&LidarInterface::getNumCols))
        .def("get_num_rows", wrapInterfaceFunction(&LidarInterface::getNumRows))
        .def("get_num_cols_ticked", wrapInterfaceFunction(&LidarInterface::getNumColsTicked))

        .def("get_depth_data",
             [](const LidarInterface* li, const char* lidarPath) -> py::object {
                 if (!li)
                     return py::none();
                 uint16_t* data = li->getDepthData(lidarPath);
                 int rows = li->getNumRows(lidarPath);
                 int numColsTicked = li->getNumColsTicked(lidarPath);
                 return py::array(py::buffer_info(data, sizeof(uint16_t), py::format_descriptor<uint16_t>::value, 2,
                                                  { numColsTicked, rows }, { sizeof(uint16_t) * rows, sizeof(uint16_t) }));
             })

        .def("get_intensity_data",
             [](const LidarInterface* li, const char* lidarPath) -> py::object {
                 if (!li)
                     return py::none();
                 uint8_t* data = li->getIntensityData(lidarPath);
                 int rows = li->getNumRows(lidarPath);
                 int numColsTicked = li->getNumColsTicked(lidarPath);
                 return py::array(py::buffer_info(data, sizeof(uint8_t), py::format_descriptor<uint8_t>::value, 2,
                                                  { numColsTicked, rows }, { sizeof(uint8_t) * rows, sizeof(uint8_t) }));
             })

        .def("get_zenith_data",
             [](const LidarInterface* li, const char* lidarPath) -> py::object {
                 if (!li)
                     return py::none();
                 float* data = li->getZenithData(lidarPath);
                 int rows = li->getNumRows(lidarPath);
                 return py::array(py::buffer_info(
                     data, sizeof(float), py::format_descriptor<float>::value, 1, { rows }, { sizeof(float) }));
             })

        .def("get_azimuth_data",
             [](const LidarInterface* li, const char* lidarPath) -> py::object {
                 if (!li)
                     return py::none();
                 float* data = li->getAzimuthData(lidarPath);
                 int numColsTicked = li->getNumColsTicked(lidarPath);
                 return py::array(py::buffer_info(data, sizeof(float), py::format_descriptor<float>::value, 1,
                                                  { numColsTicked }, { sizeof(float) }));
             })

        .def("is_lidar", wrapInterfaceFunction(&LidarInterface::isLidar));
}
}
