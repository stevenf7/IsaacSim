// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsPythonUtils.h>

#include <include/Ros2Bridge.h>
#include <pybind11/numpy.h>

CARB_BINDINGS("isaacsim.ros2.bridge.python")

namespace isaacsim
{
namespace ros2
{
namespace bridge
{
} // namespace bridge
} // namespace ros2
} // namespace isaacsim

namespace
{

PYBIND11_MODULE(_ros2_bridge, m)
{
    using namespace carb;
    using namespace isaacsim::ros2::bridge;

    m.doc() = "Isaac ROS2 bridge bindings";

    {
        defineInterfaceClass<Ros2Bridge>(m, "Ros2Bridge", "acquire_ros2_bridge_interface", "release_ros2_bridge_interface")
            .def("get_startup_status", wrapInterfaceFunction(&Ros2Bridge::getStartupStatus));
    }
}

} // namespace anonymous
