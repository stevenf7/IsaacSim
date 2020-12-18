// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// // clang-format off
// #include "UsdPCH.h"
// #include <omni/usd/UsdContextIncludes.h>
// #include <omni/usd/UsdContext.h>
// // clang-format on

#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <pybind11/pybind11/numpy.h>

CARB_BINDINGS("omni.isaac.range_sensor.python")


namespace omni
{
namespace isaac
{
namespace range_sensor
{
// // A simple point instancer that can visualize multiple range sensors
// class RangeSensorVisualizer
// {
// public:
//     RangeSensorVisualizer(const std::string& visualizerPath, const carb::Float3& pointColor, const float pointSize =
//     0.1)
//     {

//         framework = carb::getFramework();
//         if (!framework)
//         {
//             CARB_LOG_ERROR("*** Failed to get Carbonite framework\n");
//             return;
//         }

//         mRangeSensorInterface = framework->acquireInterface<omni::isaac::range_sensor::RangeSensorInterface>();
//         if (!mRangeSensorInterface)
//         {
//             CARB_LOG_ERROR("Failed to acquire omni::isaac::range_sensor interface");
//             return;
//         }
//         mStage = omni::usd::UsdContext::getContext()->getStage();
//         pxr::VtArray<pxr::GfVec3f> colors;
//         colors.push_back(pxr::GfVec3f(pointColor.x, pointColor.y, pointColor.z));
//         pxr::UsdGeomCube occupiedCube = pxr::UsdGeomCube::Define(mStage, pxr::SdfPath(visualizerPath + "/cube"));
//         occupiedCube.CreateDisplayColorPrimvar().Set(colors);

//         mInstancer = pxr::UsdGeomPointInstancer::Define(mStage, pxr::SdfPath(visualizerPath));
//         pxr::SdfPathVector mSelectedPaths;
//         mSelectedPaths.push_back(pxr::SdfPath(visualizerPath + "/cube"));
//         mInstancer.GetPrototypesRel().SetTargets(mSelectedPaths);
//     }

//     void setSensorsToVisualize(const std::vector<std::string>& sensorPaths)
//     {
//         msensorPaths = sensorPaths;
//     }
//     // get new data from sensors and render it
//     void updateVisualization()
//     {
//         mPositions.clear();
//         mProtoIndices.clear();
//         for (auto& path : msensorPaths)
//         {
//             if (!mRangeSensorInterface->isRangeSensor(path.c_str()))
//             {
//                 CARB_LOG_ERROR("Prim %s is not registered with Range Sensor extension", path.c_str());
//                 return;
//             }
//             else
//             {
//                 carb::Float3* rangeSensorData = mRangeSensorInterface->getPointCloud(path.c_str());

//                 int rows = mRangeSensorInterface->getNumRows(path.c_str());
//                 int numColsTicked = mRangeSensorInterface->getNumColsTicked(path.c_str());
//                 for (int i = 0; i < rows * numColsTicked; i++)
//                 {


//                     mPositions.push_back(pxr::GfVec3f(rangeSensorData[i].x, rangeSensorData[i].y,
//                     rangeSensorData[i].z)); mProtoIndices.push_back(0);
//                 }
//             }
//         }
//         mInstancer.GetPositionsAttr().Set(mPositions);
//         mInstancer.GetProtoIndicesAttr().Set(mProtoIndices);
//     }

// private:
//     std::vector<std::string> msensorPaths;
//     pxr::VtArray<pxr::GfVec3f> mPositions;
//     pxr::VtArray<int> mProtoIndices;
//     pxr::UsdGeomPointInstancer mInstancer;
//     omni::isaac::range_sensor::RangeSensorInterface* mRangeSensorInterface;
//     carb::Framework* framework;
//     pxr::UsdStageWeakPtr mStage;
// };
}
}
}


namespace
{
PYBIND11_MODULE(_range_sensor, m)
{
    using namespace carb;
    using namespace omni::isaac::range_sensor;

    m.doc() = R"pbdoc(
        This extension provides an interface to a `omni.isaac.RangeSensorSchemaLidar` prim defined in a stage. 
        
        Example:
            To use this interface you must first call the acquire interface function.
            It is also recommended to use the `is_range_sensor` function to check if a given USD path is valid
            
            ::

                import omni.isaac.range_sensor._range_sensor.acquire_lidar_sensor_interface
                lidar_sensor_interface = acquire_lidar_sensor_interface()
                if lidar_sensor_interface.is_lidar_sensor("/World/Lidar"):
                    print("range_sensor is valid")
        
        Refer to the sample documentation for more examples and usage
                )pbdoc";

