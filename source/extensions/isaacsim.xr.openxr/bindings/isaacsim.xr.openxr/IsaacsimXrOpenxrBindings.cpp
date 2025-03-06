// Copyright (c) 2024-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsPythonUtils.h>

#include <isaacsim/xr/openxr/IOpenXR.h>
#include <openxr/openxr.h>
#include <openxr/openxr_platform.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>


CARB_BINDINGS("isaacsim.xr.openxr.python")

namespace
{

PYBIND11_MODULE(_openxr, m)
{
    using namespace isaacsim::xr::openxr;

    m.doc() = "pybind11 isaacsim.xr.openxr.pybind bindings";

    py::enum_<XrHandEXT>(m, "XrHandEXT")
        .value("XR_HAND_LEFT_EXT", XR_HAND_LEFT_EXT)
        .value("XR_HAND_RIGHT_EXT", XR_HAND_RIGHT_EXT);

    py::enum_<XrHandJointEXT>(m, "HandJointEXT")
        .value("XR_HAND_JOINT_PALM_EXT", XR_HAND_JOINT_PALM_EXT)
        .value("XR_HAND_JOINT_WRIST_EXT", XR_HAND_JOINT_WRIST_EXT)
        .value("XR_HAND_JOINT_THUMB_METACARPAL_EXT", XR_HAND_JOINT_THUMB_METACARPAL_EXT)
        .value("XR_HAND_JOINT_THUMB_PROXIMAL_EXT", XR_HAND_JOINT_THUMB_PROXIMAL_EXT)
        .value("XR_HAND_JOINT_THUMB_DISTAL_EXT", XR_HAND_JOINT_THUMB_DISTAL_EXT)
        .value("XR_HAND_JOINT_THUMB_TIP_EXT", XR_HAND_JOINT_THUMB_TIP_EXT)
        .value("XR_HAND_JOINT_INDEX_METACARPAL_EXT", XR_HAND_JOINT_INDEX_METACARPAL_EXT)
        .value("XR_HAND_JOINT_INDEX_PROXIMAL_EXT", XR_HAND_JOINT_INDEX_PROXIMAL_EXT)
        .value("XR_HAND_JOINT_INDEX_INTERMEDIATE_EXT", XR_HAND_JOINT_INDEX_INTERMEDIATE_EXT)
        .value("XR_HAND_JOINT_INDEX_DISTAL_EXT", XR_HAND_JOINT_INDEX_DISTAL_EXT)
        .value("XR_HAND_JOINT_INDEX_TIP_EXT", XR_HAND_JOINT_INDEX_TIP_EXT)
        .value("XR_HAND_JOINT_MIDDLE_METACARPAL_EXT", XR_HAND_JOINT_MIDDLE_METACARPAL_EXT)
        .value("XR_HAND_JOINT_MIDDLE_PROXIMAL_EXT", XR_HAND_JOINT_MIDDLE_PROXIMAL_EXT)
        .value("XR_HAND_JOINT_MIDDLE_INTERMEDIATE_EXT", XR_HAND_JOINT_MIDDLE_INTERMEDIATE_EXT)
        .value("XR_HAND_JOINT_MIDDLE_DISTAL_EXT", XR_HAND_JOINT_MIDDLE_DISTAL_EXT)
        .value("XR_HAND_JOINT_MIDDLE_TIP_EXT", XR_HAND_JOINT_MIDDLE_TIP_EXT)
        .value("XR_HAND_JOINT_RING_METACARPAL_EXT", XR_HAND_JOINT_RING_METACARPAL_EXT)
        .value("XR_HAND_JOINT_RING_PROXIMAL_EXT", XR_HAND_JOINT_RING_PROXIMAL_EXT)
        .value("XR_HAND_JOINT_RING_INTERMEDIATE_EXT", XR_HAND_JOINT_RING_INTERMEDIATE_EXT)
        .value("XR_HAND_JOINT_RING_DISTAL_EXT", XR_HAND_JOINT_RING_DISTAL_EXT)
        .value("XR_HAND_JOINT_RING_TIP_EXT", XR_HAND_JOINT_RING_TIP_EXT)
        .value("XR_HAND_JOINT_LITTLE_METACARPAL_EXT", XR_HAND_JOINT_LITTLE_METACARPAL_EXT)
        .value("XR_HAND_JOINT_LITTLE_PROXIMAL_EXT", XR_HAND_JOINT_LITTLE_PROXIMAL_EXT)
        .value("XR_HAND_JOINT_LITTLE_INTERMEDIATE_EXT", XR_HAND_JOINT_LITTLE_INTERMEDIATE_EXT)
        .value("XR_HAND_JOINT_LITTLE_DISTAL_EXT", XR_HAND_JOINT_LITTLE_DISTAL_EXT)
        .value("XR_HAND_JOINT_LITTLE_TIP_EXT", XR_HAND_JOINT_LITTLE_TIP_EXT);

    py::class_<XrQuaternionf>(m, "XrQuaternionf", py::buffer_protocol())
        .def_readwrite("x", &XrQuaternionf::x)
        .def_readwrite("y", &XrQuaternionf::y)
        .def_readwrite("z", &XrQuaternionf::z)
        .def_readwrite("w", &XrQuaternionf::w)
        .def_buffer(
            [](XrQuaternionf& quaternion)
            {
                return py::buffer_info(
                    &quaternion.x, sizeof(float), py::format_descriptor<float>::format(), 4, { 4 }, { sizeof(float) });
            });

    py::class_<XrVector3f>(m, "XrVector3f", py::buffer_protocol())
        .def_readwrite("x", &XrVector3f::x)
        .def_readwrite("y", &XrVector3f::y)
        .def_readwrite("z", &XrVector3f::z)
        .def_buffer(
            [](XrVector3f& vector)
            {
                return py::buffer_info(
                    &vector.x, sizeof(float), py::format_descriptor<float>::format(), 3, { 3 }, { sizeof(float) });
            });

    m.attr("XR_SPACE_LOCATION_ORIENTATION_VALID_BIT") = static_cast<uint64_t>(0x00000001);
    m.attr("XR_SPACE_LOCATION_POSITION_VALID_BIT") = static_cast<uint64_t>(0x00000002);
    m.attr("XR_SPACE_LOCATION_ORIENTATION_TRACKED_BIT") = static_cast<uint64_t>(0x00000004);
    m.attr("XR_SPACE_LOCATION_POSITION_TRACKED_BIT") = static_cast<uint64_t>(0x00000008);

    py::class_<XrPosef>(m, "XrPosef")
        .def_readwrite("position", &XrPosef::position)
        .def_readwrite("orientation", &XrPosef::orientation);

    py::class_<XrHandJointLocationEXT>(m, "XrHandJointLocationEXT")
        .def_readwrite("locationFlags", &XrHandJointLocationEXT::locationFlags)
        .def_readwrite("pose", &XrHandJointLocationEXT::pose)
        .def_readwrite("radius", &XrHandJointLocationEXT::radius);

    py::class_<XrSpaceLocation>(m, "XrSpaceLocation")
        .def_readwrite("locationFlags", &XrSpaceLocation::locationFlags)
        .def_readwrite("pose", &XrSpaceLocation::pose);


    // carb interface
    carb::defineInterfaceClass<IOpenxr>(m, "IOpenxr", "acquire_openxr_interface", "release_openxr_interface")
        .def("locate_hand_joints", &IOpenxr::locate_hand_joints, py::arg("hand"), py::arg("time") = std::nullopt,
             py::arg("axisStage"));
}

}
