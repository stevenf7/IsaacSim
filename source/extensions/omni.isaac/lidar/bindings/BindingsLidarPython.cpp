// Copyright (c) 2018-2019, NVIDIA CORPORATION.  All rights reserved.
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
        .def("get_lidar_handle", wrapInterfaceFunction(&LidarInterface::getLidarHandle))

        .def("get_horizontal_fov", wrapInterfaceFunction(&LidarInterface::getHorizontalFov))
        .def("get_vertical_fov", wrapInterfaceFunction(&LidarInterface::getVerticalFov))
        .def("get_rotation_rate", wrapInterfaceFunction(&LidarInterface::getRotationRate))
        .def("get_horizontal_resolution", wrapInterfaceFunction(&LidarInterface::getHorizontalResolution))
        .def("get_vertical_resolution", wrapInterfaceFunction(&LidarInterface::getVerticalResolution))
        .def("get_min_range", wrapInterfaceFunction(&LidarInterface::getMinRange))
        .def("get_max_range", wrapInterfaceFunction(&LidarInterface::getMaxRange))
        .def("get_high_lod", wrapInterfaceFunction(&LidarInterface::getHighLod))
        .def("get_draw_lidar_points", wrapInterfaceFunction(&LidarInterface::getDrawLidarPoints))

        .def("set_horizontal_fov", wrapInterfaceFunction(&LidarInterface::setHorizontalFov))
        .def("set_vertical_fov", wrapInterfaceFunction(&LidarInterface::setVerticalFov))
        .def("set_rotation_rate", wrapInterfaceFunction(&LidarInterface::setRotationRate))
        .def("set_horizontal_resolution", wrapInterfaceFunction(&LidarInterface::setHorizontalResolution))
        .def("set_vertical_resolution", wrapInterfaceFunction(&LidarInterface::setVerticalResolution))
        .def("set_min_range", wrapInterfaceFunction(&LidarInterface::setMinRange))
        .def("set_max_range", wrapInterfaceFunction(&LidarInterface::setMaxRange))
        .def("set_high_lod", wrapInterfaceFunction(&LidarInterface::setHighLod))
        .def("set_draw_lidar_points", wrapInterfaceFunction(&LidarInterface::setDrawLidarPoints))


        .def("get_num_cols", wrapInterfaceFunction(&LidarInterface::getNumCols))
        .def("get_num_rows", wrapInterfaceFunction(&LidarInterface::getNumRows))
        .def("get_num_cols_ticked", wrapInterfaceFunction(&LidarInterface::getNumColsTicked))

        .def("get_depth_data",
             [](const LidarInterface* li, LidarHandle handle) -> py::object {
                 if (!li)
                     return py::none();
                 uint16_t* data = li->getDepthData(handle);
                 int rows = li->getNumRows(handle);
                 int numColsTicked = li->getNumColsTicked(handle);
                 return py::array(py::buffer_info(data, sizeof(uint16_t), py::format_descriptor<uint16_t>::value, 2,
                                                  { numColsTicked, rows }, { sizeof(uint16_t) * rows, sizeof(uint16_t) }));
             })

        .def("get_intensity_data",
             [](const LidarInterface* li, LidarHandle handle) -> py::object {
                 if (!li)
                     return py::none();
                 uint8_t* data = li->getIntensityData(handle);
                 int rows = li->getNumRows(handle);
                 int numColsTicked = li->getNumColsTicked(handle);
                 return py::array(py::buffer_info(data, sizeof(uint8_t), py::format_descriptor<uint8_t>::value, 2,
                                                  { numColsTicked, rows }, { sizeof(uint8_t) * rows, sizeof(uint8_t) }));
             })

        .def("get_zenith_data",
             [](const LidarInterface* li, LidarHandle handle) -> py::object {
                 if (!li)
                     return py::none();
                 float* data = li->getZenithData(handle);
                 int rows = li->getNumRows(handle);
                 return py::array(py::buffer_info(
                     data, sizeof(float), py::format_descriptor<float>::value, 1, { rows }, { sizeof(float) }));
             })

        .def("get_azimuth_data", [](const LidarInterface* li, LidarHandle handle) -> py::object {
            if (!li)
                return py::none();
            float* data = li->getAzimuthData(handle);
            int numColsTicked = li->getNumColsTicked(handle);
            return py::array(py::buffer_info(
                data, sizeof(float), py::format_descriptor<float>::value, 1, { numColsTicked }, { sizeof(float) }));
        });
}
}
