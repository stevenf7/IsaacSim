import omni.ext
import omni.ui as ui
import omni.kit.ui
from .. import _occupancy_map
import omni
import carb
from pxr import UsdGeom, Gf, Sdf, Usd
import os
import gc


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
        self._window = omni.ui.Window(EXTENSION_NAME, width=600, height=400, visible=False)
        self._menu_entry = omni.kit.ui.get_editor_menu().add_item(f"Window/Isaac/{EXTENSION_NAME}", self._menu_callback)
        self._om = _occupancy_map.acquire_occupancy_map_interface()
        self._editor = omni.kit.editor.get_editor_interface()
        self._layers = omni.usd.get_context().get_layers()
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

                    self.generate_image_btn = ui.Button("Generate Image", clicked_fn=self._generate_image)
                    self.generate_image_btn.visible = False
                    # self.draw_voxel_btn = ui.Button("Draw Voxels", clicked_fn=self._draw_instances)
                    # self.draw_voxel_btn.visible = False

    def _menu_callback(self, name, visible):
        self._window.visible = not self._window.visible
        if not self._window.visible:
            self._stage_event_sub = None
        else:
            self._usd_context = omni.usd.get_context()
            if self._usd_context is not None:
                self._selection = self._usd_context.get_selection()

    def on_update_location(self):
        self._om.set_transform(
            (
                self.start_location["X"].model.get_value_as_float(),
                self.start_location["Y"].model.get_value_as_float(),
                self.start_location["Z"].model.get_value_as_float(),
            ),
            (self.lower_bound["X"].model.get_value_as_float(), self.lower_bound["Y"].model.get_value_as_float()),
            (self.upper_bound["X"].model.get_value_as_float(), self.upper_bound["Y"].model.get_value_as_float()),
        )
        self._om.update()

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
        self._om.set_transform(
            (
                self.start_location["X"].model.get_value_as_float(),
                self.start_location["Y"].model.get_value_as_float(),
                self.start_location["Z"].model.get_value_as_float(),
            ),
            (self.lower_bound["X"].model.get_value_as_float(), self.lower_bound["Y"].model.get_value_as_float()),
            (self.upper_bound["X"].model.get_value_as_float(), self.upper_bound["Y"].model.get_value_as_float()),
        )
        self._om.update()
        self._om.generate(
            self.cell_size.model.get_value_as_float(),
            self.deg_per_ray.model.get_value_as_float(),
            self.min_search_dist.model.get_value_as_float(),
            self.occupancy_threshold.model.get_value_as_float(),
            self.max_rays.model.get_value_as_int(),
        )
        self.generate_image_btn.visible = True
        # self.draw_voxel_btn.visible = True

    def _generate_image(self):
        from PIL import Image, ImageDraw

        points = self._om.get_occupied_positions()
        if len(points) == 0:
            print("No occupied points, cannot generate image")
            return

        # print("min bound: ", self._om.get_min_bound())
        # print("max bound: ", self._om.get_max_bound())

        min_b = self._om.get_min_bound()
        max_b = self._om.get_max_bound()
        scale = self.cell_size.model.get_value_as_float()
        half_w = scale * 0.5
        print("World coordinates for image in stage units:")
        print("Top left: ", max_b[0] - half_w, min_b[1] + half_w)
        print("Top right: ", min_b[0] + half_w, min_b[1] + half_w)

        print("Bottom left: ", max_b[0] - half_w, max_b[1] - half_w)
        print("Bottom right: ", min_b[0] + half_w, max_b[1] - half_w)

        size = [0, 0, 0]

        size[0] = max_b[0] - min_b[0]
        size[1] = max_b[1] - min_b[1]
        size[2] = max_b[2] - min_b[2]

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

        image = unknown_col * (int(size[0] / scale) * int(size[1] / scale))

        for p in points:
            index = int(p[1] / scale - min_b[1] / scale) * int(size[0] / scale) + int(p[0] / scale - min_b[0] / scale)
            image[index * 4 + 0] = occupied_col[0]
            image[index * 4 + 1] = occupied_col[1]
            image[index * 4 + 2] = occupied_col[2]
            image[index * 4 + 3] = occupied_col[3]

        start_pix = (
            int(self.start_location["X"].model.get_value_as_float() / scale - min_b[0] / scale),
            int(self.start_location["Y"].model.get_value_as_float() / scale - min_b[1] / scale),
        )

        im = Image.frombytes("RGBA", (int(size[0] / scale), int(size[1] / scale)), bytes(image))
        ImageDraw.floodfill(
            im,
            start_pix,
            (freespace_col[0], freespace_col[1], freespace_col[2], freespace_col[3]),
            border=None,
            thresh=0,
        )
        # Flip image to match what SDK expects
        im = im.transpose(Image.FLIP_LEFT_RIGHT)

        image = list(im.tobytes())
        self._visualize_window = omni.ui.Window("Visualization", width=300, height=300)

        def save_image(path):
            print("Saving occupancy map image to", path)
            im.save(path)

        def save_file():
            self._filepicker = omni.kit.ui.FilePicker(
                "Save Generated Image",
                file_type=omni.kit.ui.FileDialogSelectType.FILE,
                mode=omni.kit.ui.FileDialogOpenMode.SAVE,
            )
            self._filepicker.set_file_selected_fn(save_image)
            self._filepicker.add_filter("PNG (*.png)", r".*.png$")
            self._filepicker.show()

        with self._visualize_window.frame:
            self._rgb_byte_provider = omni.ui.ByteImageProvider()
            self._rgb_byte_provider.set_data(image, [int(size[0] / scale), int(size[1] / scale)])
            with ui.VStack():
                with ui.VStack(height=0):
                    ui.Label(
                        f"Coordinates in stage units: \n Top Left: [{max_b[0]-half_w}, {min_b[1]+half_w}]\t\t Top Right: {min_b[0]+half_w}, {min_b[1]+half_w}\n Bottom Left: {max_b[0]-half_w}, {max_b[1]-half_w}\t\t Bottom Right: {min_b[0]+half_w}, {max_b[1]-half_w}",
                        alignment=ui.Alignment.LEFT,
                    )
                ui.Spacer(height=5)
                omni.ui.ImageWithProvider(self._rgb_byte_provider)
                with ui.VStack(height=0):
                    ui.Label(f"Image size in pixels: {int(size[0] / scale)}, {int(size[1] / scale)}")
                ui.Button("Save Image", clicked_fn=save_file, height=0)

    def on_shutdown(self):
        _occupancy_map.release_occupancy_map_interface(self._om)
        gc.collect()