    // auto lidar_visualizer = py::class_<LidarVisualizer>(m, "LidarVisualizer")
    //                             .def(py::init<const std::string&, const carb::Float3&, const float>())
    //                             .def("set_lidars_to_visualize", &LidarVisualizer::setLidarsToVisualize)
    //                             .def("update_visualization", &LidarVisualizer::updateVisualization);

    defineInterfaceClass<LidarSensorInterface>(
        m, "LidarSensorInterface", "acquire_lidar_sensor_interface", "release_lidar_sensor_interface")
        .def("get_num_cols", wrapInterfaceFunction(&LidarSensorInterface::getNumCols),
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                    :obj:`int`: The number of vertical scans of the sensor, 0 if error occurred)pbdoc")
        .def("get_num_rows", wrapInterfaceFunction(&LidarSensorInterface::getNumRows),
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                     :obj:`int`: The number of horizontal scans of the sensor, 0 if error occurred)pbdoc")
        .def("get_num_cols_ticked", wrapInterfaceFunction(&LidarSensorInterface::getNumColsTicked),
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                     :obj:`int`: The number of vertical scans the sensor completed in the last simulation step,
                                 0 if error occurred. Generally only useful for lidars with a non-zero rotation
                                 speed)pbdoc")

        .def("get_depth_data",
             [](const LidarSensorInterface* li, const char* sensorPath) -> py::object {
                 if (!li)
                     return py::none();
                 uint16_t* data = li->getDepthData(sensorPath);
                 int rows = li->getNumRows(sensorPath);
                 int numColsTicked = li->getNumColsTicked(sensorPath);
                 return py::array(py::buffer_info(data, sizeof(uint16_t), py::format_descriptor<uint16_t>::value, 2,
                                                  { numColsTicked, rows }, { sizeof(uint16_t) * rows, sizeof(uint16_t) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                :obj:`numpy.ndarray`: The distance from the sensor to the hit for each beam in uint16 and scaled 
                                      by min and max distance)pbdoc")

        .def("get_linear_depth_data",
             [](const LidarSensorInterface* li, const char* sensorPath) -> py::object {
                 if (!li)
                     return py::none();
                 float* data = li->getLinearDepthData(sensorPath);
                 int rows = li->getNumRows(sensorPath);
                 int numColsTicked = li->getNumColsTicked(sensorPath);
                 return py::array(py::buffer_info(data, sizeof(float), py::format_descriptor<float>::value, 2,
                                                  { numColsTicked, rows }, { sizeof(float) * rows, sizeof(float) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                :obj:`numpy.ndarray`: The distance from the sensor to the hit for each beam in meters)pbdoc")


        .def("get_intensity_data",
             [](const LidarSensorInterface* li, const char* sensorPath) -> py::object {
                 if (!li)
                     return py::none();
                 uint8_t* data = li->getIntensityData(sensorPath);
                 int rows = li->getNumRows(sensorPath);
                 int numColsTicked = li->getNumColsTicked(sensorPath);
                 return py::array(py::buffer_info(data, sizeof(uint8_t), py::format_descriptor<uint8_t>::value, 2,
                                                  { numColsTicked, rows }, { sizeof(uint8_t) * rows, sizeof(uint8_t) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                :obj:`numpy.ndarray`: The observed specular intensity of each beam, 255 if hit, 0 if not)pbdoc")

        .def("get_zenith_data",
             [](const LidarSensorInterface* li, const char* sensorPath) -> py::object {
                 if (!li)
                     return py::none();
                 float* data = li->getZenithData(sensorPath);
                 int rows = li->getNumRows(sensorPath);
                 return py::array(py::buffer_info(
                     data, sizeof(float), py::format_descriptor<float>::value, 1, { rows }, { sizeof(float) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                :obj:`numpy.ndarray`: The zenith angle in radians for each row)pbdoc")

        .def("get_azimuth_data",
             [](const LidarSensorInterface* li, const char* sensorPath) -> py::object {
                 if (!li)
                     return py::none();
                 float* data = li->getAzimuthData(sensorPath);
                 int numColsTicked = li->getNumColsTicked(sensorPath);
                 return py::array(py::buffer_info(data, sizeof(float), py::format_descriptor<float>::value, 1,
                                                  { numColsTicked }, { sizeof(float) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                :obj:`numpy.ndarray`: The azimuth angle in radians for each column)pbdoc")

        .def("is_lidar_sensor", wrapInterfaceFunction(&LidarSensorInterface::isLidarSensor),
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                :obj:`bool`: True if a sensor exists at the give path, False otherwise)pbdoc");

    defineInterfaceClass<UltrasonicSensorInterface>(
        m, "UltrasonicSensorInterface", "acquire_ultrasonic_sensor_interface", "release_ultrasonic_sensor_interface")
        .def("is_ultrasonic_sensor", wrapInterfaceFunction(&UltrasonicSensorInterface::isUSS),
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                :obj:`bool`: True if a sensor exists at the give path, False otherwise)pbdoc")
        .def("get_num_cols", wrapInterfaceFunction(&UltrasonicSensorInterface::getNumCols),
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                     :obj:`int`: The number of horizontal scans of the sensor, 0 if error occurred)pbdoc")
        .def("get_num_rows", wrapInterfaceFunction(&UltrasonicSensorInterface::getNumRows),
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                     :obj:`int`: The number of horizontal scans of the sensor, 0 if error occurred)pbdoc")
        .def("get_num_emitters", wrapInterfaceFunction(&UltrasonicSensorInterface::getNumEmitters),
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                     :obj:`int`: The number of emitters on the sensor array, 0 if error occurred)pbdoc")
        .def("get_depth_data",
             [](const UltrasonicSensorInterface* ul, const char* sensorPath, int emitterIndex) -> py::object {
                 if (!ul)
                     return py::none();
                 uint16_t* data = ul->getDepthData(sensorPath, emitterIndex);
                 int rows = ul->getNumRows(sensorPath);
                 int cols = ul->getNumCols(sensorPath);
                 return py::array(py::buffer_info(data, sizeof(uint16_t), py::format_descriptor<uint16_t>::value, 2,
                                                  { cols, rows }, { sizeof(uint16_t) * rows, sizeof(uint16_t) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                :obj:`numpy.ndarray`: The distance from the sensor to the hit for each beam in uint16 and
                                      scaled by min and max distance)pbdoc")
        .def("get_linear_depth_data",
             [](const UltrasonicSensorInterface* ul, const char* sensorPath, int emitterIndex) -> py::object {
                 if (!ul)
                     return py::none();
                 float* data = ul->getLinearDepthData(sensorPath, emitterIndex);
                 int rows = ul->getNumRows(sensorPath);
                 int numColsTicked = ul->getNumCols(sensorPath);
                 return py::array(py::buffer_info(data, sizeof(float), py::format_descriptor<float>::value, 2,
                                                  { numColsTicked, rows }, { sizeof(float) * rows, sizeof(float) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                :obj:`numpy.ndarray`: The distance from the sensor to the hit for each beam in meters)pbdoc")


        .def("get_intensity_data",
             [](const UltrasonicSensorInterface* ul, const char* sensorPath, int emitterIndex) -> py::object {
                 if (!ul)
                     return py::none();
                 uint8_t* data = ul->getIntensityData(sensorPath, emitterIndex);
                 int rows = ul->getNumRows(sensorPath);
                 int numColsTicked = ul->getNumCols(sensorPath);
                 return py::array(py::buffer_info(data, sizeof(uint8_t), py::format_descriptor<uint8_t>::value, 2,
                                                  { numColsTicked, rows }, { sizeof(uint8_t) * rows, sizeof(uint8_t) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                :obj:`numpy.ndarray`: The observed specular intensity of each beam, 255 if hit, 0 if not)pbdoc")

        .def("get_zenith_data",
             [](const UltrasonicSensorInterface* ul, const char* sensorPath) -> py::object {
                 if (!ul)
                     return py::none();
                 float* data = ul->getZenithData(sensorPath);
                 int rows = ul->getNumRows(sensorPath);
                 return py::array(py::buffer_info(
                     data, sizeof(float), py::format_descriptor<float>::value, 1, { rows }, { sizeof(float) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                :obj:`numpy.ndarray`: The zenith angle in radians for each row)pbdoc")

        .def("get_azimuth_data",
             [](const UltrasonicSensorInterface* ul, const char* sensorPath) -> py::object {
                 if (!ul)
                     return py::none();
                 float* data = ul->getAzimuthData(sensorPath);
                 int numCols = ul->getNumCols(sensorPath);
                 std::stringstream ss;
                 ss << "numCols " << numCols;
                 CARB_LOG_WARN(ss.str().c_str());
                 return py::array(py::buffer_info(
                     data, sizeof(float), py::format_descriptor<float>::value, 1, { numCols }, { sizeof(float) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                :obj:`numpy.ndarray`: The azimuth angle in radians for each column)pbdoc");

    defineInterfaceClass<RadarSensorInterface>(
        m, "RadarSensorInterface", "acquire_radar_sensor_interface", "release_radar_sensor_interface")
        .def("is_radar_sensor", wrapInterfaceFunction(&RadarSensorInterface::isRadarSensor),
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to sensor as a string
                
                Returns:
                :obj:`bool`: True if a sensor exists at the give path, False otherwise)pbdoc");
}
}
