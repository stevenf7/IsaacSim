import random

from isaacsim.util.debug_draw import _debug_draw

draw = _debug_draw.acquire_debug_draw_interface()

N = 10000
point_list_1 = [(random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10)) for _ in range(N)]
point_list_2 = [(random.uniform(-10, 10), random.uniform(10, 30), random.uniform(-10, 10)) for _ in range(N)]
point_list_3 = [(random.uniform(-10, 10), random.uniform(-30, -10), random.uniform(-10, 10)) for _ in range(N)]
colors = [(random.uniform(0.5, 1), random.uniform(0.5, 1), random.uniform(0.5, 1), 1) for _ in range(N)]
sizes = [random.randint(1, 50) for _ in range(N)]
draw.draw_points(point_list_1, [(1, 0, 0, 1)] * N, [10] * N)
draw.draw_points(point_list_2, [(0, 1, 0, 1)] * N, [10] * N)
draw.draw_points(point_list_3, colors, sizes)
