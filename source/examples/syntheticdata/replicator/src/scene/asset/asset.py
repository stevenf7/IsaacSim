# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from re import L
import numpy as np

from output import Logger
from sampling import Sampler


# TODO: fix scaling and parameterize these values
HORIZ_FOV = 45
VERT_FOV = 45


class Asset:
    """ For managing an asset in Isaac Sim. """

    def __init__(self, sim_app, sim_context, path, cam_data, label, group, prefix):
        """ Construct Asset. """

        self.sim_app = sim_app
        self.sim_context = sim_context
        self.path = path
        self.cam_data = cam_data
        self.label = label
        self.prefix = prefix

        self.stage = self.sim_context.stage
        self.sample = Sampler(group).sample

        self.physics = False

    def is_given(self, param):
        """ Is a parameter value is given. """

        if type(param) is np.ndarray:
            return True
        else:
            return param is not None

    def translate(self, coord):
        """ Translate asset. """

        from pxr import UsdGeom

        UsdGeom.XformCommonAPI(self.asset).SetTranslate(coord.tolist())

    def scale(self, scale):
        """ Scale asset uniformly across all axes. """

        import omni
        from pxr import Gf, Sdf, UsdGeom

        try:
            UsdGeom.XformCommonAPI(self.asset).SetScale(scale.tolist())
        except:
            omni.kit.commands.execute(
                "ChangeProperty",
                prop_path=Sdf.Path(self.path + ".xformOp:scale"),
                value=Gf.Vec3d(scale.tolist()),
                prev=(),
            )

    def rotate(self, rotation):
        """ Rotate asset. """

        import omni
        from pxr import Gf, Sdf, UsdGeom

        try:
            UsdGeom.XformCommonAPI(self.asset).SetRotate(rotation.tolist())
        except:
            omni.kit.commands.execute(
                "ChangeProperty",
                prop_path=Sdf.Path(self.path + ".xformOp:rotateXYZ"),
                value=Gf.Vec3d(rotation.tolist()),
                prev=(),
            )

    def concat(self, parameter_suffix):
        """ Concatenate the parameter prefix and suffix. """

        return self.prefix + "_" + parameter_suffix

    def get_coords(self):
        """ Get coordinates of asset across 3 axes. """

        is_coord_scene_relative = self.sample(self.concat("coord_sensor_relative"))
        if is_coord_scene_relative:
            ((cam_x, cam_y, cam_z), (cam_rot_x, cam_rot_y, cam_rot_z), (horiz_fov, vert_fov)) = self.cam_data

            radius = self.sample(self.concat("distance"))
            theta = horiz_fov * self.sample(self.concat("horiz_fov_loc")) / 2
            phi = vert_fov * self.sample(self.concat("vert_fov_loc")) / 2

            # Convert from polar to cartesian
            rads = np.radians(cam_rot_z + theta)
            x = cam_x + radius * np.cos(rads)
            y = cam_y + radius * np.sin(rads)

            rads = np.radians(cam_rot_x + phi)
            z = cam_z + radius * np.sin(rads)

            Logger.print(
                "adding {} {} at cartesian({}, {}, {}) and relative polar({}, {}, {})".format(
                    self.prefix.upper(),
                    self.label,
                    round(x),
                    round(y),
                    round(z),
                    round(radius),
                    round(theta),
                    round(phi),
                )
            )
        else:
            x, y, z = (
                self.sample(self.concat("coord_x")),
                self.sample(self.concat("coord_y")),
                self.sample(self.concat("coord_z")),
            )
            Logger.print(
                "adding {} {} at cartesian({}, {}, {}) ".format(
                    self.prefix.upper(), self.label, round(x), round(y), round(z)
                )
            )

        coords = np.array([x, y, z])

        return coords

    def get_rotation(self):
        """ Get rotation of asset across 3 axes. """

        rotation = [
            self.sample(self.concat("rot_x")),
            self.sample(self.concat("rot_y")),
            self.sample(self.concat("rot_z")),
        ]
        rotation = np.array(rotation)

        is_rotation_scene_relative = self.sample(self.concat("rot_sensor_relative"))
        if is_rotation_scene_relative:
            ((cam_x, cam_y, cam_z), (cam_rot_x, cam_rot_y, cam_rot_z), (horiz_fov, vert_fov)) = self.cam_data
            rotation = np.add(rotation, [cam_rot_x, cam_rot_y, cam_rot_z], out=rotation, casting="unsafe")

        return rotation

    def place_in_scene(self):
        """ Place asset in scene. """
        pass
