import random

import omni.usd
from pxr import UsdGeom


class Example:
    def create(self):
        # Create Point List
        N = 500
        self.point_list = [
            (random.uniform(-2.0, 2.0), random.uniform(-0.1, 0.1), random.uniform(-1.0, 1.0)) for _ in range(N)
        ]
        self.sizes = [0.05 for _ in range(N)]

        points_path = "/World/Points"
        stage = omni.usd.get_context().get_stage()
        self.points = UsdGeom.Points.Define(stage, points_path)
        self.points.CreatePointsAttr().Set(self.point_list)
        self.points.CreateWidthsAttr().Set(self.sizes)
        self.points.CreateDisplayColorPrimvar("constant").Set([(1, 0, 1)])

    def update(self):
        # modify the point list
        for i in range(len(self.point_list)):
            self.point_list[i] = (random.uniform(-2.0, 2.0), random.uniform(-0.1, 0.1), random.uniform(-1.0, 1.0))
        # update the points
        self.points.GetPointsAttr().Set(self.point_list)


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
