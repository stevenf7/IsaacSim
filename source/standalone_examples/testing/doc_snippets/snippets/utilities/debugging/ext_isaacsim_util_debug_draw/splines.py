import random

from isaacsim.util.debug_draw import _debug_draw

draw = _debug_draw.acquire_debug_draw_interface()

point_list_1 = [(random.uniform(-30, -10), random.uniform(-10, 10), random.uniform(-10, 10)) for _ in range(10)]
draw.draw_lines_spline(point_list_1, (1, 1, 1, 1), 10, False)
point_list_2 = [(random.uniform(-30, -10), random.uniform(-10, 10), random.uniform(-10, 10)) for _ in range(10)]
draw.draw_lines_spline(point_list_2, (1, 1, 1, 1), 1, True)
