// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/partition/IsaacPartition.h>

CARB_BINDINGS("omni.isaac.partition.python")

using namespace omni::isaac;

namespace
{
PYBIND11_MODULE(_partition, m)
{
    using namespace carb;

    m.doc() = "pybind11 omni.isaac.partition bindings";

    auto isaacPartition = defineInterfaceClass<IsaacPartition>(
        m, "IsaacPartition", "acquire_partition_interface", "release_partition_interface");

    // save_to_usd
    const char* docString = R"(
        Save partition data into USD.
    )";
    isaacPartition.def("save_to_usd", wrapInterfaceFunction(&IsaacPartition::saveToUsd), docString);

    // set_export_path
    docString = R"(
        Set the file to export.
    )";
    isaacPartition.def("set_export_path", wrapInterfaceFunction(&IsaacPartition::setExportPath), docString);

    // get_export_path
    docString = R"(
        Get the file to export.
    )";
    isaacPartition.def("get_export_path", wrapInterfaceFunction(&IsaacPartition::getExportPath), docString);

    // clear_cameras
    docString = R"(
        Clear the selected cameras.
    )";
    isaacPartition.def("clear_cameras", wrapInterfaceFunction(&IsaacPartition::clearCameras), docString);

    // add_camera_path
    docString = R"(
        Add camera path.
    )";
    isaacPartition.def("add_camera_path", wrapInterfaceFunction(&IsaacPartition::addCameraPath), docString);

    // num_cameras_paths
    docString = R"(
        Get the number of cameras to export.
    )";
    isaacPartition.def("num_camera_paths", wrapInterfaceFunction(&IsaacPartition::numCameraPaths), docString);

    // get_camera_path
    docString = R"(
        Get the number of cameras to export.
    )";
    isaacPartition.def("get_camera_path", wrapInterfaceFunction(&IsaacPartition::getCameraPath), docString);
}
} // namespace
