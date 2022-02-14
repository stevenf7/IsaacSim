# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from pxr import Gf
import numpy as np
from scipy.spatial.transform import Rotation as R

from .object_interface import Object

"""
An Object allows the manipulation of a group of prims as a single unit.  A subclass of Object must implement
the construct() method to specify what prims comprise an object, and what their relative positions are.

When an Object is created, the base pose is specified in the constructor.  Inside the construct() method,
the position of each prim in the object is specified relative to that base pose.

For example, the Cubby Object is constructed from a set of blocks that have translations specified relative to 
the base of the Cubby.  The relative rotation is not specified, and so is assumed to be the identity.

Target, Block, Sphere, and Capsule are the most basic possible variants of Object, as they are comprised of 
just a single prim.
"""


class Target(Object):
    def construct(self, **kwargs):
        size = kwargs.get("size", 5)
        target_color = kwargs.get("target_color", np.array([1.0, 0, 0]))

        self.create_target(target_size=size, target_color=target_color)

    def get_target(self, make_visible=True):
        target = self.targets[0]
        target.set_visibility(make_visible)

        return target


class Block(Object):
    def construct(self, **kwargs):
        self.size = kwargs.get("size", 10 * np.ones(3))
        # self.scales = kwargs.get("scales", np.array([1.0, 1.0, 1.0]))

        self.create_block(self.size)

    def get_component(self):
        return self.components[0]


class Sphere(Object):
    def construct(self, **kwargs):
        self.radius = kwargs.get("radius", 10)
        self.create_sphere(self.radius)

    def get_geom(self):
        return self.components[0]


class Capsule(Object):
    def construct(self, **kwargs):
        self.radius = kwargs.get("radius", 5)
        self.height = kwargs.get("height", 10)
        self.create_capsule(self.radius, self.height)

    def get_geom(self):
        return self.components[0]


class Cubbies(Object):
    def construct(self, **kwargs):
        self.size = kwargs.get("size", 1)

        self.num_rows = kwargs.get("num_rows", 3)
        self.num_cols = kwargs.get("num_cols", 3)

        self.height = kwargs.get("height", 100)  # z axis
        self.width = kwargs.get("width", 100)  # y axis
        self.depth = kwargs.get("depth", 30)  # x axis

        self.target_depth = kwargs.get("target_depth", self.depth / 2)

        self.cub_height = self.height / self.num_rows
        self.cub_width = self.width / self.num_cols

        back = self.create_block(
            self.size * np.array([1, self.width, self.height]),
            relative_translation=np.array([self.depth / 2, 0, self.height / 2]),
        )

        for i in range(self.num_rows + 1):
            shelf = self.create_block(
                self.size * np.array([self.depth, self.width, 1]),
                relative_translation=np.array([0, 0, self.cub_height * i]),
            )
        for i in range(self.num_cols + 1):
            shelf = self.create_block(
                self.size * np.array([self.depth, 1, self.height]),
                relative_translation=np.array([0, self.cub_width * i - self.width / 2, self.height / 2]),
            )

        # Put a target in each shelf.

        target_x_offset = self.target_depth - self.depth / 2

        target_start = np.array([target_x_offset, -self.width / 2 + self.cub_width / 2, self.cub_height / 2])

        target_rot = R.from_rotvec([0, np.pi / 2, 0]).as_matrix()

        for i in range(self.num_rows):
            for j in range(self.num_cols):
                pos = target_start + np.array([0, self.cub_width * j, self.cub_height * i])
                target = self.create_target(relative_translation=pos, relative_rotation=target_rot)


class Windmill(Object):
    def construct(self, **kwargs):
        self.size = kwargs.get("size", 1)  # scales entire windmill

        self.num_blades = kwargs.get("num_blades", 2)

        self.blade_width = kwargs.get("blade_width", 1)  # y axis
        self.blade_height = kwargs.get("blade_height", 100)  # z axis
        self.blade_depth = kwargs.get("blade_depth", 1)  # x axis

        for i in range(self.num_blades):
            rot = R.from_rotvec([i * np.pi / self.num_blades, 0, 0])
            blade = self.create_block(
                self.size * np.array([self.blade_depth, self.blade_width, self.blade_height]),
                relative_rotation=rot.as_matrix(),
            )


class Window(Object):
    def construct(self, **kwargs):
        self.width = kwargs.get("width", 100)  # y axis
        self.depth = kwargs.get("depth", 5)  # x axis
        self.height = kwargs.get("height", 100)  # z axis

        self.size = kwargs.get("size", 1)  # scales entire window

        self.window_width = kwargs.get("window_width", 50)
        self.window_height = kwargs.get("window_height", 50)

        side_width = (self.width - self.window_width) / 2
        side = self.create_block(
            self.size * np.array([self.depth, side_width, self.height]),
            relative_translation=np.array([0, -self.width / 2 + side_width / 2, 0]),
        )
        side = self.create_block(
            self.size * np.array([self.depth, side_width, self.height]),
            relative_translation=np.array([0, +self.width / 2 - side_width / 2, 0]),
        )

        top_height = (self.height - self.window_height) / 2
        top = self.create_block(
            self.size * np.array([self.depth, self.width, top_height]),
            relative_translation=np.array([0, 0, self.height / 2 - top_height / 2]),
        )
        bottom = self.create_block(
            self.size * np.array([self.depth, self.width, top_height]),
            relative_translation=np.array([0, 0, -self.height / 2 + top_height / 2]),
        )

        self.center_target = self.create_target()  # in center of window
        self.behind_target = self.create_target(relative_translation=np.array([self.depth, 0, 0]))
        self.front_target = self.create_target(relative_translation=np.array([-self.depth, 0, 0]))
