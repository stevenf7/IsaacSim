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

from scene.asset import Asset
from output import Logger


class Camera(Asset):
    """ For managing a camera in Isaac Sim. """

    def __init__(self, sim_app, sim_context, path, cam_pose, group):
        """ Construct Camera. """

        super().__init__(sim_app, sim_context, path, cam_pose, "", group, "camera")

        self.load_camera()

    def is_coord_camera_relative(self):
        return False

    def is_rot_camera_relative(self):
        return False

    def load_camera(self):
        """ Create a camera in Isaac Sim. """

        import omni
        from pxr import Sdf, UsdGeom
        from omni.isaac.core.utils import prims

        self.asset = prims.create_prim(self.path, "Xform")
        self.camera_rig = UsdGeom.Xformable(self.asset)

        camera_prim_paths = []
        if self.sample("stereo"):
            camera_prim_paths.append(self.path + "/LeftCamera")
            camera_prim_paths.append(self.path + "/RightCamera")
        else:
            camera_prim_paths.append(self.path + "/MonoCamera")

        self.cameras = [
            self.stage.DefinePrim(Sdf.Path(camera_prim_path), "Camera") for camera_prim_path in camera_prim_paths
        ]

        for camera in self.cameras:
            camera = UsdGeom.Camera(camera)
            camera.GetFocalLengthAttr().Set(self.sample("focal_length"))
            camera.GetFocusDistanceAttr().Set(self.sample("focus_distance"))
            camera.GetHorizontalApertureAttr().Set(self.sample("horiz_aperture"))
            camera.GetVerticalApertureAttr().Set(self.sample("vert_aperture"))
            camera.GetFStopAttr().Set(self.sample("f_stop"))

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

        self.intrinsics = [self.get_intrinsics(camera) for camera in self.cameras]

    def place_in_scene(self):
        """ Place camera in scene. """

        from pxr import UsdGeom

        self.coord = self.get_initial_coord()
        self.rotation = self.get_initial_rotation()
        if self.sample("stereo"):
            self.camera_coords = self.get_stereo_coords(self.coord, self.rotation)
        else:
            self.camera_coords = [self.coord]

        for i in range(len(self.camera_coords)):
            viewport_name, viewport_window = self.viewports[i]
            camera = self.cameras[i]
            coord = self.camera_coords[i]
            viewport_window.set_camera_position(str(camera.GetPath()), coord[0], coord[1], coord[2], True)
            offset_cam_rot = self.rotation + np.array((90, 0, 270))
            UsdGeom.XformCommonAPI(camera).SetRotate(offset_cam_rot.tolist())

    def get_stereo_coords(self, coord, rotation):
        """ Convert camera center coord and rotation and return stereo camera coords. """

        coords = []
        for i in range(len(self.cameras)):
            sign = 1 if i == 0 else -1
            theta = np.radians(rotation[0] + sign * 90)
            phi = np.radians(rotation[1])

            radius = self.sample("stereo_baseline") / 2

            # Add offset such that center of stereo cameras is at cam_coord
            x = coord[0] + radius * np.cos(theta) * np.cos(phi)
            y = coord[1] + radius * np.sin(theta) * np.cos(phi)
            z = coord[2] + radius * sign * np.sin(phi)

            coords.append(np.array(x, y, z))

        return coords

    def get_intrinsics(self, camera):
        """ Compute, print, and return camera intrinsics. """

        # TODO: Use Isaac SIM API to get camera intrinsics

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

        Logger.print("")
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
