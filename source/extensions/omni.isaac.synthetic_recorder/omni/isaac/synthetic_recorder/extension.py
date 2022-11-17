# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import gc
import time
import asyncio
import json
import carb
import carb.events
import omni.kit.ui
import omni.kit.actions.core
import omni.timeline
import omni.ui as ui
import omni.replicator.core as rep
from omni.kit.viewport.utility import get_active_viewport
from omni.kit.window.extensions.utils import open_file_using_os_default
from omni.replicator.core import orchestrator
from omni.replicator.core.scripts.orchestrator import _Orchestrator
from functools import lru_cache
from enum import Enum

EXTENSION_NAME = "Synthetic Data Recorder"
SYNTHETIC_RECORDER_MENU_PATH = f"Synthetic Data/{EXTENSION_NAME}"

PARAM_TOOLTIPS = {
    "rgb": "Produces an array of type np.uint8 with shape (width, height, 4), where the four channels correspond to R,G,B,A.",
    "bounding_box_2d_tight": "Outputs tight 2d bounding box of each entity with semantics in the camera's viewport.\nTight bounding boxes bound only the visible pixels of entities.\nCompletely occluded entities are ommited.\nBounds only visible pixels.",
    "bounding_box_2d_loose": "Outputs loose 2d bounding box of each entity with semantics in the camera's field of view.\nLoose bounding boxes bound the entire entity regardless of occlusions.\nWill produce the loose 2d bounding box of any prim in the viewport, no matter if is partially occluded or fully occluded.",
    "semantic_segmentation": "Outputs semantic segmentation of each entity in the camera's viewport that has semantic labels.\nIf colorize is set to True (mapping from color to semantic labels), the image will be a 2d array of types np.uint8 with 4 channels.\nIf colorize is set to False (mapping from semantic id to semantic labels), the image will be a 2d array of types np.uint32 with 1 channel, which is the semantic id of the entities.",
    "colorize_semantic_segmentation": "If True, semantic segmentation is converted to an image where semantic ids are mapped to colors and saved as a uint8 4 channel PNG image.\nIf False, the output is saved as a uint32 PNG image.",
    "instance_id_segmentation": "Outputs instance id segmentation of each entity in the camera's viewport.\nThe instance id is unique for each prim in the scene with different paths.\nIf colorize is set to True (mapping from color to usd prim path of that entity), the image will be a 2d array of types np.uint8 with 4 channels.\nIf colorize is set to False (mapping from instance id to usd prim path of that entity), the image will be a 2d array of types np.uint32 with 1 channel, which is the instance id of the entities.",
    "colorize_instance_id_segmentation": "If True, instance id segmentation is converted to an image where instance ids are mapped to colors and saved as a uint8 4 channel PNG image.\nIf False, the output is saved as a uint32 PNG image.",
    "instance_segmentation": "Outputs instance segmentation of each entity in the camera' viewport.\nThe main difference between instance id segmentation and instance segmentation are that instance segmentation annotator goes down the hierarchy to the lowest level prim which has semantic labels,\n whereas instance id segmentation always goes down to the leaf prim.\nIf colorize is set to True (mapping from color to usd prim path of that semantic entity), the image will be a 2d array of types np.uint8 with 4 channels.\nIf colorize is set to False (mapping from instance id to usd prim path of that semantic entity), the image will be a 2d array of types np.uint32 with 1 channel, which is the instance id of the semantic entities.",
    "colorize_instance_segmentation": "If True, instance segmentation is converted to an image where instance are mapped to colors and saved as a uint8 4 channel PNG image.\nIf False, the output is saved as a uint32 PNG image.",
    "distance_to_camera": "Outputs a depth map from objects to camera positions.\nProduces a 2d array of types np.float32 with 1 channel.",
    "distance_to_image_plane": "Outputs a depth map from objects to image plane of the camera.\nProduces a 2d array of types np.float32 with 1 channel.",
    "bounding_box_3d": "Outputs 3D bounding box of each entity with semantics in the camera's viewport, generated regardless of occlusion.",
    "occlusion": "Outputs the occlusion of each entity in the camera's viewport.\nContains the instanceId, semanticId and the occlusionRation.",  # TODO: check and add more details
    "normals": "Produces an array of type np.float32 with shape (height, width, 4).\nThe first three channels correspond to (x, y, z).\nThe fourth channel is unused.",
    "motion_vectors": "Outputs a 2D array of motion vectors representing the relative motion of a pixel in the camera's viewport between frames.\nProduces a 2darray of types np.float32 with 4 channels.\nEach value is a normalized direction in 3D space.\nThe values represent motion relative to camera space.",
    "camera_params": "Outputs the camera model (pinhole or fisheye models), view matrix, projection matrix, fisheye nominal width/height, fisheye optical centre, fisheye maximum field of view, fisheye polynomial, near/far clipping range.",
    "pointcloud": "Outputs a 2D array of shape (N, 3) representing the points sampled on the surface of the prims in the viewport, where N is the number of point.\nPoint positions are in the world space.\nSample resolution is determined by the resolution of the render product.\nTo get the mapping from semantic id to semantic labels, pointcloud annotator is better used with semantic segmentation annotator, and users can extract the idToLabels data from the semantic segmentation annotator.",
    "skeleton_data": "Retrieves skeleton data given skeleton prims and camera paramters",  # TODO: check and add more details
    "s3_bucket": "The S3 Bucket name to write to. If not provided, disk backend will be used instead.\nThis backend requires that AWS credentials are set up in ~/.aws/credentials.",
    "s3_region": "If provided, this is the region the S3 bucket will be set to. Default: us-east-1",
    "s3_endpoint": "Gateway endpoint for Amazon S3",
}

