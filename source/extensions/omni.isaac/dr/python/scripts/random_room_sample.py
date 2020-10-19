import carb
import omni.ui as ui
import omni.usd
from .nucleus_utils import find_nucleus_server

ADD_SIMPLE_ROOM_PYTHON_SAMPLE_MENU = "Isaac Robotics/Domain Randomizer/Simple Room Python Sample"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._asset_path = nucleus_server + "/Isaac"
        self._window = ui.Window("Simple Room Python Sample", width=600, height=400)
        self._menu_entry = omni.kit.ui.get_editor_menu().add_item(
            ADD_SIMPLE_ROOM_PYTHON_SAMPLE_MENU, self._menu_callback
        )
        self._window.visible = False
        self._window.deferred_dock_in("Content")

        with self._window.frame:
            with ui.VStack(height=0):
                ui.Spacer(width=5)
                load_stage_btn = ui.Button("Load Stage", width=100)
                load_stage_btn.set_clicked_fn(self._on_load_stage)
                load_comp_btn = ui.Button("Load DR Component", width=100)
                load_comp_btn.set_clicked_fn(self._on_load_component)

    def _menu_callback(self, a, b):
        self._window.visible = not self._window.visible

    def on_shutdown(self):
        self._window = None
        self._usd_context = None
        self._stage = None

    def _on_load_stage(self):
        omni.usd.get_context().open_stage(self._asset_path + "/Environments/Simple_Room/simple_room.usd", None)

    def _on_load_component(self):
        """Creates DR components with various attributes
        """

        # List of textures to randomize from
        texture_list = [
            self._asset_path + "/Samples/DR/Materials/Textures/checkered.png",
            self._asset_path + "/Samples/DR/Materials/Textures/marble_tile.png",
            self._asset_path + "/Samples/DR/Materials/Textures/picture_a.png",
            self._asset_path + "/Samples/DR/Materials/Textures/picture_b.png",
            self._asset_path + "/Samples/DR/Materials/Textures/textured_wall.png",
            self._asset_path + "/Samples/DR/Materials/Textures/checkered_color.png",
        ]

        # Some prim paths to used for randomization
        simple_room_prim_path = "/Root"
        light_prim_path = "/Root/RectLight"
        table_prim_path = "/Root/table_low_327"
        floor_prim_path = "/Root/Towel_Room01_floor_bottom_218"

        # Create DR texture component
        result, prim = omni.kit.commands.execute(
            "CreateTextureComponentCommand",
            prim_paths=[simple_room_prim_path],
            enable_project_uvw=False,
            texture_list=texture_list,
            ignored_class_list=["floor_bottom"],
            grouped_class_list=[],
            duration=1.0,
            include_children=True,
        )
        # Create DR color component
        result, prim = omni.kit.commands.execute(
            "CreateColorComponentCommand",
            prim_paths=[floor_prim_path],
            first_color_range=(0.0, 0.0, 0.0),
            second_color_range=(1.0, 1.0, 1.0),
            roughness_range=(0.0, 1.0),
            metallic_range=(0.0, 1.0),
            duration=1.0,
            include_children=False,
        )
        # Create DR movement component
        result, prim = omni.kit.commands.execute(
            "CreateMovementComponentCommand",
            prim_paths=[table_prim_path],
            min_range=(-50.0, -50.0, 18.04),
            max_range=(50.0, 50.0, 18.04),
            target_position=None,
            target_paths=None,
            duration=1.0,
            include_children=False,
        )
        # Create DR rotation component
        result, prim = omni.kit.commands.execute(
            "CreateRotationComponentCommand",
            prim_paths=[table_prim_path],
            min_range=(0.0, 0.0, 0.0),
            max_range=(0.0, 0.0, 360.0),
            duration=1.0,
            include_children=False,
        )
        # Create DR scale component
        result, prim = omni.kit.commands.execute(
            "CreateScaleComponentCommand",
            prim_paths=[table_prim_path],
            min_range=(0.4, 0.4, 0.4),
            max_range=(1.3, 1.3, 1.3),
            uniform_scaling=True,
            duration=1.0,
            include_children=False,
        )
        # Create DR light component
        result, prim = omni.kit.commands.execute(
            "CreateLightComponentCommand",
            light_paths=[light_prim_path],
            first_color_range=(0.9, 0.9, 0.9),
            second_color_range=(1.0, 1.0, 1.0),
            intensity_range=(40000.0, 70000.0),
            temperature_range=(1500.0, 6500.0),
            enable_temperature=True,
            duration=1.0,
            include_children=False,
        )
