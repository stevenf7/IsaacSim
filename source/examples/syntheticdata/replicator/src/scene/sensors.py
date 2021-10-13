# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import math
import numpy as np

import carb
import omni

from output import Logger
from sampling import Sampler


class SensorManager:
    """ For setting-up sensors and placing them in scenes. """

    def __init__(self, sim_app, sim_context):
        """ Construct SensorManager. Set-up camera and viewports in simulator. """

        self.sim_app = sim_app
        self.sim_context = sim_context

        self.stage = self.sim_context.stage

        self.sample = Sampler().sample
        self.setup_camera()

    def setup_camera(self):
        """ Set-up mono or stereo cameras and viewports in Isaac-Sim. """

        from pxr import UsdGeom
        from omni.isaac.core.utils import prims

        # Create mono or stereo cameras
        camera_path = "/World/CameraRig"
        self.camera_rig = UsdGeom.Xformable(prims.create_prim(self.stage, camera_path, "Xform"))

        camera_prim_paths = []
        if self.sample("stereo"):
            camera_prim_paths.append(camera_path + "/LeftCamera")
            camera_prim_paths.append(camera_path + "/RightCamera")
        else:
            camera_prim_paths.append(camera_path + "/MonoCamera")

        self.cameras = [self.stage.DefinePrim(camera_prim_path, "Camera") for camera_prim_path in camera_prim_paths]

        # TODO: add FOV support
        for camera in self.cameras:
            camera = UsdGeom.Camera(camera)
            camera.GetFocalLengthAttr().Set(self.sample("focal_length"))

        # Set viewports
        carb.settings.acquire_settings_interface().set_int("/app/renderer/resolution/width", -1)
        carb.settings.acquire_settings_interface().set_int("/app/renderer/resolution/height", -1)

        self.viewports = []
        for i in range(len(self.cameras)):
            if i == 0:
                viewport_handle = omni.kit.viewport.get_viewport_interface().get_instance("Viewport")
            else:
                viewport_handle = omni.kit.viewport.get_viewport_interface().create_instance()
            viewport_window = omni.kit.viewport.get_viewport_interface().get_viewport_window(viewport_handle)
            viewport_window.set_texture_resolution(self.sample("img_width"), self.sample("img_height"))
            viewport_window.set_active_camera(camera_prim_paths[i])

            # Set viewport window size
            viewport_window.set_window_size(1800, 1600)
            if i == 0:
                viewport_window.set_window_pos(0, 40)
            else:
                viewport_window.set_window_pos(1440, 40)

            if self.sample("stereo"):
                if i == 0:
                    viewport_name = "left"
                else:
                    viewport_name = "right"
            else:
                viewport_name = "mono"
            self.viewports.append((viewport_name, viewport_window))

        self.sim_context.render()

        Logger.print("")
        self.cam_intrinsics = [self.get_cam_intrinsics(camera) for camera in self.cameras]

    def get_cam_intrinsics(self, camera):
        """ Compute and print camera intrinsics. """

        width = self.sample("img_width")
        height = self.sample("img_height")

        focal_length = camera.GetAttribute("focalLength").Get()
        horiz_aperture = camera.GetAttribute("horizontalAperture").Get()
        vert_aperture = camera.GetAttribute("verticalAperture").Get()

        horiz_fov = 2 * math.atan(horiz_aperture / (2 * focal_length))
        horiz_fov = np.degrees(horiz_fov)
        vert_fov = 2 * math.atan(vert_aperture / (2 * focal_length))
        vert_fov = np.degrees(vert_fov)

        fx = width * focal_length / horiz_aperture
        fy = height * focal_length / vert_aperture
        cx = width * 0.5
        cy = height * 0.5

        proj_mat = np.array([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]])
        with np.printoptions(precision=2, suppress=True):
            proj_mat_str = str(proj_mat)

        Logger.print("Camera intrinsics")
        Logger.print("- width, height: {}, {}".format(round(width), round(height)))
        Logger.print("- focal_length: {}".format(focal_length))
        Logger.print("- horiz_aperture, vert_aperture: {}, {}".format(round(horiz_aperture, 2), round(vert_aperture)))
        Logger.print("- horiz_fov, vert_fov: {}, {}".format(round(horiz_fov, 2), round(vert_fov, 2)))
        Logger.print("- focal_x, focal_y: {}, {}".format(round(fx, 2), round(fy, 2)))
        Logger.print("- proj_mat: \n {}".format(str(proj_mat_str)))
        Logger.print("")

        cam_intrinsics = {
            "width": width,
            "height": height,
            "focal_length": focal_length,
            "horiz_aperture": horiz_aperture,
            "vert_aperture": vert_aperture,
            "horiz_fov": horiz_fov,
            "vert_fov": vert_fov,
            "fx": fx,
            "fy": fy,
            "cx": cx,
            "cy": cy,
            "proj_mat": proj_mat,
        }

        return cam_intrinsics

    def place_camera(self):
        """ Spawn in a camera at a coord and rotation. """

        from pxr import Gf, UsdGeom

        self.cam_x = self.sample("camera_coord_x")
        self.cam_y = self.sample("camera_coord_y")
        self.cam_z = self.sample("camera_coord_z")

        self.cam_rot_x = self.sample("camera_rot_x")
        self.cam_rot_y = self.sample("camera_rot_y")  # clockwise viewport rotation
        self.cam_rot_z = self.sample("camera_rot_z")

        Logger.print(
            "adding CAM at cartesian({}, {}, {}) with rotation({}, {}, {})".format(
                round(self.cam_x),
                round(self.cam_y),
                round(self.cam_z),
                round(self.cam_rot_x),
                round(self.cam_rot_y),
                round(self.cam_rot_z),
            )
        )

        for i, camera in enumerate(self.cameras):
            viewport_name, viewport_window = self.viewports[i]
            if self.sample("stereo"):
                sign = 1 if i == 0 else -1
                theta = np.radians(self.cam_rot_x + sign * 90)
                phi = np.radians(self.cam_rot_y)

                radius = self.sample("stereo_baseline") / 2

                # Add offset such that center of stereo cameras is at cam_x, cam_y, cam_z
                x = self.cam_x + radius * np.cos(theta) * np.cos(phi)
                y = self.cam_y + radius * np.sin(theta) * np.cos(phi)
                z = self.cam_z + radius * sign * np.sin(phi)
            else:
                x = self.cam_x
                y = self.cam_y
                z = self.cam_z

            # Place camera(s) at a position and orientation
            viewport_window.set_camera_position(str(camera.GetPath()), x, y, z, True)
            UsdGeom.XformCommonAPI(camera).SetRotate(
                Gf.Vec3f(90 + self.cam_rot_x, self.cam_rot_y, 270 + self.cam_rot_z)
            )

        horiz_fov = self.cam_intrinsics[0]["horiz_fov"]
        vert_fov = self.cam_intrinsics[0]["vert_fov"]
        cam_data = (
            (self.cam_x, self.cam_y, self.cam_z),
            (self.cam_rot_x, self.cam_rot_y, self.cam_rot_z),
            (horiz_fov, vert_fov),
        )

        return cam_data
