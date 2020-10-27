// Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
#include <omni/usd/UsdContextIncludes.h>
#include <omni/usd/UsdContext.h>
// clang-format on

#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/lidar/LidarInterface.h>
#include <pybind11/pybind11/numpy.h>

CARB_BINDINGS("omni.isaac.lidar.python")


namespace omni
{
namespace isaac
{
namespace lidar
{
// A simple point instancer that can visualize multiple lidars
class LidarVisualizer
{
public:
    LidarVisualizer(const std::string& visualizerPath, const carb::Float3& pointColor, const float pointSize = 0.1)
    {

        framework = carb::getFramework();
        if (!framework)
        {
            CARB_LOG_ERROR("*** Failed to get Carbonite framework\n");
            return;
        }

        mLidarInterface = framework->acquireInterface<omni::isaac::lidar::LidarInterface>();
        if (!mLidarInterface)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::lidar interface");
            return;
        }
        mStage = omni::usd::UsdContext::getContext()->getStage();
        pxr::VtArray<pxr::GfVec3f> colors;
        colors.push_back(pxr::GfVec3f(pointColor.x, pointColor.y, pointColor.z));
        pxr::UsdGeomCube occupiedCube = pxr::UsdGeomCube::Define(mStage, pxr::SdfPath(visualizerPath + "/cube"));
        occupiedCube.CreateDisplayColorPrimvar().Set(colors);

        mInstancer = pxr::UsdGeomPointInstancer::Define(mStage, pxr::SdfPath(visualizerPath));
        pxr::SdfPathVector mSelectedPaths;
        mSelectedPaths.push_back(pxr::SdfPath(visualizerPath + "/cube"));
        mInstancer.GetPrototypesRel().SetTargets(mSelectedPaths);
    }

    void setLidarsToVisualize(const std::vector<std::string>& lidarPaths)
    {
        mLidarPaths = lidarPaths;
    }
    // get new data from lidars and render it
    void updateVisualization()
    {
        mPositions.clear();
        mProtoIndices.clear();
        for (auto& path : mLidarPaths)
        {
            if (!mLidarInterface->isLidar(path.c_str()))
            {
                CARB_LOG_ERROR("Prim %s is not registered with Lidar extension", path.c_str());
                return;
            }
            else
            {
                carb::Float3* lidarData = mLidarInterface->getPointCloud(path.c_str());

                int rows = mLidarInterface->getNumRows(path.c_str());
                int numColsTicked = mLidarInterface->getNumColsTicked(path.c_str());
                for (int i = 0; i < rows * numColsTicked; i++)
                {


                    mPositions.push_back(pxr::GfVec3f(lidarData[i].x, lidarData[i].y, lidarData[i].z));
                    mProtoIndices.push_back(0);
                }
            }
        }
        mInstancer.GetPositionsAttr().Set(mPositions);
        mInstancer.GetProtoIndicesAttr().Set(mProtoIndices);
    }

private:
    std::vector<std::string> mLidarPaths;
    pxr::VtArray<pxr::GfVec3f> mPositions;
    pxr::VtArray<int> mProtoIndices;
    pxr::UsdGeomPointInstancer mInstancer;
    omni::isaac::lidar::LidarInterface* mLidarInterface;
    carb::Framework* framework;
    pxr::UsdStageWeakPtr mStage;
};
}
}
}


namespace
{
PYBIND11_MODULE(_lidar, m)
{
    using namespace carb;
    using namespace omni::isaac::lidar;

    m.doc() = R"pbdoc(
        This extension provides an interface to a `omni.isaac.LidarSchema.Lidar` prim defined in a stage. 
        
        Example:
            To use this interface you must first call the acquire interface function.
            It is also recommended to use the `is_lidar` function to check if a given USD path is valid
            
            ::

                import omni.isaac.lidar._lidar.acquire_lidar_interface
                lidar_interface = acquire_lidar_interface()
                if lidar_interface.is_lidar("/World/Lidar"):
                    print("lidar is valid")
        
        Refer to the sample documentation for more examples and usage
                )pbdoc";

    auto lidar_visualizer = py::class_<LidarVisualizer>(m, "LidarVisualizer")
                                .def(py::init<const std::string&, const carb::Float3&, const float>())
                                .def("set_lidars_to_visualize", &LidarVisualizer::setLidarsToVisualize)
                                .def("update_visualization", &LidarVisualizer::updateVisualization);

