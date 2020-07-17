import omni.ext
import omni.ui as ui
import omni.kit.ui
from .. import _occupancy_map
import omni
import carb
from pxr import UsdGeom, Gf
from PIL import Image, ImageDraw


def create_xyz(init=0):
    all_axis = ["X", "Y", "Z"]
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
    return float_drags


class Extension(omni.ext.IExt):
    def on_startup(self):
        print("Starting Occupancy Map Extension")
        EXTENSION_NAME = "Occupancy Map"
        self._window = omni.ui.Window(EXTENSION_NAME, width=600, height=400)
        # self._menu_entry = omni.kit.ui.get_editor_menu().add_item(f"Window/Isaac/{EXTENSION_NAME}", self._menu_callback)
        self._om = _occupancy_map.acquire_occupancy_map_interface()
        with self._window.frame:
            with ui.HStack():
                with ui.VStack():
                    with ui.HStack(height=0):
                        ui.Label("Start Location", width=0, alignment=ui.Alignment.CENTER)
                        ui.Spacer(width=10)
                        self.start_location = create_xyz()
                    ui.Spacer(height=5)
                    with ui.HStack(height=0):
                        ui.Label("Lower Bound", width=0)
                        ui.Spacer(width=10)
                        self.lower_bound = create_xyz(-100000)
                    ui.Spacer(height=5)
                    with ui.HStack(height=0, padding=5):
                        ui.Label("Upper Bound", width=0)
                        ui.Spacer(width=10)
                        self.upper_bound = create_xyz(100000)
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
                    with ui.VStack():
                        ui.Button("Generate Occupancy Map", clicked_fn=self._manual_comp)
                        # ui.Spacer(width=10)
                        # ui.IntSlider(name="value_less", min=0, max=100, usingGauge=True).model.set_value(30)
                        # style = {"background_color": 0xFF000000, "secondary_color": 0xFFAAAAAA, "color": 0xFF444444}
                        # slider = ui.FloatSlider(enabled = False, style = style)
                        # slider.model.set_value(.5)
                        with ui.CollapsableFrame(title="Stats", collapsed=True):
                            with ui.VStack():
                                ui.Label("Rays", width=0, height=0)
                                ui.Label("Voxels", width=0, height=0)

                ui.Spacer(width=10)
                with ui.VStack():
                    with ui.HStack(height=0):
                        # ui.Label("Pixels Per Voxel", width=0, height=0)
                        # ui.Spacer(width=10)
                        # ui.MultiFloatField(1.0, height=0, h_spacing=5)
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

                    ui.Button("Generate Image", clicked_fn=self._generate_image)

        # self.btn_manual_comp = omni.kit.ui.Button("castRay")
        # self.btn_manual_comp.set_clicked_fn(self._manual_comp)
        # self._window.layout.add_child(self.btn_manual_comp)
        # print((self.start_location.model.get_item_value_model_count()))

    def _draw_instances(self, instancePath, cubePath, pos_list, scale, color):
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
        print("total points: ", len(pos_list))
        positions_attr.Set(pos_list)
        proto_indices_attr.Set([0] * len(pos_list))

    def _manual_comp(self):

        self._om.generateMap(
            (
                self.start_location["X"].model.get_value_as_float(),
                self.start_location["Y"].model.get_value_as_float(),
                self.start_location["Z"].model.get_value_as_float(),
            ),
            (
                self.lower_bound["X"].model.get_value_as_float(),
                self.lower_bound["Y"].model.get_value_as_float(),
                self.lower_bound["Z"].model.get_value_as_float(),
            ),
            (
                self.upper_bound["X"].model.get_value_as_float(),
                self.upper_bound["Y"].model.get_value_as_float(),
                self.upper_bound["Z"].model.get_value_as_float(),
            ),
            self.cell_size.model.get_value_as_float(),
            self.deg_per_ray.model.get_value_as_float(),
            self.min_search_dist.model.get_value_as_float(),
            self.occupancy_threshold.model.get_value_as_float(),
        )

        self._draw_instances(
            "/occupancyMap/occupiedInstances",
            "/occupancyMap/occupiedCube",
            self._om.getOccupiedPositions(),
            self.cell_size.model.get_value_as_float() * 0.5,
            (0.0, 1.0, 1.0),
        )

        # self._draw_instances(
        #     "/occupancyMap/freeInstances",
        #     "/occupancyMap/freeCube",
        #     self._om.getFreePositions(),
        #     self.cell_size.model.get_value_as_float() * 0.5,
        #     (1.0, 1.0, 0.0),
        # )

    def _generate_image(self):
        print(self._om.getMinBound())
        print(self._om.getMaxBound())

        min_b = self._om.getMinBound()
        max_b = self._om.getMaxBound()
        size = [0, 0, 0]

        size[0] = max_b[0] - min_b[0]
        size[1] = max_b[1] - min_b[1]
        size[2] = max_b[2] - min_b[2]

        points = self._om.getOccupiedPositions()
        scale = self.cell_size.model.get_value_as_float()
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
            # print(p, int(p[0]) * int(size[1]) + int(p[1]))
            # image[int(p[0]) * int(size[1]) + int(p[1]) + 0] = [255, 0, 0, 255]
            index = int(p[1] / scale - min_b[1] / scale) * int(size[0] / scale) + int(p[0] / scale - min_b[0] / scale)
            image[index * 4 + 0] = occupied_col[0]
            image[index * 4 + 1] = occupied_col[1]
            image[index * 4 + 2] = occupied_col[2]
            image[index * 4 + 3] = occupied_col[3]
        # print(image)

        print(size)
        # put a colored pixel at the start location
        # index = int(self.start_location["Y"].model.get_value_as_float() / scale - min_b[1] / scale) * int(
        #     size[0] / scale
        # ) + int(self.start_location["X"].model.get_value_as_float() / scale - min_b[0] / scale)
        # image[index * 4 + 0] = 255
        # image[index * 4 + 1] = 0
        # image[index * 4 + 2] = 0
        # image[index * 4 + 3] = 255
        start_pix = (
            int(self.start_location["X"].model.get_value_as_float() / scale - min_b[0] / scale),
            int(self.start_location["Y"].model.get_value_as_float() / scale - min_b[1] / scale),
        )
        print(
            "center",
            self.start_location["X"].model.get_value_as_float(),
            self.start_location["Y"].model.get_value_as_float(),
            min_b[0],
            min_b[1],
            start_pix[0],
            start_pix[1],
        )
        im = Image.frombytes("RGBA", (int(size[0] / scale), int(size[1] / scale)), bytes(image))
        ImageDraw.floodfill(
            im,
            start_pix,
            (freespace_col[0], freespace_col[1], freespace_col[2], freespace_col[3]),
            border=None,
            thresh=0,
        )
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
        image = list(im.tobytes())
        self._visualize_window = omni.ui.Window("Visualization", width=300, height=300)
        with self._visualize_window.frame:
            self._rgb_byte_provider = omni.ui.ByteImageProvider()
            self._rgb_byte_provider.set_data(image, [int(size[0] / scale), int(size[1] / scale)])
            omni.ui.ImageWithProvider(self._rgb_byte_provider)
        im.save("myfile.png")

    def on_shutdown(self):
        print("Shutting down Occupancy Map")
        _occupancy_map.release_occupancy_map_interface(self._om)
