// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "omni/isaac/decals/Decals.h"

#include <carb/BindingsPythonUtils.h>

#include <memory>
#include <string>
#include <vector>

CARB_BINDINGS("omni.isaac.decals.python")

namespace omni
{
namespace isaac
{
namespace decals
{

}
}
}

namespace
{

PYBIND11_MODULE(_decals, m)
{
    using namespace carb;
    using namespace omni::isaac::decals;
    // We use carb data types, must import bindings for them
    auto carb_module = py::module::import("carb");

    m.doc() = "pybind11 omni.isaac.decals bindings";

    defineInterfaceClass<Decals>(m, "Decals", "acquire")
        .def("set_enabled", [](Decals* iface, bool enabled) { iface->setEnbled(enabled); })
        .def("set_picking_enabled", [](Decals* iface, bool enabled) { iface->setPickingEnabled(enabled); })
        .def("set_pen_color", [](Decals* iface, float r, float g, float b) { iface->setPenColor(r, g, b); })
        .def("set_pen_width", [](Decals* iface, float width) { iface->setPenWidth(width); })
        .def("set_pen_offset", [](Decals* iface, float offset) { iface->setPenOffset(offset); })
        .def("set_pen_threshold", [](Decals* iface, float threshold) { iface->setPenThreshold(threshold); })
        .def("set_pen_surface", [](Decals* iface, const char* primPath) { iface->setPenSurface(primPath); })
        .def("set_pen_position", [](Decals* iface, const Float3& worldPosition) { iface->setPenPosition(worldPosition); })
        .def("set_pen_down", [](Decals* iface, bool penDown) { iface->setPenDown(penDown); })
        .def("erase_surface", [](Decals* iface, const char* primPath) { return iface->eraseSurface(primPath); })
        .def("erase_all_surfaces", [](Decals* iface) { iface->eraseAllSurfaces(); })
        .def("run_tests", [](Decals* iface) { iface->runTests(); });
}
}