    defineInterfaceClass<LidarInterface>(m, "LidarInterface", "acquire_lidar_interface", "release_lidar_interface")
        .def("get_num_cols", wrapInterfaceFunction(&LidarInterface::getNumCols),
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to lidar prim as a string
                
                Returns:
                    :obj:`int`: The number of vertical scans of the lidar, 0 if error occurred)pbdoc")
        .def("get_num_rows", wrapInterfaceFunction(&LidarInterface::getNumRows),
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to lidar prim as a string
                
                Returns:
                     :obj:`int`: The number of horizontal scans of the lidar, 0 if error occurred)pbdoc")
        .def("get_num_cols_ticked", wrapInterfaceFunction(&LidarInterface::getNumColsTicked), R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to lidar prim as a string
                
                Returns:
                     :obj:`int`: The number of vertical scans the lidar completed in the last simulation step, 0 if error occurred. Generally only useful for lidars with a non-zero rotation speed)pbdoc")

        .def("get_depth_data",
             [](const LidarInterface* li, const char* lidarPath) -> py::object {
                 if (!li)
                     return py::none();
                 uint16_t* data = li->getDepthData(lidarPath);
                 int rows = li->getNumRows(lidarPath);
                 int numColsTicked = li->getNumColsTicked(lidarPath);
                 return py::array(py::buffer_info(data, sizeof(uint16_t), py::format_descriptor<uint16_t>::value, 2,
                                                  { numColsTicked, rows }, { sizeof(uint16_t) * rows, sizeof(uint16_t) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to lidar prim as a string
                
                Returns:
                :obj:`numpy.ndarray`: The distance from the lidar to the hit for each beam in uint16 and scaled by min and max distance)pbdoc")

        .def("get_linear_depth_data",
             [](const LidarInterface* li, const char* lidarPath) -> py::object {
                 if (!li)
                     return py::none();
                 float* data = li->getLinearDepthData(lidarPath);
                 int rows = li->getNumRows(lidarPath);
                 int numColsTicked = li->getNumColsTicked(lidarPath);
                 return py::array(py::buffer_info(data, sizeof(float), py::format_descriptor<float>::value, 2,
                                                  { numColsTicked, rows }, { sizeof(float) * rows, sizeof(float) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to lidar prim as a string
                
                Returns:
                :obj:`numpy.ndarray`: The distance from the lidar to the hit for each beam in meters)pbdoc")


        .def("get_intensity_data",
             [](const LidarInterface* li, const char* lidarPath) -> py::object {
                 if (!li)
                     return py::none();
                 uint8_t* data = li->getIntensityData(lidarPath);
                 int rows = li->getNumRows(lidarPath);
                 int numColsTicked = li->getNumColsTicked(lidarPath);
                 return py::array(py::buffer_info(data, sizeof(uint8_t), py::format_descriptor<uint8_t>::value, 2,
                                                  { numColsTicked, rows }, { sizeof(uint8_t) * rows, sizeof(uint8_t) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to lidar prim as a string
                
                Returns:
                :obj:`numpy.ndarray`: The observed specular intensity of each beam, 255 if hit, 0 if not)pbdoc")

        .def("get_zenith_data",
             [](const LidarInterface* li, const char* lidarPath) -> py::object {
                 if (!li)
                     return py::none();
                 float* data = li->getZenithData(lidarPath);
                 int rows = li->getNumRows(lidarPath);
                 return py::array(py::buffer_info(
                     data, sizeof(float), py::format_descriptor<float>::value, 1, { rows }, { sizeof(float) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to lidar prim as a string
                
                Returns:
                :obj:`numpy.ndarray`: The zenith angle in radians for each row)pbdoc")

        .def("get_azimuth_data",
             [](const LidarInterface* li, const char* lidarPath) -> py::object {
                 if (!li)
                     return py::none();
                 float* data = li->getAzimuthData(lidarPath);
                 int numColsTicked = li->getNumColsTicked(lidarPath);
                 return py::array(py::buffer_info(data, sizeof(float), py::format_descriptor<float>::value, 1,
                                                  { numColsTicked }, { sizeof(float) }));
             },
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to lidar prim as a string
                
                Returns:
                :obj:`numpy.ndarray`: The azimuth angle in radians for each column)pbdoc")

        .def("is_lidar", wrapInterfaceFunction(&LidarInterface::isLidar),
             R"pbdoc(
                Args: 
                    arg0 (:obj:`str`): USD path to lidar prim as a string
                
                Returns:
                :obj:`bool`: True if a lidar exists at the give path, False otherwise)pbdoc");
}
}
