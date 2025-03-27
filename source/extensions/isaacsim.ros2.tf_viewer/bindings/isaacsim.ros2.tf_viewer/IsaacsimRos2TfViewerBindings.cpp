// SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#include <carb/BindingsPythonUtils.h>

#include <isaacsim/ros2/tf_viewer/ITransformListener.h>

CARB_BINDINGS("isaacsim.ros2.tf_viewer")

namespace isaacsim
{
namespace ros2
{
namespace tf_viewer
{
} // namespace tf_viewer
} // namespace ros2
} // namespace isaacsim

namespace py = pybind11;

PYBIND11_MODULE(_transform_listener, m)
{
    using namespace isaacsim::ros2::tf_viewer;

    m.doc() = "pybind11 isaacsim.ros2.tf_viewer bindings";

    carb::defineInterfaceClass<ITransformListener>(
        m, "ITransformListener", "acquire_transform_listener_interface", "release_transform_listener_interface")
        .def("initialize", &ITransformListener::initialize)
        .def("finalize", &ITransformListener::finalize)
        .def("spin", &ITransformListener::spin)
        .def("reset", &ITransformListener::reset)
        .def("get_transforms",
             [](ITransformListener& m, std::string rootFrame)
             {
                 m.computeTransforms(rootFrame);
                 return std::make_tuple(m.getFrames(), m.getTransforms(), m.getRelations());
             });
}
