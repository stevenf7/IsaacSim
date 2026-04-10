// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


#include <carb/BindingsPythonUtils.h>

#include <isaacsim/util/debug_draw/IDebugDraw.h>

CARB_BINDINGS("isaacsim.util.debug_draw.python")


namespace
{

namespace py = pybind11;

PYBIND11_MODULE(_debug_draw, m)
{
    using namespace carb;
    using namespace isaacsim::util::debug_draw;
    // We use carb data types, must import bindings for them
    auto carbModule = py::module::import("carb");

    m.doc() =
        R"pbdoc(

        Debug Drawing
        -------------

        This submodule provides bindings to draw debug lines and points

        Point Example:
            drawn points to the screen with random colors and sizes

            .. code-block:: python

                import random
                from isaacsim.util.debug_draw import _debug_draw
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
                from isaacsim.util.debug_draw import _debug_draw
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

                from isaacsim.util.debug_draw import _debug_draw
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

        .def("draw_points", wrapInterfaceFunction(&DebugDraw::drawPoints),
             R"doc(
                Draw a set of points to the screen.
                
                Args:
                    points (list[tuple]): List of 3D positions (x, y, z) for each point.
                    colors (list[tuple]): List of RGBA colors (r, g, b, a) for each point, values in [0, 1].
                    sizes (list[int]): List of sizes in pixels for each point.
                    
                Returns:
                    None
                    
                Note:
                    All lists must have the same length. Points persist until cleared.
             )doc")
        .def("clear_points", wrapInterfaceFunction(&DebugDraw::clearPoints),
             R"doc(
                Clear all drawn points from the screen.
                
                Args:
                    None
                    
                Returns:
                    None
             )doc")
        .def("get_num_points", wrapInterfaceFunction(&DebugDraw::getNumPoints),
             R"doc(
                Get the current number of points being drawn.
                
                Args:
                    None
                    
                Returns:
                    int: Number of points currently being rendered.
             )doc")
        .def("draw_lines", wrapInterfaceFunction(&DebugDraw::drawLines),
             R"doc(
                Draw a set of lines to the screen.
                
                Args:
                    start_points (list[tuple]): List of 3D start positions (x, y, z) for each line.
                    end_points (list[tuple]): List of 3D end positions (x, y, z) for each line.
                    colors (list[tuple]): List of RGBA colors (r, g, b, a) for each line, values in [0, 1].
                    widths (list[int]): List of line widths in pixels for each line.
                    
                Returns:
                    None
                    
                Note:
                    All lists must have the same length. Lines persist until cleared.
             )doc")
        .def("draw_lines_spline", wrapInterfaceFunction(&DebugDraw::drawLinesSpline),
             R"doc(
                Draw a smooth spline curve through a list of points.
                
                Creates a smooth interpolated curve passing through all control points
                and renders it as connected line segments.
                
                Args:
                    control_points (list[tuple]): List of 3D control points (x, y, z) defining the spline path.
                    color (tuple): RGBA color (r, g, b, a) for the spline, values in [0, 1].
                    width (int): Line width in pixels.
                    closed (bool): If True, connects the last point back to the first to form a closed loop.
                    
                Returns:
                    None
                    
                Note:
                    The spline persists until lines are cleared.
             )doc")
        .def("clear_lines", wrapInterfaceFunction(&DebugDraw::clearLines),
             R"doc(
                Clear all drawn lines and splines from the screen.
                
                Args:
                    None
                    
                Returns:
                    None
             )doc")
        .def("get_num_lines", wrapInterfaceFunction(&DebugDraw::getNumLines),
             R"doc(
                Get the current number of lines being drawn.
                
                Args:
                    None
                    
                Returns:
                    int: Number of line segments currently being rendered.
             )doc");
}
}
