import random

from isaacsim.util.debug_draw import _debug_draw


class Example:
    def create(self):
        self.draw = _debug_draw.acquire_debug_draw_interface()
        N = 500
        self.point_list = [
            (random.uniform(-2.0, 2.0), random.uniform(-0.1, 0.1), random.uniform(-1.0, 1.0)) for _ in range(N)
        ]
        self.color_list = [(random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1), 1) for _ in range(N)]
        self.size_list = [10.0 for _ in range(N)]

    def update(self):
        # modify the point list
        for i in range(len(self.point_list)):
            self.point_list[i] = (random.uniform(-2.0, 2.0), random.uniform(-0.1, 0.1), random.uniform(-1.0, 1.0))

        # draw the points
        self.draw.clear_points()
        self.draw.draw_points(self.point_list, self.color_list, self.size_list)


import asyncio

import omni

example = Example()
example.create()


async def update_points():
    # Update 10 times, waiting 10 frames between each update
    for _ in range(10):
        for _ in range(10):
            await omni.kit.app.get_app().next_update_async()
        example.update()


asyncio.ensure_future(update_points())
