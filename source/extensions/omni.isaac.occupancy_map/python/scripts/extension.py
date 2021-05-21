import omni.ext
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from .. import _occupancy_map
import omni
from pxr import UsdGeom, Gf
import gc
import os
from .utils import update_location, compute_coordinates, generate_image
import weakref
import asyncio


def create_xyz(init=0, all_axis=["X", "Y", "Z"], callback=None):

    colors = {"X": 0xFF5555AA, "Y": 0xFF76A371, "Z": 0xFFA07D4F}
    float_drags = {}
    for axis in all_axis:
        with ui.HStack():
            with ui.ZStack(width=15):
                ui.Rectangle(
                    width=15,
                    height=20,
                    style={"background_color": colors[axis], "border_radius": 3, "corner_flag": ui.CornerFlag.LEFT},
                )
                ui.Label(axis, name="transform_label", alignment=ui.Alignment.CENTER)
            float_drags[axis] = ui.FloatDrag(name="transform", min=-1000000, max=1000000, step=0.01)
            float_drags[axis].model.set_value(init)
            if callback:
                float_drags[axis].model.add_value_changed_fn(lambda m: callback())
    return float_drags


class Extension(omni.ext.IExt):
    def on_startup(self):
        EXTENSION_NAME = "Occupancy Map"
        self._timeline = omni.timeline.get_timeline_interface()
        self._window = omni.ui.Window(EXTENSION_NAME, width=600, height=400, visible=False)
        self._window.deferred_dock_in("Console", omni.ui.DockPolicy.DO_NOTHING)
        self._menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        add_menu_items(self._menu_items, "Isaac Utils")
        self._om = _occupancy_map.acquire_occupancy_map_interface()
        self._layers = omni.usd.get_context().get_layers()
        self._filepicker = None
        with self._window.frame:
            with ui.HStack():
                with ui.VStack():
                    with ui.HStack(height=0):
                        ui.Label("Start Location", width=0, alignment=ui.Alignment.CENTER)
                        ui.Spacer(width=10)
                        self.start_location = create_xyz(callback=self.on_update_location)
                    ui.Spacer(height=5)
                    with ui.HStack(height=0):
                        ui.Label("Lower Bound", width=0)
                        ui.Spacer(width=10)
                        self.lower_bound = create_xyz(-100, all_axis=["X", "Y"], callback=self.on_update_location)
                    ui.Spacer(height=5)
                    with ui.HStack(height=0, padding=5):
                        ui.Label("Upper Bound", width=0)
                        ui.Spacer(width=10)
                        self.upper_bound = create_xyz(100, all_axis=["X", "Y"], callback=self.on_update_location)
                    ui.Spacer(height=5)

                    with ui.VStack(height=0):
                        with ui.HStack(height=0):
                            ui.Label("Degrees Per Ray", width=0, height=0)
                            ui.Spacer(width=10)
                            self.deg_per_ray = ui.FloatDrag(
                                name="degrees", min=0.01, max=359, step=0.01, height=0, h_spacing=5
                            )
                            self.deg_per_ray.model.set_value(5)
                        ui.Spacer(height=5)
                        with ui.HStack(height=0):
                            ui.Label("Cell Size [cm]", width=0, height=0)
                            ui.Spacer(width=10)
                            self.cell_size = ui.FloatDrag(
                                name="cell size", min=0.01, max=100, step=0.01, height=0, h_spacing=5
                            )
                            self.cell_size.model.set_value(5)
                        ui.Spacer(height=5)
                        with ui.HStack(height=0):
                            ui.Label("Surface Offset Distance [cm]", width=0, height=0)
                            ui.Spacer(width=10)
                            self.min_search_dist = ui.FloatDrag(
                                name="surface offset distance", min=0.01, max=1000, step=0.01, height=0, h_spacing=5
                            )
                            self.min_search_dist.model.set_value(2)
                        ui.Spacer(height=5)
                        with ui.HStack(height=0):
                            ui.Label("Occupancy Threshold", width=0, height=0)
                            ui.Spacer(width=10)
                            self.occupancy_threshold = ui.FloatDrag(
                                name="min search dist", min=0.01, max=2, step=0.01, height=0, h_spacing=5
                            )
                            self.occupancy_threshold.model.set_value(1)
                        ui.Spacer(height=5)
                        with ui.HStack(height=0):
                            ui.Label("Max Rays", width=0, height=0)
                            ui.Spacer(width=10)
                            self.max_rays = ui.IntField(
                                name="min search dist", min=0, max=100000000, height=0, h_spacing=5
                            )
                            self.max_rays.model.set_value(1000000)
                    with ui.VStack():
                        ui.Button("Generate Occupancy Map", clicked_fn=self._generate_map)

                ui.Spacer(width=10)
                with ui.VStack():
                    with ui.HStack(height=0):
                        ui.Label("Occupied Color", width=0, height=0)
                        ui.Spacer(width=10)
                        self.occupied_color_model = ui.ColorWidget(0, 0, 0, 1, width=0).model
                        ui.Spacer(width=10)
                        ui.Label("Freespace Color", width=0, height=0)
                        ui.Spacer(width=10)
                        self.freespace_color_model = ui.ColorWidget(1, 1, 1, 1, width=0).model
                        ui.Spacer(width=10)
                        ui.Label("Unknown Color", width=0, height=0)
                        ui.Spacer(width=10)
                        self.unknown_color_model = ui.ColorWidget(0.5, 0.5, 0.5, 1, width=0).model
                    ui.Spacer(height=10)
                    with ui.HStack(height=0):
                        ui.Label("Rotation", width=0, height=0, tooltip="Clockwise rotation")
                        ui.Spacer(width=10)

                        self._selected_image_rotation = ui.ComboBox(0, "0", "-90", "90", "180", height=0, width=200)
                    self.generate_image_btn = ui.Button("Generate Image", clicked_fn=self._generate_image)
                    self.generate_image_btn.visible = False
                    # self.draw_voxel_btn = ui.Button("Draw Voxels", clicked_fn=self._draw_instances)
                    # self.draw_voxel_btn.visible = False

    def _menu_callback(self):
        self._window.visible = not self._window.visible
        if not self._window.visible:
            self._stage_event_sub = None
        else:
            self._usd_context = omni.usd.get_context()
            if self._usd_context is not None:
                self._selection = self._usd_context.get_selection()

    def on_update_location(self):
        update_location(
            self._om,
            [
                self.start_location["X"].model.get_value_as_float(),
                self.start_location["Y"].model.get_value_as_float(),
                self.start_location["Z"].model.get_value_as_float(),
            ],
            [self.lower_bound["X"].model.get_value_as_float(), self.lower_bound["Y"].model.get_value_as_float()],
            [self.upper_bound["X"].model.get_value_as_float(), self.upper_bound["Y"].model.get_value_as_float()],
        )

    def _draw_instances(self):

        instancePath = "/occupancyMap/occupiedInstances"
        cubePath = "/occupancyMap/occupiedCube"
        pos_list = self._om.get_occupied_positions()
        scale = self.cell_size.model.get_value_as_float() * 0.5
        color = (0.0, 1.0, 1.0)
        stage = omni.usd.get_context().get_stage()
        if stage.GetPrimAtPath(instancePath):
            stage.RemovePrim(instancePath)
        point_instancer = UsdGeom.PointInstancer(stage.DefinePrim(instancePath, "PointInstancer"))
        positions_attr = point_instancer.CreatePositionsAttr()
        if stage.GetPrimAtPath(cubePath):
            stage.RemovePrim(cubePath)
        occupiedCube = UsdGeom.Cube(stage.DefinePrim(cubePath, "Cube"))
        occupiedCube.AddScaleOp().Set(Gf.Vec3d(1, 1, 1) * scale)
        occupiedCube.CreateDisplayColorPrimvar().Set([color])

        point_instancer.CreatePrototypesRel().SetTargets([occupiedCube.GetPath()])
        proto_indices_attr = point_instancer.CreateProtoIndicesAttr()
        print("total points drawn: ", len(pos_list))
        positions_attr.Set(pos_list)
        proto_indices_attr.Set([0] * len(pos_list))

    def _generate_map(self):
        self.on_update_location()

        async def generate_task():
            do_stop = False
            if not self._timeline.is_playing():
                self._timeline.play()
                do_stop = True
            await omni.kit.app.get_app().next_update_async()
            self._om.generate(
                self.cell_size.model.get_value_as_float(),
                self.deg_per_ray.model.get_value_as_float(),
                self.min_search_dist.model.get_value_as_float(),
                self.occupancy_threshold.model.get_value_as_float(),
                self.max_rays.model.get_value_as_int(),
            )
            await omni.kit.app.get_app().next_update_async()
            if do_stop:
                self._timeline.stop()

        asyncio.ensure_future(generate_task())
        self.generate_image_btn.visible = True
        # self.draw_voxel_btn.visible = True

    def _generate_image(self):

        scale = self.cell_size.model.get_value_as_float()

        # Clockwise rotation
        rotate_image_angle = 0
        current_image_rotation_index = self._selected_image_rotation.model.get_item_value_model().as_int
        if current_image_rotation_index == 0:
            top_left, top_right, bottom_left, bottom_right, image_coords = compute_coordinates(self._om, scale)
        elif current_image_rotation_index == 1:  # -90 degrees
            top_right, bottom_right, top_left, bottom_left, image_coords = compute_coordinates(self._om, scale)
            rotate_image_angle = -90
        elif current_image_rotation_index == 2:  # 90 degrees
            bottom_left, top_left, bottom_right, top_right, image_coords = compute_coordinates(self._om, scale)
            rotate_image_angle = 90
        elif current_image_rotation_index == 3:  # 180 degrees
            bottom_right, bottom_left, top_right, top_left, image_coords = compute_coordinates(self._om, scale)
            rotate_image_angle = 180

        print("World coordinates for image in stage units:")
        print("Top left: ", top_left)
        print("Top right: ", top_right)

        print("Bottom left: ", bottom_left)
        print("Bottom right: ", bottom_right)

        print(
            f"Coordinates of top left of image (pixel 0,0) as origin, + X down, + Y right:\n{float(image_coords[0][0]), float(image_coords[1][0])}"
        )

        occupied_col = []
        for item in self.occupied_color_model.get_item_children():
            component = self.occupied_color_model.get_item_value_model(item)
            occupied_col.append(int(component.get_value_as_float() * 255))

        freespace_col = []
        for item in self.freespace_color_model.get_item_children():
            component = self.freespace_color_model.get_item_value_model(item)
            freespace_col.append(int(component.get_value_as_float() * 255))

        unknown_col = []
        for item in self.unknown_color_model.get_item_children():
            component = self.unknown_color_model.get_item_value_model(item)
            unknown_col.append(int(component.get_value_as_float() * 255))

        image = generate_image(
            self._om,
            scale,
            occupied_col,
            unknown_col,
            freespace_col,
            [self.start_location["X"].model.get_value_as_float(), self.start_location["Y"].model.get_value_as_float()],
        )

        from PIL import Image

        dims = self._om.get_dimensions()
        im = Image.frombytes("RGBA", (dims.x, dims.y), bytes(image))
        im = im.rotate(-rotate_image_angle, expand=True)
        image = list(im.tobytes())

        image_width = im.width
        image_height = im.height

        self._visualize_window = omni.ui.Window("Visualization", width=300, height=300)

        def save_image(file, folder):
            file = file if file[-4:].lower() == ".png" else "{}.png".format(file)
            im = Image.frombytes("RGBA", (image_width, image_height), bytes(image))
            print("Saving occupancy map image to", folder + "/" + file)
            im.save(folder + "/" + file)
            self._filepicker.hide()

        def save_file():
            from omni.kit.window.filepicker import FilePickerDialog
            from omni.kit.widget.filebrowser import FileBrowserItem

            def _on_filter_png_files(item: FileBrowserItem) -> bool:
                """Callback to filter the choices of file names in the open or save dialog"""
                if not item or item.is_folder:
                    return True
                # Show only files with listed extensions
                return os.path.splitext(item.path)[1] == ".png"

            self._filepicker = None
            self._filepicker = FilePickerDialog(
                "Save .png image",
                allow_multi_selection=False,
                apply_button_label="Save",
                click_apply_handler=save_image,
                item_filter_options=[".png Files (*.png, *.PNG)"],
                item_filter_fn=_on_filter_png_files,
            )

        size = [0, 0, 0]

        size[0] = image_width * self.cell_size.model.get_value_as_float()
        size[1] = image_height * self.cell_size.model.get_value_as_float()

        with self._visualize_window.frame:
            self._rgb_byte_provider = omni.ui.ByteImageProvider()
            self._rgb_byte_provider.set_bytes_data(image, [int(size[0] / scale), int(size[1] / scale)])
            with ui.VStack():
                with ui.VStack(height=0):
                    self._selected_data_output = ui.ComboBox(
                        0,
                        "Cooordinates in stage space",
                        "ROS Occupancy Map Parameters file (YAML)",
                        height=0,
                        width=300,
                    )

                    ui.Spacer(height=5)
                    data = ui.StringField(height=100, multiline=True).model

                    image_details_text = f"Top Left: {top_left}\t\t Top Right: {top_right}\n Bottom Left: {bottom_left}\t\t Bottom Right: {bottom_right}"
                    image_details_text += f"\nCoordinates of top left of image (pixel 0,0) as origin, + X down, + Y right:\n{float(image_coords[0][0]), float(image_coords[1][0])}"
                    image_details_text += f"\nImage size in pixels: {int(size[0] / scale)}, {int(size[1] / scale)}"

                    scale_to_meters = 100.0
                    ros_yaml_file_text = "image: carter_2dnav_map.png"
                    ros_yaml_file_text += (
                        f"\nresolution: {float(self.cell_size.model.get_value_as_float() / scale_to_meters)}"
                    )
                    ros_yaml_file_text += f"\norigin: [{float(bottom_left[0]/scale_to_meters)}, {float(bottom_left[1]/scale_to_meters)}, 0.0000]"
                    ros_yaml_file_text += "\nnegate: 0"
                    ros_yaml_file_text += f"\noccupied_thresh: {self.occupancy_threshold.model.get_value_as_float()}"
                    ros_yaml_file_text += "\nfree_thresh: 0.196"
                    data.set_value(image_details_text)

                    def update_data_output(combo_box_model, item):
                        current_data_output_index = self._selected_data_output.model.get_item_value_model().as_int
                        if current_data_output_index == 0:
                            data_text = image_details_text
                        elif current_data_output_index == 1:
                            data_text = ros_yaml_file_text
                        data.set_value(data_text)

                    self._selected_data_output.model.add_item_changed_fn(update_data_output)

                ui.Spacer(height=10)
                with ui.VStack():
                    omni.ui.ImageWithProvider(self._rgb_byte_provider)
                ui.Spacer(height=5)
                ui.Button("Save Image", clicked_fn=save_file, height=0)

    def on_shutdown(self):
        if self._filepicker:
            self._filepicker = None
        remove_menu_items(self._menu_items, "Isaac Utils")
        gc.collect()
