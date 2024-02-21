# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from functools import partial

import numpy as np
from omni.replicator.core import AnnotatorRegistry, BackendDispatch, Writer, WriterRegistry
from omni.replicator.core.scripts.functional import write_image, write_json
from PIL import Image, ImageDraw
from pxr import Gf

__version__ = "0.0.1"


class PoseWriter(Writer):
    """Pose Writer

    Args:
        output_dir:
            Output directory string that indicates the directory to save the results.
        use_subfolders:
            If True, the writer will create subfolders for each render product, otherwise all data is saved in the same folder.
        visibility_threshold:
            Objects with visibility below this threshold will be skipped.  Default: ``0.0`` (fully occluded)
        skip_empty_frames:
            If True, the writer will skip frames that do not have visible objects.
        write_debug_images:
            If True, the writer will include rgb images overlaid with the projected 3d bounding boxes.
        frame_padding:
            Pad the frame number with leading zeroes.  Default: ``4``
    """

    RGB_ANNOT_NAME = "rgb"
    BB3D_ANNOT_NAME = "bounding_box_3d_fast"
    CAM_PARAMS_ANNOT_NAME = "camera_params"

    def __init__(
        self,
        output_dir: str,
        use_subfolders: bool = False,
        visibility_threshold: float = 0.0,
        skip_empty_frames: bool = True,
        write_debug_images: bool = False,
        frame_padding: int = 4,
    ):
        self.version = __version__
        self._output_dir = output_dir
        self.backend = BackendDispatch({"paths": {"out_dir": output_dir}})
        self._use_subfolders = use_subfolders
        self._visibility_threshold = visibility_threshold
        self._skip_empty_frames = skip_empty_frames
        self._write_debug_images = write_debug_images
        self._frame_padding = frame_padding
        self._frame_id = 0

        # Use render product names and their multiple render product flag for convenient data access
        self._render_product_names = []
        self._multiple_render_products = False

        self.annotators = []
        self.annotators.append(AnnotatorRegistry.get_annotator(self.RGB_ANNOT_NAME))
        self.annotators.append(AnnotatorRegistry.get_annotator(self.BB3D_ANNOT_NAME))
        self.annotators.append(AnnotatorRegistry.get_annotator(self.CAM_PARAMS_ANNOT_NAME))

    def write(self, data: dict):
        # In case of multiple render products annotator names are suffixed with the render product name:
        # (e.g. 'rgb' -> 'rgb-{rp_name}')
        for rp_name in self._render_product_names:
            # Check if data should be split into subfolders
            rp_subfolder = f"{rp_name}/" if self._multiple_render_products and self._use_subfolders else ""

            # Write frame data: rgb, camera parameters, bounding box 3d, projected cuboid, etc.
            self._process_and_write_data_to_disk(data, rp_name, rp_subfolder)

        # If the data is split into subfolders, increment the frame id only once
        if self._use_subfolders:
            self._frame_id += 1

    # Extract the camera parameters from the data
    def _extract_camera_parameters(self, camera_params) -> dict:
        camera_data = {}
        camera_data["aperture"] = camera_params["cameraAperture"].tolist()
        camera_data["aperture_offset"] = camera_params["cameraApertureOffset"].tolist()
        camera_data["focal_length"] = float(camera_params["cameraFocalLength"])
        camera_data["view_transform"] = camera_params["cameraViewTransform"].reshape(4, 4).tolist()
        camera_data["projection_matrix"] = camera_params["cameraProjection"].reshape(4, 4).tolist()
        camera_data["fisheye_optical_centre"] = camera_params["cameraFisheyeOpticalCentre"].tolist()
        camera_data["fisheye_nominal_height"] = float(camera_params["cameraFisheyeNominalHeight"])
        camera_data["fisheye_nominal_width"] = float(camera_params["cameraFisheyeNominalWidth"])
        camera_data["resolution"] = camera_params["renderProductResolution"].tolist()
        camera_data["meters_per_scene_unit"] = float(camera_params["metersPerSceneUnit"])
        return camera_data

    # Project a 3D point in world coordinates into 2D screen coordinates
    def _project_world_point_to_screen(self, world_point, view_matrix, projection_matrix, screen_size):
        # Convert the 3D point to homogeneous coordinates (if not already in that form)
        if len(world_point) == 4:
            point_homogeneous = np.array(world_point)
        else:
            point_homogeneous = np.array([*world_point, 1.0])

        # Transform to camera frame (row-major representation where the translation vector is on the left side of the multiplication)
        point_camera = point_homogeneous @ view_matrix
        # point_camera = view_matrix.T @ point_homogeneous  # column-major alternative approach with the transpose

        # Apply the projection matrix to project into screen coordinates
        point_screen = point_camera @ projection_matrix
        # point_screen = np.dot(projection_matrix.T, point_camera)  # column-major alternative approach with the transpose

        # Normalize to NDC (Normalized Device Coordinates) by dividing x, y, z by w. Needed for 3D to 2D projection across various screen sizes/aspect ratios.
        point_screen_normalized = point_screen / point_screen[3]

        # Map NDC to screen coordinates. Adjust x and y for screen dimensions, flipping y to match screen's coordinate system.
        x = (point_screen_normalized[0] + 1) * screen_size[0] / 2
        y = (1 - point_screen_normalized[1]) * screen_size[1] / 2

        return int(x), int(y)

    # Process the bounding box data and extract the object's label, location, rotation, visibility, etc.
    def _process_bounding_boxes(self, bb3d_data, bb3d_info, camera_params) -> list:
        # Map class names from bbox annotator (e.g. 'idToLabels': {0: {'class': 'cube'}, 1: {'class': 'sphere'}} -> {0: 'cube', 1: 'sphere'})
        id_to_labels = {k: v["class"] for k, v in bb3d_info["idToLabels"].items()}

        objs = []
        # ("semanticId", "<u4"),        # Semantic identifier to map to label names using ["info"]["idToLabels"]
        # ("x_min", "<i4"), [..],       # Bounding box coordinates in local space
        # ("transform", "<i4"),         # Local to world transformation matrix (row-major)
        # ('occlusionRatio', '<f4')]),  # (visible pixels / total pixels), where `0.0` is fully visible and `1.0` is fully occluded.
        for i, bbox in enumerate(bb3d_data):
            obj = {}
            # Get the object's visibility first for early exit if the visibility is below the threshold
            obj_visibility = 1.0 - float(bbox["occlusionRatio"])
            if obj_visibility <= self._visibility_threshold:
                continue
            obj["class"] = id_to_labels[bbox["semanticId"]]
            obj["prim_path"] = bb3d_info["primPaths"][i]
            obj["visibility"] = obj_visibility

            # Local space to to world transform (row-major)
            local_to_world_tf = bbox["transform"]
            obj["local_to_world_transform"] = local_to_world_tf.tolist()

            # Extract world frame location (last row) and rotation matrix (3x3) from the row-major transform matrix
            location_world_frame = local_to_world_tf[3, :3]
            obj["location_world_frame"] = location_world_frame.tolist()
            rotation_matrix_world_frame = local_to_world_tf[:3, :3]
            obj["rotation_matrix_world_frame"] = rotation_matrix_world_frame.tolist()

            # Get the world frame quaternion using Gf.Transform (row-major)
            local_to_world_tf_gf = Gf.Transform()
            local_to_world_tf_gf.SetMatrix(Gf.Matrix4d(local_to_world_tf.tolist()))
            # location_world_frame_gf = local_to_world_tf_gf.GetTranslation()
            # obj["location_world_frame_gf"] = list(location_world_frame_gf)
            # rotation_matrix_world_frame_gf = local_to_world_tf_gf.GetMatrix().ExtractRotationMatrix()
            # obj["rotation_matrix_world_frame_gf"] = [list(rotation_matrix_world_frame_gf.GetRow(i)) for i in range(3)]
            quat_world_frame_gf = local_to_world_tf_gf.GetRotation().GetQuat()
            obj["quat_wxyz_world_frame"] = [quat_world_frame_gf.GetReal()] + list(quat_world_frame_gf.GetImaginary())

            # World to camera transform (row-major) (transform a point from world coordinate to camera coordinate)
            world_to_camera_tf = camera_params["cameraViewTransform"].reshape(4, 4)

            # Object world space to camera frame transform (row-major)
            obj_to_camera_tf = world_to_camera_tf @ local_to_world_tf
            obj["object_to_camera_transform"] = obj_to_camera_tf.tolist()

            # Extract camera frame location (last row) and rotation matrix (3x3) from the row-major transform matrix
            location_camera_frame = obj_to_camera_tf[3, :3]
            obj["location_camera_frame"] = location_camera_frame.tolist()
            rotation_matrix_camera_frame = obj_to_camera_tf[:3, :3]
            obj["rotation_matrix_camera_frame"] = rotation_matrix_camera_frame.tolist()

            # Get the camera frame quaternion using Gf.Transform (row-major)
            obj_to_camera_tf_gf = Gf.Transform()
            obj_to_camera_tf_gf.SetMatrix(Gf.Matrix4d(obj_to_camera_tf.tolist()))
            # location_camera_frame_gf = obj_to_camera_tf_gf.GetTranslation()
            # obj["location_camera_frame_gf"] = list(location_camera_frame_gf)
            # rotation_matrix_camera_frame_gf = obj_to_camera_tf_gf.GetMatrix().ExtractRotationMatrix()
            # obj["rotation_matrix_camera_frame_gf"] = [list(rotation_matrix_camera_frame_gf.GetRow(i)) for i in range(3)]
            quat_camera_frame_gf = obj_to_camera_tf_gf.GetRotation().GetQuat()
            obj["quat_wxyz_camera_frame"] = [quat_camera_frame_gf.GetReal()] + list(quat_camera_frame_gf.GetImaginary())

            #  Projected cuboid vertices (local -> world -> camera -> screen space) (8 corners + world location (center))
            vertices_screen = []

            # The resolution is used to map the Normalized Device Coordinates (NDC) to screen space
            screen_size = camera_params["renderProductResolution"]

            # Camera to screen space projection matrix (row-major)
            cam_projection_tf = camera_params["cameraProjection"].reshape((4, 4))

            # Transform the cuboid corners to world frame using row-major matrix multiplication (translation on the left side)
            corners_world = [
                np.array([bbox["x_min"], bbox["y_min"], bbox["z_min"], 1]) @ local_to_world_tf,  # LDB - Left Down Back
                np.array([bbox["x_min"], bbox["y_min"], bbox["z_max"], 1]) @ local_to_world_tf,  # LDF - Left Down Front
                np.array([bbox["x_min"], bbox["y_max"], bbox["z_min"], 1]) @ local_to_world_tf,  # LUB - Left Upper Back
                np.array([bbox["x_min"], bbox["y_max"], bbox["z_max"], 1])
                @ local_to_world_tf,  # LUF - Left Upper Front
                np.array([bbox["x_max"], bbox["y_min"], bbox["z_min"], 1]) @ local_to_world_tf,  # RDB - Right Down Back
                np.array([bbox["x_max"], bbox["y_min"], bbox["z_max"], 1])
                @ local_to_world_tf,  # RDF - Right Down Front
                np.array([bbox["x_max"], bbox["y_max"], bbox["z_min"], 1])
                @ local_to_world_tf,  # RUB - Right Upper Back
                np.array([bbox["x_max"], bbox["y_max"], bbox["z_max"], 1])
                @ local_to_world_tf,  # RUF - Right Upper Front
            ]

            # Project the cuboid corners from world space to screen space
            for vertex in corners_world:
                screen_point = self._project_world_point_to_screen(
                    vertex, world_to_camera_tf, cam_projection_tf, screen_size
                )
                vertices_screen.append(screen_point)

            # Project the objects world location to screen space (usually the center of the bounding box)
            location_screen_point = self._project_world_point_to_screen(
                location_world_frame, world_to_camera_tf, cam_projection_tf, screen_size
            )
            vertices_screen.append(location_screen_point)

            obj["projected_cuboid"] = vertices_screen
            objs.append(obj)
        return objs

    # Draws the objects local frame axes at the objects world location
    def _draw_local_frame_axes(
        self, draw, local_to_world_transform, camera_view_matrix, camera_projection_matrix, screen_size, axes_length=0.2
    ):
        # Define the end points of the local coordinate system axes
        x_axis_end_point_local = np.array([axes_length, 0, 0, 1])
        y_axis_end_point_local = np.array([0, axes_length, 0, 1])
        z_axis_end_point_local = np.array([0, 0, axes_length, 1])

        # Transform local end points to world frame using row-major matrix multiplication (translation on the left side)
        x_axis_end_point_world = x_axis_end_point_local @ local_to_world_transform
        y_axis_end_point_world = y_axis_end_point_local @ local_to_world_transform
        z_axis_end_point_world = z_axis_end_point_local @ local_to_world_transform

        # Define a partial helper function to project 3D world points to 2D screen points
        project_to_screen = partial(
            self._project_world_point_to_screen,
            view_matrix=camera_view_matrix,
            projection_matrix=camera_projection_matrix,
            screen_size=screen_size,
        )

        # Extract world location from the row-major transform matrix (last row)
        origin_world = local_to_world_transform[3]
        # Project the origin and axes end points from 3D world coordinates to 2D screen coordinates
        origin_2d = project_to_screen(origin_world)
        x_axis_end_2d = project_to_screen(x_axis_end_point_world)
        y_axis_end_2d = project_to_screen(y_axis_end_point_world)
        z_axis_end_2d = project_to_screen(z_axis_end_point_world)

        # Draw the 3D axes on the 2D screen using lines with appropriate colors for each axis
        draw.line([origin_2d, x_axis_end_2d], fill="red", width=2)  # X-axis in red
        draw.line([origin_2d, y_axis_end_2d], fill="green", width=2)  # Y-axis in green
        draw.line([origin_2d, z_axis_end_2d], fill="blue", width=2)  # Z-axis in blue

    # Draws the world frame axes at the bottom left corner of the image.
    def _draw_world_frame_axes_bottom_left(
        self, draw, camera_view_matrix, camera_projection_matrix, screen_size, axes_scale=75.0, margin_percentage=0.03
    ):
        # Skip if image too small
        if min(screen_size) < 32:
            print(f"Skipping drawing world frame axes due to small image size {screen_size}")
            return

        # Maintain a consistent axes length using the distance of the camera to the origin
        camera_to_world_matrix = np.linalg.inv(camera_view_matrix)
        camera_world_location = camera_to_world_matrix[3, :3]  # row-major representation
        camera_to_origin_distance = np.linalg.norm(camera_world_location)
        axes_length = camera_to_origin_distance / axes_scale

        # Define the origin and the end points of the axes in the world coordinate system
        origin = np.array([0, 0, 0])
        x_axis_end_point = np.array([axes_length, 0, 0])
        y_axis_end_point = np.array([0, axes_length, 0])
        z_axis_end_point = np.array([0, 0, axes_length])

        # Create a partial function with fixed camera parameters
        project_to_screen = partial(
            self._project_world_point_to_screen,
            view_matrix=camera_view_matrix,
            projection_matrix=camera_projection_matrix,
            screen_size=screen_size,
        )

        # Project the origin and axes end points into 2D screen coordinates
        origin_2d = project_to_screen(origin)
        x_axis_end_2d = project_to_screen(x_axis_end_point)
        y_axis_end_2d = project_to_screen(y_axis_end_point)
        z_axis_end_2d = project_to_screen(z_axis_end_point)

        # Calculate offset margin (a percentage of the screen size) to ensure axes are not on the edge of the screen
        margin = int(margin_percentage * min(screen_size))
        offset_x = margin - min(origin_2d[0], x_axis_end_2d[0], y_axis_end_2d[0], z_axis_end_2d[0])
        offset_y = screen_size[1] - margin - max(origin_2d[1], x_axis_end_2d[1], y_axis_end_2d[1], z_axis_end_2d[1])

        # Apply the offset to the projected points
        origin_2d = (origin_2d[0] + offset_x, origin_2d[1] + offset_y)
        x_axis_end_2d = (x_axis_end_2d[0] + offset_x, x_axis_end_2d[1] + offset_y)
        y_axis_end_2d = (y_axis_end_2d[0] + offset_x, y_axis_end_2d[1] + offset_y)
        z_axis_end_2d = (z_axis_end_2d[0] + offset_x, z_axis_end_2d[1] + offset_y)

        # Draw the axes with the specified colors
        draw.line([origin_2d, x_axis_end_2d], fill="red", width=2)  # X-axis in red
        draw.line([origin_2d, y_axis_end_2d], fill="green", width=2)  # Y-axis in green
        draw.line([origin_2d, z_axis_end_2d], fill="blue", width=2)  # Z-axis in blue

    # Draw the projected cuboid and its edges
    def _draw_projected_cuboid(self, draw, cuboid, point_colors=None, point_size=4, edge_colors=None, edge_size=2):
        # Validate vertex_colors input and use default if necessary
        if point_colors is None or len(point_colors) != 9:
            print(f"Using default cuboid colors due to missing or incomplete color data.")
            # LDB, LDF, LUB, LUF, RDB, RDF, RUB, RUF, Center (as object world Location)
            point_colors = ["red", "green", "blue", "yellow", "cyan", "magenta", "orange", "purple", "white"]

        # Validate edge_colors input and use default if necessary
        if edge_colors is None or len(edge_colors) != 3:
            print(f"Using default edge colors due to missing or incomplete edge color data.")
            edge_colors = {"front": "red", "back": "blue", "connecting": "green"}

        # Draw the projected cuboid vertices in the specified colors
        for i, point in enumerate(cuboid):
            draw.ellipse(
                (point[0] - point_size, point[1] - point_size, point[0] + point_size, point[1] + point_size),
                fill=point_colors[i],
            )

        # Define the edges of the cuboid using vertex indices
        edge_colors = {"front": "red", "back": "blue", "connecting": "green"}
        edges = {
            "front": [(0, 1), (1, 3), (3, 2), (2, 0)],  # Front face
            "back": [(4, 5), (5, 7), (7, 6), (6, 4)],  # Back face
            "connecting": [(0, 4), (1, 5), (2, 6), (3, 7)],  # Connecting edges
        }

        # Draw the edges of the projected cuboid with specified colors for each set
        for edge_type, edge_list in edges.items():
            for start, end in edge_list:
                draw.line(cuboid[start] + cuboid[end], fill=edge_colors[edge_type], width=edge_size)

    # Write data to disk
    def _write_data_to_disk(self, frame_entries, rgb_data, render_product_subfolder: str = ""):
        # Frame data
        file_path = f"{render_product_subfolder}{self._frame_id:0{self._frame_padding}}.json"
        self.backend.schedule(write_json, path=file_path, data=frame_entries, indent=2)

        # RGB
        file_path = f"{render_product_subfolder}{self._frame_id:0{self._frame_padding}}.png"
        self.backend.schedule(write_image, path=file_path, data=rgb_data)

        # Debug overlays
        if self._write_debug_images:
            # Create overlay image from the RGB data
            rgb_img = Image.fromarray(rgb_data)
            draw = ImageDraw.Draw(rgb_img)

            # Get the camera and image parameters
            camera_projection_matrix = np.array(frame_entries["camera_data"]["projection_matrix"])
            camera_view_matrix = np.array(frame_entries["camera_data"]["view_transform"])
            screen_size = frame_entries["camera_data"]["resolution"]

            # Overlay the world frame axes on the bottom left part of the RGB image
            self._draw_world_frame_axes_bottom_left(draw, camera_view_matrix, camera_projection_matrix, screen_size)

            # Define the colors for the projected cuboid vertices and edges
            # LDB, LDF, LUB, LUF, RDB, RDF, RUB, RUF, Center (as object world Location)
            point_colors = ["red", "green", "blue", "yellow", "cyan", "magenta", "orange", "purple", "white"]
            edge_colors = {"front": "red", "back": "blue", "connecting": "green"}

            # Iterate objects and draw the projected cuboid and local frame axes
            for obj in frame_entries["objects"]:
                cuboid = obj["projected_cuboid"]

                # Draw the projected cuboid and its edges
                self._draw_projected_cuboid(draw, cuboid, point_colors=point_colors, edge_colors=edge_colors)

                # Draw local frame axes
                obj_world_frame_tf = np.array(obj["local_to_world_transform"])
                self._draw_local_frame_axes(
                    draw, obj_world_frame_tf, camera_view_matrix, camera_projection_matrix, screen_size
                )

            file_path = f"{render_product_subfolder}{self._frame_id:0{self._frame_padding}}_overlay.png"
            self.backend.schedule(write_image, path=file_path, data=np.asarray(rgb_img))

    # Process the frame data and write to disk
    def _process_and_write_data_to_disk(self, data: dict, render_product_name: str, render_product_subfolder: str = ""):
        frame_entries = {}

        # Get the camera parameters
        camera_params_annot_name = (
            f"{self.CAM_PARAMS_ANNOT_NAME}-{render_product_name}"
            if self._multiple_render_products
            else self.CAM_PARAMS_ANNOT_NAME
        )
        camera_params = data[camera_params_annot_name]
        frame_entries["camera_data"] = self._extract_camera_parameters(camera_params)

        # Get the bounding box 3d data
        bb3d_annot_name = (
            f"{self.BB3D_ANNOT_NAME}-{render_product_name}" if self._multiple_render_products else self.BB3D_ANNOT_NAME
        )
        bb3d_data = data[bb3d_annot_name]["data"]
        bb3d_info = data[bb3d_annot_name]["info"]
        objs = self._process_bounding_boxes(bb3d_data, bb3d_info, camera_params)

        # Check if the frame should be skipped if there are no visible objects
        if self._skip_empty_frames and len(objs) == 0:
            return

        # Add the objects to the frame entries
        frame_entries["objects"] = objs

        # RGB data
        rgb_annot_name = (
            f"{self.RGB_ANNOT_NAME}-{render_product_name}" if self._multiple_render_products else self.RGB_ANNOT_NAME
        )
        rgb_data = data[rgb_annot_name]

        # Write the data (frame, rgb, debug rgb) to disk
        self._write_data_to_disk(frame_entries, rgb_data, render_product_subfolder)

        # Increment the frame id for every frame if not using subfolders (otherwise once per step outside of this function)
        if not self._use_subfolders:
            self._frame_id += 1

    # Override to cache the render product names
    def attach(self, render_products, trigger="omni.replicator.core.OgnOnFrame"):
        super().attach(render_products, trigger)
        self._cache_render_product_names(render_products)

    # Override to clear the writer state
    def detach(self):
        super().detach()
        self._reset_writer_state()

    # Save the render product names for easier data access in the write function
    def _cache_render_product_names(self, render_products):
        if not isinstance(render_products, list):
            render_products = [render_products]
        for rp in render_products:
            rp_name = rp.path.split("/Render/")[-1]
            self._render_product_names.append(rp_name)
        # Check if there are multiple render products, this is used to suffix the annotator names for data access
        self._multiple_render_products = len(self._render_product_names) > 1

    # Reset the writer state
    def _reset_writer_state(self):
        self._render_product_names = []
        self._frame_id = 0
        self._multiple_render_products = False


WriterRegistry.register(PoseWriter)
