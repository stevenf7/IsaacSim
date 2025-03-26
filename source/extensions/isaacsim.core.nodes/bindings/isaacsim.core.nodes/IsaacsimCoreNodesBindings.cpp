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
#include <carb/logging/Log.h>

#include <isaacsim/core/nodes/ICoreNodes.h>

CARB_BINDINGS("isaacsim.core.nodes.python")


namespace
{

PYBIND11_MODULE(_isaacsim_core_nodes, m)
{
    // clang-format off
    using namespace carb;
    using namespace isaacsim::core::nodes;
    m.doc() = "pybind11 isaacsim.core.nodes bindings";

    defineInterfaceClass< isaacsim::core::nodes::CoreNodes>(m, "CoreNodes", "acquire_interface", "release_interface")
        .def("get_sim_time", wrapInterfaceFunction(&CoreNodes::getSimTime))
        .def("get_sim_time_monotonic", wrapInterfaceFunction(&CoreNodes::getSimTimeMonotonic))
        .def("get_system_time", wrapInterfaceFunction(&CoreNodes::getSystemTime))
        .def("get_physics_num_steps", wrapInterfaceFunction(&CoreNodes::getPhysicsNumSteps))
        .def("get_sim_time_at_time", wrapInterfaceFunction(&CoreNodes::getSimTimeAtTime))
        .def("get_sim_time_monotonic_at_time", wrapInterfaceFunction(&CoreNodes::getSimTimeMonotonicAtTime))
        .def("get_system_time_at_time", wrapInterfaceFunction(&CoreNodes::getSystemTimeAtTime))
        // TODO105 kill these 3 or replace with _at_time versions
        .def("get_sim_time_at_swh_frame", wrapInterfaceFunction(&CoreNodes::getSimTimeAtSwhFrame))
        .def("get_sim_time_monotonic_at_swh_frame", wrapInterfaceFunction(&CoreNodes::getSimTimeMonotonicAtSwhFrame))
        .def("get_system_time_at_swh_frame", wrapInterfaceFunction(&CoreNodes::getSystemTimeAtSwhFrame))
        ;


}
}
