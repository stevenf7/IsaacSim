import random

import omni.usd
from pxr import Gf, UsdGeom


class Example:
    def create(self):
        # Create Point List
        N = 500
        scale = 0.05
        self.point_list = [
            (random.uniform(-2.0, 2.0), random.uniform(-0.1, 0.1), random.uniform(-1.0, 1.0)) for _ in range(N)
        ]
        self.colors = [(1, 1, 1, 1) for _ in range(N)]
        self.sizes = [(1.0, 1.0, 1.0) for _ in range(N)]

        # Set up Geometry to be Instanced
        cube_path = "/World/Cube"
        stage = omni.usd.get_context().get_stage()
        cube = UsdGeom.Cube(stage.DefinePrim(cube_path, "Cube"))
        cube.AddScaleOp().Set(Gf.Vec3d(1, 1, 1) * scale)
        cube.CreateDisplayColorPrimvar().Set([(0, 1, 1)])
        # Set up Point Instancer

        instance_path = "/World/PointInstancer"
        self.point_instancer = UsdGeom.PointInstancer(stage.DefinePrim(instance_path, "PointInstancer"))
        # Create & Set the Positions Attribute
        self.positions_attr = self.point_instancer.CreatePositionsAttr()
        self.positions_attr.Set(self.point_list)
        self.scale_attr = self.point_instancer.CreateScalesAttr()
        self.scale_attr.Set(self.sizes)
        # Set the Instanced Geometry
        self.point_instancer.CreatePrototypesRel().SetTargets([cube.GetPath()])

        self.proto_indices_attr = self.point_instancer.CreateProtoIndicesAttr()
        self.proto_indices_attr.Set([0] * len(self.point_list))

    def update(self):
        # modify the point list
        for i in range(len(self.point_list)):
            self.point_list[i] = (random.uniform(-2.0, 2.0), random.uniform(-0.1, 0.1), random.uniform(-1.0, 1.0))
        # update the points
        self.positions_attr.Set(self.point_list)


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
