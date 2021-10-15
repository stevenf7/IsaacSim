# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from scene.asset import Asset


class Light(Asset):
    """ For managing a light asset in Isaac Sim. """

    def __init__(self, sim_app, sim_context, path, cam_pose, group):
        """ Construct a Light. """

        super().__init__(sim_app, sim_context, path, cam_pose, "", group, "light")

        self.load_light()

    def place_in_scene(self):
        """ Place light in scene. """

        coords = self.get_coords()
        self.translate(coords)
        rotation = self.get_rotation()
        self.rotate(rotation)

    def load_light(self):
        """ Create a light in Isaac Sim. """

        from omni.isaac.core.utils import prims

        attributes = {}
        attributes["intensity"] = self.sample("light_intensity")
        attributes["color"] = tuple(self.sample("light_color") / 255)

        if self.sample("light_distant"):
            light_shape = "DistantLight"
        else:
            light_shape = "SphereLight"
            attributes["radius"] = self.sample("light_radius")

        self.asset = prims.create_prim(self.path, light_shape, attributes=attributes)