ORCHESTRATOR_EVENT_NAME = carb.events.type_from_string("omni.replicator.core.orchestrator")


class OutWriteType(Enum):
    OVERWRITE = 0
    INCREMENT = 1
    TIMESTAMP = 2


@lru_cache()
def _ui_get_delete_glyph():
    return omni.ui.get_custom_glyph_code("${glyphs}/menu_delete.svg")


@lru_cache()
def _ui_get_open_folder_glyph():
    return omni.ui.get_custom_glyph_code("${glyphs}/folder_open.svg")


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        """Caled to load the extension"""

        self._window = ui.Window(EXTENSION_NAME, dockPreference=ui.DockPreference.RIGHT_BOTTOM, visible=True)
        self._window.deferred_dock_in("Property", omni.ui.DockPolicy.DO_NOTHING)

        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            self._menu = editor_menu.add_item(SYNTHETIC_RECORDER_MENU_PATH, self._menu_callback)

        self._writer_name = "BasicWriter"
        self._writer = None
        self._num_frames = 0
        self._counter = 0
        self._rt_subframes = 0
        self._reset_timeline = True

        self._orchestrator_status = rep.orchestrator.get_status()
        self._enable_buttons_at_status = None

        # Subscribers
        _Orchestrator()._register_status_callback(self._on_orchestrator_status_changed)
        self._sub_orchestrator_message = None
        # self._sub_orchestrator_event = None

        self._sub_stage_event = (
            omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(self._on_stage_event)
        )

        self._sub_shutdown = (
            omni.kit.app.get_app()
            .get_shutdown_event_stream()
            .create_subscription_to_pop_by_type(
                omni.kit.app.POST_QUIT_EVENT_TYPE,
                self._on_editor_quit_event,
                name="omni.isaac.synthetic_recorder::shutdown_callback",
                order=0,
            )
        )

        self._config_dir = os.path.abspath(
            os.path.join(omni.kit.app.get_app().get_extension_manager().get_extension_path(ext_id), "data", "")
        )
        self._last_config_path = os.path.join(self._config_dir, "last_config.json")
        self._config_file = "custom_config.json"
        self._out_working_dir = os.getcwd() + "/"
        self._out_dir = "_out_sdrec"
        self._out_write_type = OutWriteType.OVERWRITE
        self._s3_params = {"s3_bucket": "", "s3_region": "", "s3_endpoint": ""}

        self._annot_params = {
            "rgb": True,
            "bounding_box_2d_tight": False,
            "bounding_box_2d_loose": False,
            "semantic_segmentation": False,
            "colorize_semantic_segmentation": False,
            "instance_id_segmentation": False,
            "colorize_instance_id_segmentation": False,
            "instance_segmentation": False,
            "colorize_instance_segmentation": False,
            "distance_to_camera": False,
            "distance_to_image_plane": False,
            "bounding_box_3d": False,
            "occlusion": False,
            "normals": False,
            "motion_vectors": False,
            "camera_params": False,
            "pointcloud": False,
            "skeleton_data": False,
        }
        self._render_products = []
        self._rp_data = [["/OmniverseKit_Persp", 512, 512]]

        # UI - frames collapsed state
        self._config_frame_collapsed = True
        self._writer_frame_collapsed = False
        self._output_frame_collapsed = False
        self._annot_params_frame_collapsed = True
        self._s3_params_frame_collapsed = True
        self._rp_frame_collapsed = False
        self._control_frame_collapsed = False
        self._control_params_frame_collapsed = False
        self._manual_control_frame_collapsed = True

        # UI - Buttons
        self._start_stop_button = None
        self._pause_resume_button = None
        self._manual_init_clear_button = None
        self._manual_preview_button = None
        self._manual_step_button = None
        self._manual_step_n_button = None

        # Load latest or default config values
        if os.path.isfile(self._last_config_path):
            self.load_config(self._last_config_path)
        else:
            self.load_config(os.path.join(self._config_dir, "default_config.json"))

        # Build the window ui
        self._build_window_ui()

    def _menu_callback(self, menu, value):
        self._window.visible = not self._window.visible

    def _on_orchestrator_status_changed(self, status):
        new_status = status is not self._orchestrator_status
        if new_status:
            self._orchestrator_status = status
            if self._enable_buttons_at_status is not None:
                if self._enable_buttons_at_status is rep.orchestrator.Status.STARTED:
                    self._enable_buttons_at_status = None
                    self._enable_buttons(case="start")
                elif self._enable_buttons_at_status is rep.orchestrator.Status.STOPPED:
                    self._enable_buttons_at_status = None
                    self._enable_buttons(case="stop")

    def _on_stage_event(self, e: carb.events.IEvent):
        if e.type == int(omni.usd.StageEventType.CLOSING):
            self._disable_all_buttons()
            if self._orchestrator_status is not orchestrator.Status.STOPPED:
                rep.orchestrator.stop()
            self._clear_writer()
            self._enable_buttons(case="reset")

    def _on_editor_quit_event(self, e: carb.events.IEvent):
        if self._orchestrator_status is not orchestrator.Status.STOPPED:
            rep.orchestrator.stop()
            self._clear_writer()
        self.save_config(self._last_config_path)

    def on_shutdown(self):
        """Called when the extesion is unloaded"""
        if self._orchestrator_status is not orchestrator.Status.STOPPED:
            rep.orchestrator.stop()
            self._clear_writer()
        self.save_config(self._last_config_path)
        self._window = None
        self._menu = None
        gc.collect()

    def _open_dir(self, path):
        if not os.path.isdir(path):
            carb.log_warn(f"Could not open directory {path}.")
            return
        open_file_using_os_default(path)

    def load_config(self, path):
        if not os.path.isfile(path):
            carb.log_warn(f"Could not find config file {path}.")
            return
        with open(path, "r") as f:
            config = json.load(f)
            if "writer_name" in config:
                self._writer_name = config["writer_name"]
            if "num_frames" in config:
                self._num_frames = config["num_frames"]
            if "rt_subframes" in config:
                self._rt_subframes = config["rt_subframes"]
            if "reset_timeline" in config:
                self._reset_timeline = config["reset_timeline"]
            if "config_dir" in config:
                self._config_dir = config["config_dir"]
            if "config_file" in config:
                self._config_file = config["config_file"]
            if "out_working_dir" in config:
                self._out_working_dir = config["out_working_dir"]
            if "out_dir" in config:
                self._out_dir = config["out_dir"]
            if "out_write_type" in config:
                self._out_write_type = OutWriteType[config["out_write_type"]]
            if "s3_params" in config:
                self._s3_params = config["s3_params"]
            if "annot_params" in config:
                self._annot_params = config["annot_params"]
            if "rp_data" in config:
                self._rp_data = config["rp_data"]

    def _load_config_and_refresh_ui(self, directory, filename):
        self.load_config(os.path.join(directory, filename))
        self._build_window_ui()

    def save_config(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.isfile(path):
            carb.log_info(f"Overwriting config file {path}.")
        with open(path, "w") as json_file:
            json.dump(
                {
                    "writer_name": self._writer_name,
                    "num_frames": self._num_frames,
                    "rt_subframes": self._rt_subframes,
                    "reset_timeline": self._reset_timeline,
                    "config_dir": self._config_dir,
                    "config_file": self._config_file,
                    "out_working_dir": self._out_working_dir,
                    "out_dir": self._out_dir,
                    "out_write_type": self._out_write_type.name,
                    "s3_params": self._s3_params,
                    "annot_params": self._annot_params,
                    "rp_data": self._rp_data,
                },
                json_file,
                indent=4,
            )

    def _get_dir_next_numerical_suffix(self, path, dir_name):
        nums = [-1]
        for file in os.listdir(path):
            if file.startswith(dir_name) and os.path.isdir(os.path.join(path, file)):
                file = file[len(dir_name) :]
                file = file.replace("_", "")
                if file.isdecimal():
                    nums.append(int(file))
        suffix = "_" + str(max(nums) + 1)
        return suffix

    def _get_output_dir(self):
        out_dir = self._out_dir
        if self._out_write_type is OutWriteType.INCREMENT:
            out_dir = out_dir + self._get_dir_next_numerical_suffix(self._out_working_dir, out_dir)
        elif self._out_write_type is OutWriteType.TIMESTAMP:
            out_dir = out_dir + time.strftime("_%Y-%m-%d-%H-%M-%S")
        return os.path.join(self._out_working_dir, out_dir, "")

    def _check_if_valid_camera(self, path):
        context = omni.usd.get_context()
        if context.get_stage().GetPrimAtPath(path).GetTypeName() == "Camera":
            return True
        else:
            carb.log_warn(f"{path} is not a valid 'Camera' prim path.")
            return False

    def _check_if_valid_rp_entry(self, entry):
        if (
            len(entry) == 3
            and type(entry[0]) == str
            and type(entry[1]) == int
            and type(entry[2]) == int
            and self._check_if_valid_camera(entry[0])
            and entry[1] > 0
            and entry[2] > 0
        ):
            return True
        else:
            carb.log_warn(f"Entry data {entry} is not a valid to generate a render product.")
            return False

    def _update_rp_entry(self, idx, field, value):
        self._rp_data[idx][field] = value

    def _remove_rp_entry(self, idx):
        del self._rp_data[idx]
        self._build_window_ui()

    def _add_new_rp_field(self):
        # If cameras are selected in the stage viewer use them default values
        context = omni.usd.get_context()
        stage = context.get_stage()
        selected_prims = context.get_selection().get_selected_prim_paths()
        selected_cameras = [path for path in selected_prims if stage.GetPrimAtPath(path).GetTypeName() == "Camera"]

        if selected_cameras:
            for path in selected_cameras:
                self._rp_data.append([path, 512, 512])
        else:
            # Use selected viewport camera as default value
            active_vp = get_active_viewport()
            active_cam = active_vp.get_active_camera()
            self._rp_data.append([str(active_cam), 512, 512])

        self._build_window_ui()

    def _on_orchestrator_message(self, event):
        if event is None:
            return
        payload_dict = event.payload.get_dict()
        # if "trigger_frame" in payload_dict:
        #     self._counter += 1
        if "swhFrameNumber" in payload_dict:
            self._counter += 1
        # FIXME: Getting one frame less than expected (for RTSubframes 0 or 1), so adding 1 to the counter
        if self._rt_subframes > 1:
            if self._counter > self._num_frames:
                self._sub_orchestrator.unsubscribe()
                self._sub_orchestrator = None
                self._counter = 0
                self._disable_all_buttons()
                rep.orchestrator.stop()
                self._clear_writer()
                self._enable_buttons_at_status = orchestrator.Status.STOPPED
                if self._reset_timeline:
                    omni.timeline.get_timeline_interface().set_current_time(0.0)
        else:
            if self._counter > self._num_frames + 1:
                self._sub_orchestrator.unsubscribe()
                self._sub_orchestrator = None
                self._counter = 0
                self._disable_all_buttons()
                rep.orchestrator.stop()
                self._clear_writer()
                self._enable_buttons_at_status = orchestrator.Status.STOPPED
                if self._reset_timeline:
                    omni.timeline.get_timeline_interface().set_current_time(0.0)

    def _on_orchestrator_event(self, event):
        if event is None:
            return
        payload_dict = event.payload.get_dict()

    def _subscribe_to_orchestrator_message_bus(self):
        if self._sub_orchestrator_message is None:
            # Pop subscription to orchestrator events, expect a 1-frame lag between send and receive
            self._sub_orchestrator = (
                omni.kit.app.get_app()
                .get_message_bus_event_stream()
                .create_subscription_to_pop_by_type(ORCHESTRATOR_EVENT_NAME, self._on_orchestrator_message)
            )

    def _subscribe_to_orchestrator_event_stream(self):
        if self._sub_orchestrator_event is None:
            self._sub_orchestrator_event = (
                omni.kit.app.get_app()
                .get_update_event_stream()
                .create_subscription_to_pop(self._on_orchestrator_event, name="omni.replicator.core.orchestrator")
            )

    def _clear_writer(self):
        if self._writer:
            self._writer.detach()
            self._writer = None
        self._render_products.clear()

    def _init_writer(self):
        if self._writer is None:
            self._writer = rep.WriterRegistry.get(self._writer_name)

        # Set the number of subframes
        if self._rt_subframes != carb.settings.get_settings().get("/omni/replicator/RTSubframes"):
            rep.settings.carb_settings("/omni/replicator/RTSubframes", self._rt_subframes)
            carb.log_info(f"Setting 'RTSubframes' to {self._rt_subframes}.")

        # Get the init parameters (output directory, annotators, s3 bucket, etc)
        output_dir = self._get_output_dir()
        all_params = {**self._annot_params, **self._s3_params}

        # Init the writer
        self._writer.initialize(output_dir=output_dir, **all_params)

        # Create the render products
        if not self._render_products:
            for rp_entry in self._rp_data:
                if self._check_if_valid_rp_entry(rp_entry):
                    rp = rep.create.render_product(rp_entry[0], (rp_entry[1], rp_entry[2]))
                    self._render_products.append(rp)

        # Attach the render products to the writer
        self._writer.attach(self._render_products)

    def _start_stop_writer(self):
        if self._reset_timeline:
            omni.timeline.get_timeline_interface().set_current_time(0.0)
        if self._orchestrator_status is orchestrator.Status.STOPPED:
            self._disable_all_buttons()
            self._init_writer()
            if self._num_frames > 0:
                self._subscribe_to_orchestrator_message_bus()
            rep.orchestrator.run()
            self._enable_buttons_at_status = orchestrator.Status.STARTED
        elif self._orchestrator_status in [orchestrator.Status.STARTED, orchestrator.Status.PAUSED]:
            self._disable_all_buttons()
            rep.orchestrator.stop()
            self._clear_writer()
            self._enable_buttons_at_status = orchestrator.Status.STOPPED
        else:
            carb.log_warn(
                f"Replicator's current state({self._orchestrator_status.name}) is different state than STOPPED, STARTED or PAUSED. Try again in a bit."
            )

    async def _start_stop_writer_async(self, wait_time=0.0):
        if self._reset_timeline:
            await self._reset_timeline_async()
        if self._orchestrator_status is orchestrator.Status.STOPPED:
            self._disable_all_buttons()
            self._init_writer()
            if self._num_frames > 0:
                self._subscribe_to_orchestrator_message_bus()
            rep.orchestrator.run()
            await asyncio.sleep(wait_time)
            self._enable_buttons(case="start")
        elif self._orchestrator_status in [orchestrator.Status.STARTED, orchestrator.Status.PAUSED]:
            self._disable_all_buttons()
            rep.orchestrator.stop()
            await asyncio.sleep(wait_time)
            self._clear_writer()
            self._enable_buttons(case="stop")
        else:
            carb.log_warn(
                f"Replicator's current state({self._orchestrator_status.name}) is different state than STOPPED, STARTED or PAUSED. Try again in a bit."
            )

    def _pause_resume_writer(self):
        self._pause_resume_button.enabled = False
        if self._orchestrator_status is orchestrator.Status.STARTED:
            rep.orchestrator.pause()
            self._pause_resume_button.text = "Resume"
        elif self._orchestrator_status is orchestrator.Status.PAUSED:
            rep.orchestrator.resume()
            self._pause_resume_button.text = "Pause"
        else:
            carb.log_warn(
                f"Replicator's current state (({self._orchestrator_status.name})) is different state than STARTED or PAUSED. Try again in a bit."
            )
        self._pause_resume_button.enabled = True

    def _manual_init_clear(self):
        if self._reset_timeline:
            omni.timeline.get_timeline_interface().set_current_time(0.0)
        self._disable_all_buttons()
        if self._writer is None:
            self._init_writer()
            self._enable_buttons(case="manual_init")
        else:
            if self._orchestrator_status is not orchestrator.Status.STOPPED:
                rep.orchestrator.stop()
            self._clear_writer()
            self._enable_buttons(case="manual_clear")

    async def _manual_init_clear_async(self, wait_time=0.0):
        if self._reset_timeline:
            await self._reset_timeline_async()
        self._disable_all_buttons()
        if self._writer is None:
            self._init_writer()
            await asyncio.sleep(wait_time)
            self._enable_buttons(case="manual_init")
        else:
            if self._orchestrator_status is not orchestrator.Status.STOPPED:
                rep.orchestrator.stop()
            await asyncio.sleep(wait_time)
            self._clear_writer()
            self._enable_buttons(case="manual_clear")

    def _disable_all_buttons(self):
        self._start_stop_button.enabled = False
        self._pause_resume_button.enabled = False
        self._manual_init_clear_button.enabled = False
        self._manual_preview_button.enabled = False
        self._manual_step_button.enabled = False
        self._manual_step_n_button.enabled = False

    def _enable_buttons(self, case="reset"):
        if case == "reset":
            self._start_stop_button.enabled = True
            self._start_stop_button.text = "Start"
            self._manual_init_clear_button.enabled = True
            self._manual_init_clear_button.text = "Init"
            self._pause_resume_button.text = "Pause"
        elif case == "manual_init":
            self._manual_init_clear_button.text = "Clear"
            self._manual_init_clear_button.enabled = True
            self._manual_preview_button.enabled = True
            self._manual_step_button.enabled = True
            self._manual_step_n_button.enabled = True
        elif case == "manual_clear":
            self._manual_init_clear_button.text = "Init"
            self._manual_init_clear_button.enabled = True
            self._start_stop_button.enabled = True
        elif case == "start":
            self._start_stop_button.text = "Stop"
            self._start_stop_button.enabled = True
            self._pause_resume_button.enabled = True
        elif case == "stop" or case == "sub_stop":
            self._start_stop_button.text = "Start"
            self._pause_resume_button.text = "Pause"
            self._start_stop_button.enabled = True
            self._manual_init_clear_button.enabled = True

    async def _reset_timeline_async(self):
        await omni.kit.app.get_app().next_update_async()
        await asyncio.sleep(0.05)
        omni.timeline.get_timeline_interface().set_current_time(0.0)

    def _manual_preview(self):
        rep.orchestrator.preview()

    async def _manual_step_async(self):
        self._manual_step_button.enabled = False
        await rep.orchestrator.step_async()
        self._manual_step_button.enabled = True

    async def _manual_step_n_async(self):
        self._manual_step_n_button.enabled = False
        for _ in range(self._num_frames):
            await rep.orchestrator.step_async()
        self._manual_step_n_button.enabled = True

    def _build_config_ui(self):
        with ui.VStack(spacing=5):
            with ui.HStack():
                ui.Spacer(width=10)
                ui.Label("Config Directory", tooltip="Directory where config files are stored")
            with ui.HStack():
                ui.Spacer(width=10)
                config_dir_model = ui.StringField().model
                config_dir_model.set_value(self._config_dir)

                def config_dir_changed(model):
                    self._config_dir = model.as_string

                config_dir_model.add_value_changed_fn(config_dir_changed)

                ui.Button(
                    f"{_ui_get_open_folder_glyph()}",
                    width=30,
                    clicked_fn=lambda: self._open_dir(self._config_dir),
                    tooltip="Open config directory",
                )

            with ui.HStack(spacing=5):
                ui.Spacer(width=10)
                config_file_model = ui.StringField(tooltip="Config file name").model
                config_file_model.set_value(self._config_file)

                def config_file_changed(model):
                    self._config_file = model.as_string

                config_file_model.add_value_changed_fn(config_file_changed)

                ui.Button(
                    "Load",
                    clicked_fn=lambda: self._load_config_and_refresh_ui(self._config_dir, self._config_file),
                    tooltip="Load recorder configuration file",
                )
                ui.Button(
                    "Save",
                    clicked_fn=lambda: self.save_config(os.path.join(self._config_dir, self._config_file)),
                    tooltip="Save recorder configuration to file",
                )

    def _build_s3_ui(self):
        with ui.VStack(spacing=5):
            for key, val in self._s3_params.items():
                with ui.HStack():
                    ui.Spacer(width=10)
                    ui.Label(key, alignment=ui.Alignment.LEFT, tooltip=PARAM_TOOLTIPS[key])
                    model = ui.StringField().model
                    model.set_value(val)

                    def value_changed(m, k=key):
                        self._s3_params[k] = m.as_string

                    model.add_value_changed_fn(value_changed)

    def _build_output_ui(self):
        with ui.VStack(spacing=5):
            with ui.HStack():
                ui.Spacer(width=10)
                ui.Label("Working Directory")
            with ui.HStack():
                ui.Spacer(width=10)
                out_working_dir_model = ui.StringField().model
                out_working_dir_model.set_value(self._out_working_dir)

                def out_working_dir_changed(model):
                    self._out_working_dir = model.as_string

                out_working_dir_model.add_value_changed_fn(out_working_dir_changed)

                ui.Button(
                    f"{_ui_get_open_folder_glyph()}",
                    width=30,
                    clicked_fn=lambda: self._open_dir(self._out_working_dir),
                    tooltip="Open working directory",
                )

            with ui.HStack(spacing=5):
                ui.Spacer(width=10)
                out_dir_model = ui.StringField().model
                out_dir_model.set_value(self._out_dir)

                def out_dir_changed(model):
                    self._out_dir = model.as_string

                out_dir_model.add_value_changed_fn(out_dir_changed)

                write_collection = ui.RadioCollection()
                write_collection.model.set_value(self._out_write_type.value)

                def write_collection_changed(model):
                    self._out_write_type = OutWriteType(model.as_int)

                write_collection.model.add_value_changed_fn(write_collection_changed)

                ui.RadioButton(
                    text="Overwrite",
                    radio_collection=write_collection,
                    tooltip="Overwrite data if output folder already exists",
                )
                ui.RadioButton(
                    text="Increment",
                    radio_collection=write_collection,
                    tooltip="Append numerical increments to output folder (e.g., _01, _02)",
                )
                ui.RadioButton(
                    text="Timestamp",
                    radio_collection=write_collection,
                    tooltip="Append timestamp to output folder (e.g., _YYYY-mm-dd-HH-MM-SS)",
                )

            s3_frame = ui.CollapsableFrame("S3 Bucket", height=0, collapsed=self._s3_params_frame_collapsed)
            with s3_frame:

                def on_collapsed_changed(collapsed):
                    self._s3_params_frame_collapsed = collapsed

                s3_frame.set_collapsed_changed_fn(on_collapsed_changed)
                self._build_s3_ui()

    def _build_rp_ui(self):
        with ui.VStack(spacing=5):
            with ui.HStack(spacing=5):
                ui.Spacer(width=15)
                ui.Label("Camera Path", width=200, tooltip="Camera prim to be used as a render product")
                ui.Spacer(width=15)
                ui.Label("X", tooltip="X resolution of the render product")
                ui.Spacer(width=15)
                ui.Label("Y", tooltip="Y resolution of the render product")
            for i, entry in enumerate(self._rp_data):
                with ui.HStack(spacing=5):
                    ui.Spacer(width=10)
                    path_field_model = ui.StringField(width=200).model
                    path_field_model.set_value(entry[0])
                    path_field_model.add_value_changed_fn(lambda m, idx=i: self._update_rp_entry(idx, 0, m.as_string))
                    ui.Spacer(width=10)
                    x_field = ui.IntField()
                    x_field.model.set_value(entry[1])
                    x_field.model.add_value_changed_fn(lambda m, idx=i: self._update_rp_entry(idx, 1, m.as_int))
                    ui.Spacer(width=10)
                    y_field = ui.IntField()
                    y_field.model.set_value(entry[2])
                    y_field.model.add_value_changed_fn(lambda m, idx=i: self._update_rp_entry(idx, 2, m.as_int))
                    ui.Button(
                        f"{_ui_get_delete_glyph()}",
                        width=30,
                        clicked_fn=lambda idx=i: self._remove_rp_entry(idx),
                        tooltip="Remove entry",
                    )
            with ui.HStack(spacing=5):
                ui.Spacer(width=10)
                ui.Button("Add New Render Product", clicked_fn=self._add_new_rp_field, tooltip="Create a new entry")

    def _build_annotator_ui(self):
        with ui.VStack(spacing=5):
            for key, val in self._annot_params.items():
                with ui.HStack():
                    ui.Spacer(width=10)
                    ui.Label(key, alignment=ui.Alignment.LEFT, tooltip=PARAM_TOOLTIPS[key])
                    model = ui.CheckBox().model
                    model.set_value(val)

                    def value_changed(m, k=key):
                        self._annot_params[k] = m.as_bool

                    model.add_value_changed_fn(value_changed)

    def _build_writer_ui(self):
        with ui.VStack(spacing=5):
            config_frame = ui.CollapsableFrame("Config", height=0, collapsed=self._config_frame_collapsed)
            with config_frame:

                def on_collapsed_changed(collapsed):
                    self._config_frame_collapsed = collapsed

                config_frame.set_collapsed_changed_fn(on_collapsed_changed)
                self._build_config_ui()

            output_frame = ui.CollapsableFrame("Output", height=0, collapsed=self._output_frame_collapsed)
            with output_frame:

                def on_collapsed_changed(collapsed):
                    self._output_frame_collapsed = collapsed

                output_frame.set_collapsed_changed_fn(on_collapsed_changed)
                self._build_output_ui()

            annotator_frame = ui.CollapsableFrame("Annotators", height=0, collapsed=self._annot_params_frame_collapsed)
            with annotator_frame:

                def on_collapsed_changed(collapsed):
                    self._annot_params_frame_collapsed = collapsed

                annotator_frame.set_collapsed_changed_fn(on_collapsed_changed)
                self._build_annotator_ui()

            rp_frame = ui.CollapsableFrame("Render Products", height=0, collapsed=self._rp_frame_collapsed)
            with rp_frame:

                def on_collapsed_changed(collapsed):
                    self._rp_frame_collapsed = collapsed

                rp_frame.set_collapsed_changed_fn(on_collapsed_changed)
                self._build_rp_ui()

    def _build_control_params_ui(self):
        with ui.VStack(spacing=5):
            with ui.HStack(spacing=5):
                ui.Spacer(width=10)
                ui.Label("Number of frames", tooltip="If set to 0, data acquisition will run indefinitely")
                num_frames_model = ui.IntField().model
                num_frames_model.set_value(self._num_frames)

                def num_frames_changed(m):
                    self._num_frames = m.as_int

                num_frames_model.add_value_changed_fn(num_frames_changed)

                ui.Label("RTSubframes", tooltip="Render extra frames between captures to avoid rendering artifacts")
                rt_subframes_model = ui.IntField().model
                rt_subframes_model.set_value(self._rt_subframes)

                def num_rt_subframes_changed(m):
                    self._rt_subframes = m.as_int

                rt_subframes_model.add_value_changed_fn(num_rt_subframes_changed)

            with ui.HStack(spacing=5):
                ui.Spacer(width=10)
                ui.Label("Reset Timeline", alignment=ui.Alignment.LEFT, tooltip="Reset the timeline on Stop/Clear")
                reset_timeline_model = ui.CheckBox().model
                reset_timeline_model.set_value(self._reset_timeline)

                def value_changed(m):
                    self._reset_timeline = m.as_bool

                reset_timeline_model.add_value_changed_fn(value_changed)

    def _build_manual_control_ui(self):
        with ui.HStack(spacing=5):
            ui.Spacer(width=5)
            self._manual_init_clear_button = ui.Button(
                "Init", clicked_fn=self._manual_init_clear, enabled=True, tooltip="Initialize or clear the writer"
            )
            self._manual_preview_button = ui.Button(
                "Preview",
                clicked_fn=self._manual_preview,
                enabled=False,
                tooltip="Run the graph once to load required assets/materials without writing data, enabled once 'Init' is pressed",
            )
            self._manual_step_button = ui.Button(
                "Step",
                clicked_fn=lambda: asyncio.ensure_future(self._manual_step_async()),
                enabled=False,
                tooltip="Capture one frame through one async step call, enabled once 'Init' is pressed",
            )
            self._manual_step_n_button = ui.Button(
                "Step N",
                clicked_fn=lambda: asyncio.ensure_future(self._manual_step_n_async()),
                enabled=False,
                tooltip="Capture N frames(set in 'Number of frames' field), through N async step calls, enabled once 'Init' is pressed",
            )

    def _build_control_ui(self):
        with ui.VStack(spacing=5):
            control_params_frame = ui.CollapsableFrame(
                "Parameters", height=0, collapsed=self._control_params_frame_collapsed
            )
            with control_params_frame:

                def on_collapsed_changed(collapsed):
                    self._control_params_frame_collapsed = collapsed

                control_params_frame.set_collapsed_changed_fn(on_collapsed_changed)
                self._build_control_params_ui()

            manual_control_frame = ui.CollapsableFrame(
                "Manual Control", height=0, collapsed=self._manual_control_frame_collapsed
            )
            with manual_control_frame:

                def on_collapsed_changed(collapsed):
                    self._manual_control_frame_collapsed = collapsed

                manual_control_frame.set_collapsed_changed_fn(on_collapsed_changed)
                self._build_manual_control_ui()

            with ui.HStack(spacing=5):
                ui.Spacer(width=5)
                self._start_stop_button = ui.Button(
                    "Start",
                    # clicked_fn=lambda: asyncio.ensure_future(self._start_stop_writer_async()),
                    clicked_fn=self._start_stop_writer,
                    enabled=True,
                    tooltip="Start/stop the writer",
                )
                self._pause_resume_button = ui.Button(
                    "Pause",
                    clicked_fn=self._pause_resume_writer,
                    enabled=False,
                    tooltip="Pause/resume a started writer",
                )

    def _build_window_ui(self):
        with self._window.frame:
            with ui.ScrollingFrame():
                with ui.VStack(spacing=5):
                    writer_frame = ui.CollapsableFrame("Writer", height=0, collapsed=self._writer_frame_collapsed)
                    with writer_frame:

                        def on_collapsed_changed(collapsed):
                            self._writer_frame_collapsed = collapsed

                        writer_frame.set_collapsed_changed_fn(on_collapsed_changed)
                        self._build_writer_ui()

                    control_frame = ui.CollapsableFrame("Control", height=0, collapsed=self._control_frame_collapsed)
                    with control_frame:

                        def on_collapsed_changed(collapsed):
                            self._control_frame_collapsed = collapsed

                        control_frame.set_collapsed_changed_fn(on_collapsed_changed)
                        self._build_control_ui()
