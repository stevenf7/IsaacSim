# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np

from scene import Object
from sampling import Sampler


class Room:
    """ For managing a parameterizable rectangular prism centered at the origin. """

    def __init__(self, sim_app, sim_context):
        """ Construct a Room. """

        self.sim_app = sim_app
        self.sim_context = sim_context

        self.stage = self.sim_context.stage

        self.sample = Sampler().sample

    def generate(self):
        """ Create a rectangular prism at the origin. """

        from pxr import Gf, PhysicsSchemaTools

        wall_height = self.sample("wall_height")
        floor_size = self.sample("floor_size")
        self.room_faces = []

        if self.sample("floor"):
            self.room_faces.append("floor")
        if self.sample("wall"):
            self.room_faces.append("wall")
        if self.sample("ceiling"):
            self.room_faces.append("ceiling")

        self.room = []
        for face in self.room_faces:
            if face == "floor":
                translations = [(0, 0, 0)]
                scales = [(floor_size / 100, floor_size / 100, 1)]
                rotations = [(0, 0, 0)]

                PhysicsSchemaTools.addGroundPlane(
                    self.stage, "/World/Room/ground", "Z", floor_size // 2, Gf.Vec3f(0, 0, -1), Gf.Vec3f(1.0)
                )
            elif face == "ceiling":
                translations = [(0, 0, wall_height)]
                scales = [(floor_size / 100, floor_size / 100, 1)]
                rotations = [(0, 0, 0)]
            elif face == "wall":
                translations = []
                translations.append((floor_size / 2, 0, wall_height / 2))
                translations.append((0, floor_size / 2, wall_height / 2))
                translations.append((-floor_size / 2, 0, wall_height / 2))
                translations.append((0, -floor_size / 2, wall_height / 2))
                scales = 4 * [(floor_size / 100, wall_height / 100, 1)]
                rotations = []
                rotations.append((90, 0, 90))
                rotations.append((90, 0, 0))
                rotations.append((90, 0, 90))
                rotations.append((90, 0, 0))

            ref = self.sample("nucleus_server") + "/Users/mtrepte/plane.usd"
            # TODO: change
            label = "other"

            for i in range(len(translations)):
                path = "/World/Room/{}_{}".format(face, i)
                room_face = Object(self.sim_app, self.sim_context, ref, path, None, None, prefix=face)
                room_face.translate(np.array(translations[i]))
                room_face.scale(np.array(scales[i]))
                room_face.rotate(np.array(rotations[i]))
                self.room.append(room_face)

    def update(self):
        """ Update room components. """

        for room_face in self.room:
            room_face.add_material()
