# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from abc import ABC, abstractmethod
import math
import numpy as np

from output import Logger
from sampling import Sampler


class Asset(ABC):
    """ For managing an asset in Isaac Sim. """

    def __init__(self, sim_app, sim_context, path, camera, label, group, prefix, can_move=True):
        """ Construct Asset. """

        self.sim_app = sim_app
        self.sim_context = sim_context
        self.path = path
        self.camera = camera
        self.label = label
        self.prefix = prefix
        self.can_move = can_move

        self.stage = self.sim_context.stage
        self.sample = Sampler(group=group).sample

        if self.can_move:
            self.vel = self.sample(self.concat("vel"))
            self.rot_vel = self.sample(self.concat("rot_vel"))

            self.acc = self.sample(self.concat("accel"))
            self.rot_acc = self.sample(self.concat("rot_accel"))

        self.physics = False

    @abstractmethod
    def place_in_scene(self):
        """ Place asset in scene. """
        pass

    def is_given(self, param):
        """ Is a parameter value is given. """

        if type(param) in (np.ndarray, list, tuple, str):
            return len(param) > 0
        elif type(param) is float:
            return not math.isnan(param)
        else:
            return param is not None

    def translate(self, coord):
        """ Translate asset. """

        from pxr import Gf

        xform_op = self.asset.GetAttribute("xformOp:translate")
        xform_op.Set(Gf.Vec3f(coord.tolist()))

    def scale(self, scale):
        """ Scale asset uniformly across all axes. """

        from pxr import Gf

        xform_op = self.asset.GetAttribute("xformOp:scale")
        xform_op.Set(Gf.Vec3f(scale.tolist()))

    def rotate(self, rotation):
        """ Rotate asset. """

        from omni.isaac.core.utils.rotations import euler_angles_to_quat
        from pxr import Gf

        xform_op = self.asset.GetAttribute("xformOp:orient")
        xform_op.Set(Gf.Quatf(*euler_angles_to_quat(rotation.tolist(), degrees=True).tolist()))

    def is_coord_camera_relative(self):
        return self.sample(self.concat("coord_camera_relative"))

    def is_rot_camera_relative(self):
        return self.sample(self.concat("rot_camera_relative"))

    def concat(self, parameter_suffix):
        """ Concatenate the parameter prefix and suffix. """

        return self.prefix + "_" + parameter_suffix

    def get_initial_coord(self):
        """ Get coordinates of asset across 3 axes. """

        if self.is_coord_camera_relative():
            cam_coord = self.camera.coord
            cam_rot = self.camera.rotation
            horiz_fov = -1 * self.camera.intrinsics[0]["horiz_fov"]
            vert_fov = self.camera.intrinsics[0]["vert_fov"]

            radius = self.sample(self.concat("distance"))
            theta = horiz_fov * self.sample(self.concat("horiz_fov_loc")) / 2
            phi = vert_fov * self.sample(self.concat("vert_fov_loc")) / 2

            relative_polar_coord = np.array([radius, theta, phi])

            # Convert from polar to cartesian
            rads = np.radians(cam_rot[2] + theta)
            x = cam_coord[0] + radius * np.cos(rads)
            y = cam_coord[1] + radius * np.sin(rads)

            rads = np.radians(cam_rot[0] + phi)
            z = cam_coord[2] + radius * np.sin(rads)

            coord = np.array([x, y, z])

            Logger.print(
                "adding {} {} at cartesian {} and relative polar {}".format(
                    self.prefix.upper(),
                    self.label,
                    np.round(coord, decimals=2),
                    np.round(relative_polar_coord, decimals=2),
                )
            )

        else:
            coord = self.sample(self.concat("coord"))
            Logger.print(
                "adding {} {} at cartesian {}".format(self.prefix.upper(), self.label, np.round(coord, decimals=2))
            )

        return coord

    def get_initial_rotation(self):
        """ Get rotation of asset across 3 axes. """

        rotation = self.sample(self.concat("rot"))
        rotation = np.array(rotation)

        if self.is_rot_camera_relative():
            cam_rot = self.camera.rotation
            rotation += cam_rot

        return rotation

    def step(self, step_time):
        """ Step asset forward in its sequence. """

        if not self.can_move:
            return

        vel_vector = self.vel
        acc_vector = self.acc
        if self.sample(self.concat("movement") + "_" + self.concat("relative")):
            rot_x = self.rotation[0]
            rot_z = self.rotation[2]

            vel_vector[0] = self.vel[0] * np.cos(np.radians(rot_x)) + self.vel[1] * np.cos(np.radians(rot_x + 90))
            vel_vector[1] = self.vel[0] * np.sin(np.radians(rot_x)) + self.vel[1] * np.sin(np.radians(rot_x + 90))
            vel_vector[2] = self.vel[2] * np.sin(np.radians(rot_z))

        self.coord = self.coord + vel_vector * step_time + 0.5 * acc_vector * step_time ** 2
        self.translate(self.coord)

        self.rotation = self.rotation + self.rot_vel * step_time + 0.5 * self.rot_acc * step_time ** 2
        self.rotate(self.rotation)
