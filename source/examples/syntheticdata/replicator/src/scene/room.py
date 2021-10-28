# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np

from sampling import Sampler
from scene import Object


class Room:
    """ For managing a parameterizable rectangular prism centered at the origin. """

    def __init__(self, sim_app, sim_context):
        """ Construct Room. Generate room in Isaac SIM. """

        self.sim_app = sim_app
        self.sim_context = sim_context

        self.stage = self.sim_context.stage

        self.sample = Sampler().sample

        self.room = self.create_room()
        self.sim_context.render()

    def create_room(self):
        """ Generate and return assets creating a rectangular prism at the origin. """

        from pxr import Gf, PhysicsSchemaTools

        wall_height = self.sample("wall_height")
        floor_size = self.sample("floor_size")
        self.room_faces = []

        faces = []
        coords = []
        scales = []
        rotations = []
        if self.sample("floor"):
            faces.append("floor")
            coords.append((0, 0, 0))
            scales.append((floor_size / 100, floor_size / 100, 1))
            rotations.append((0, 0, 0))

            # TODO: Replace this by making the room itself have a physical hitbox
            PhysicsSchemaTools.addGroundPlane(
                self.stage, "/World/Room/ground", "Z", floor_size // 2, Gf.Vec3f(0, 0, -1), Gf.Vec3f(1.0)
            )

        if self.sample("wall"):
            faces.extend(4 * ["wall"])
            coords.append((floor_size / 2, 0, wall_height / 2))
            coords.append((0, floor_size / 2, wall_height / 2))
            coords.append((-floor_size / 2, 0, wall_height / 2))
            coords.append((0, -floor_size / 2, wall_height / 2))
            scales.extend(4 * [(floor_size / 100, wall_height / 100, 1)])
            rotations.append((90, 0, 90))
            rotations.append((90, 0, 0))
            rotations.append((90, 0, 90))
            rotations.append((90, 0, 0))

        if self.sample("ceiling"):
            faces.append("ceiling")
            coords.append((0, 0, wall_height))
            scales.append((floor_size / 100, floor_size / 100, 1))
            rotations.append((0, 0, 0))

        # TODO: move this to an official path on Nucleus
        ref = self.sample("nucleus_server") + "/Users/mtrepte/shapes/plane.usd"
        room = []

        for i in range(len(faces)):
            path = "/World/Room/{}_{}".format(faces[i], i)
            room_face = Object(self.sim_app, self.sim_context, ref, path, None, None, prefix=faces[i], can_move=False)
            room_face.translate(np.array(coords[i]))
            room_face.scale(np.array(scales[i]))
            room_face.rotate(np.array(rotations[i]))
            room.append(room_face)

        return room

    def update(self):
        """ Update room components. """

        for room_face in self.room:
            room_face.add_material()
