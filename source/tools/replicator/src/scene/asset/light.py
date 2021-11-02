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
        """ Construct Light. """

        super().__init__(sim_app, sim_context, path, cam_pose, "", group, "light")

        self.load_light()

    def place_in_scene(self):
        """ Place light in scene. """

        self.coord = self.get_initial_coord()
        self.translate(self.coord)
        self.rotation = self.get_initial_rotation()
        self.rotate(self.rotation)

    def load_light(self):
        """ Create a light in Isaac Sim. """

        from omni.isaac.core.utils import prims

        intensity = self.sample("light_intensity")
        color = tuple(self.sample("light_color") / 255)
        temp_enabled = self.sample("light_temp_enabled")
        temp = self.sample("light_temp")
        radius = self.sample("light_radius")
        focus = self.sample("light_directed_focus")
        focus_softness = self.sample("light_directed_focus_softness")

        attributes = {}
        if self.sample("light_distant"):
            light_shape = "DistantLight"
        elif self.sample("light_directed"):
            light_shape = "DiskLight"
            attributes["shaping:focus"] = focus
            attributes["shaping:cone:softness"] = focus_softness
            attributes["radius"] = radius
        else:
            light_shape = "SphereLight"
            attributes["radius"] = radius

        attributes["intensity"] = intensity
        attributes["color"] = color
        if temp_enabled:
            attributes["enableColorTemperature"] = True
            attributes["colorTemperature"] = temp

        self.asset = prims.create_prim(self.path, light_shape, attributes=attributes)
