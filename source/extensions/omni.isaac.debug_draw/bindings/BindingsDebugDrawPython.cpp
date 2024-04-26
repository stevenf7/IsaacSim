// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <carb/BindingsPythonUtils.h>

#include <DebugDraw.h>

CARB_BINDINGS("omni.isaac.debug_draw.python")

namespace omni
{
namespace isaac
{
namespace debug_draw
{
}
}
}

namespace
{

namespace py = pybind11;

PYBIND11_MODULE(_debug_draw, m)
{
    using namespace carb;
    using namespace omni::isaac::debug_draw;
    // We use carb data types, must import bindings for them
    auto carb_module = py::module::import("carb");

    m.doc() =
        R"pbdoc( 
            
        Debug Drawing
        -------------

        This submodule provides bindings to draw debug lines and points
        
        Point Example:
            drawn points to the screen with random colors and sizes

            .. code-block:: python

                import random
                from omni.isaac.debug_draw import _debug_draw
                draw = _debug_draw.acquire_debug_draw_interface()
                N = 10000
                point_list_1 = [
                    (random.uniform(-1000, 1000), random.uniform(-1000, 1000), random.uniform(-1000, 1000)) for _ in range(N)
                ]
                point_list_2 = [
                    (random.uniform(-1000, 1000), random.uniform(1000, 3000), random.uniform(-1000, 1000)) for _ in range(N)
                ]
                point_list_3 = [
                    (random.uniform(-1000, 1000), random.uniform(-3000, -1000), random.uniform(-1000, 1000)) for _ in range(N)
                ]
                colors = [(random.uniform(0.5, 1), random.uniform(0.5, 1), random.uniform(0.5, 1), 1) for _ in range(N)]
                sizes = [random.randint(1, 50) for _ in range(N)]
                draw.draw_points(point_list_1, [(1, 0, 0, 1)] * N, [10] * N)
                draw.draw_points(point_list_2, [(0, 1, 0, 1)] * N, [10] * N)
                draw.draw_points(point_list_3, colors, sizes)

        Line Example:
            drawn lines to the screen with random colors and widths

            .. code-block:: python

                import random
                from omni.isaac.debug_draw import _debug_draw
                draw = _debug_draw.acquire_debug_draw_interface()
                N = 10000
                point_list_1 = [
                    (random.uniform(1000, 3000), random.uniform(-1000, 1000), random.uniform(-1000, 1000)) for _ in range(N)
                ]
                point_list_2 = [
                    (random.uniform(1000, 3000), random.uniform(-1000, 1000), random.uniform(-1000, 1000)) for _ in range(N)
                ]
                colors = [(random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1), 1) for _ in range(N)]
                sizes = [random.randint(1, 25) for _ in range(N)]
                draw.draw_lines(point_list_1, point_list_2, colors, sizes)

        Spline Example:
            drawn splines to the screen with random colors and widths

            .. code-block:: python

                from omni.isaac.debug_draw import _debug_draw
                draw = _debug_draw.acquire_debug_draw_interface()
                point_list_1 = [
                    (random.uniform(-300, -100), random.uniform(-100, 100), random.uniform(-100, 100)) for _ in range(10)
                ]
                draw.draw_lines_spline(point_list_1, (1, 1, 1, 1), 10, False)
                point_list_2 = [
                    (random.uniform(-300, -100), random.uniform(-100, 100), random.uniform(-100, 100)) for _ in range(10)
                ]
                draw.draw_lines_spline(point_list_2, (1, 1, 1, 1), 5, True)

        )pbdoc";
    defineInterfaceClass<DebugDraw>(m, "DebugDraw", "acquire_debug_draw_interface", "release_debug_draw_interface")

        .def("draw_points", wrapInterfaceFunction(&DebugDraw::drawPoints), "Draw a set of points to the screen")
        .def("clear_points", wrapInterfaceFunction(&DebugDraw::clearPoints), "Clear points")
        .def("get_num_points", wrapInterfaceFunction(&DebugDraw::getNumPoints),
             "Return the current number of points being drawn")
        .def("draw_lines", wrapInterfaceFunction(&DebugDraw::drawLines), "Draw a set of lines to the screen")
        .def("draw_lines_spline", wrapInterfaceFunction(&DebugDraw::drawLinesSpline),
             "Draw spline between a list of points as line segments")
        .def("clear_lines", wrapInterfaceFunction(&DebugDraw::clearLines), "Clear lines")
        .def("get_num_lines", wrapInterfaceFunction(&DebugDraw::getNumLines),
             "Return the current number of lines being drawn");
}
}
