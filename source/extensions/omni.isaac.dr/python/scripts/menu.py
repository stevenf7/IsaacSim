from pxr import Gf, Usd, UsdGeom, Sdf
import omni.isaac.DrSchema as DrSchema
import omni.kit
import omni.ui as ui
import omni.usd
import weakref
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription


class DRMenu:
    def __init__(self, domain_randomizer_interface):
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._window = ui.Window("Domain Randomizer", dockPreference=omni.ui.DockPreference.LEFT_BOTTOM)
        self._window.deferred_dock_in("Console", omni.ui.DockPolicy.DO_NOTHING)
        self._window.dock_order = 4
        self._dr = domain_randomizer_interface
        self.num_components = 10

        menu_items = [
            MenuItemDescription(name="Color Component", onclick_fn=lambda a=weakref.proxy(self): a.add_color_menu()),
            MenuItemDescription(
                name="Movement Component", onclick_fn=lambda a=weakref.proxy(self): a.add_movement_menu()
            ),
            MenuItemDescription(
                name="Rotation Component", onclick_fn=lambda a=weakref.proxy(self): a.add_rotation_menu()
            ),
            MenuItemDescription(name="Scale Component", onclick_fn=lambda a=weakref.proxy(self): a.add_scale_menu()),
            MenuItemDescription(
                name="Transform Component", onclick_fn=lambda a=weakref.proxy(self): a.add_transform_menu()
            ),
            MenuItemDescription(name="Light Component", onclick_fn=lambda a=weakref.proxy(self): a.add_light_menu()),
            MenuItemDescription(
                name="Texture Component", onclick_fn=lambda a=weakref.proxy(self): a.add_texture_menu()
            ),
            MenuItemDescription(
                name="Material Component", onclick_fn=lambda a=weakref.proxy(self): a.add_material_menu()
            ),
            MenuItemDescription(name="Mesh Component", onclick_fn=lambda a=weakref.proxy(self): a.add_mesh_menu()),
            MenuItemDescription(
                name="Visibility Component", onclick_fn=lambda a=weakref.proxy(self): a.add_visibility_menu()
            ),
        ]
        self._menu_items = [
            MenuItemDescription(name="Isaac", sub_menu=[MenuItemDescription(name="DR", sub_menu=menu_items)])
        ]
        add_menu_items(self._menu_items, "Create")

    def add_color_menu(self):
        parent = self._get_current_state(0, "ColorComponent")
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/color_component_" + str(self.component_count[0]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/color_component_" + str(self.component_count[0]), True
            )

        result, prim = omni.kit.commands.execute(
            "CreateColorComponentCommand",
            path=path,
            first_color_range=(0.0, 0.0, 0.0),
            second_color_range=(1.0, 1.0, 1.0),
            roughness_range=(0.0, 1.0),
            metallic_range=(0.0, 1.0),
            duration=1.0,
            include_children=False,
            seed=12345,
        )

        pass

    def add_movement_menu(self):
        parent = self._get_current_state(1, "MovementComponent")
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/movement_component_" + str(self.component_count[1]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/movement_component_" + str(self.component_count[1]), True
            )

        result, prim = omni.kit.commands.execute(
            "CreateMovementComponentCommand",
            path=path,
            min_range=(0.0, 0.0, 0.0),
            max_range=(0.0, 0.0, 0.0),
            target_position=None,
            target_paths=None,
            duration=1.0,
            include_children=False,
            seed=12345,
        )
        pass

    def add_rotation_menu(self):
        parent = self._get_current_state(5, "RotationComponent")
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/rotation_component_" + str(self.component_count[5]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/rotation_component_" + str(self.component_count[5]), True
            )

        result, prim = omni.kit.commands.execute(
            "CreateRotationComponentCommand",
            path=path,
            min_range=(0.0, 0.0, 0.0),
            max_range=(360.0, 360.0, 360.0),
            duration=1.0,
            include_children=False,
            seed=12345,
        )
        pass

    def add_scale_menu(self):
        parent = self._get_current_state(2, "ScaleComponent")
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/scale_component_" + str(self.component_count[2]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/scale_component_" + str(self.component_count[2]), True
            )
        result, prim = omni.kit.commands.execute(
            "CreateScaleComponentCommand",
            path=path,
            min_range=(0.5, 0.5, 0.5),
            max_range=(1.0, 1.0, 1.0),
            uniform_scaling=False,
            duration=1.0,
            include_children=False,
            seed=12345,
        )
        pass

    def add_transform_menu(self):
        parent = self._get_current_state(9, "TransformComponent")
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/transform_component_" + str(self.component_count[1]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/transform_component_" + str(self.component_count[1]), True
            )

        result, prim = omni.kit.commands.execute(
            "CreateTransformComponentCommand",
            path=path,
            translate_min_range=(0.0, 0.0, 0.0),
            translate_max_range=(100.0, 100.0, 100.0),
            rotate_min_range=(0.0, 0.0, 0.0),
            rotate_max_range=(0.0, 0.0, 0.0),
            scale_min_range=(0.0, 0.0, 0.0),
            scale_max_range=(0.0, 0.0, 0.0),
            target_position=None,
            target_paths=None,
            duration=1.0,
            include_children=False,
            seed=12345,
        )
        pass

    def add_light_menu(self):
        parent = self._get_current_state(3, "LightComponent")
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/light_component_" + str(self.component_count[3]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/light_component_" + str(self.component_count[3]), True
            )

        result, prim = omni.kit.commands.execute(
            "CreateLightComponentCommand",
            path=path,
            light_paths=[],
            first_color_range=(0.0, 0.0, 0.0),
            second_color_range=(1.0, 1.0, 1.0),
            intensity_range=(40000.0, 70000.0),
            temperature_range=(6500.0, 6500.0),
            enable_temperature=False,
            duration=1.0,
            include_children=False,
            seed=12345,
        )
        pass

    def add_texture_menu(self):
        parent = self._get_current_state(4, "TextureComponent")
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/texture_component_" + str(self.component_count[4]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/texture_component_" + str(self.component_count[4]), True
            )

        result, prim = omni.kit.commands.execute(
            "CreateTextureComponentCommand",
            path=path,
            prim_paths=[],
            enable_project_uvw=False,
            texture_list=[],
            ignored_class_list=[],
            grouped_class_list=[],
            duration=1.0,
            include_children=False,
            seed=12345,
        )
        pass

    def add_material_menu(self):
        parent = self._get_current_state(6, "MaterialComponent")
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/material_component_" + str(self.component_count[6]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/material_component_" + str(self.component_count[6]), True
            )
        result, prim = omni.kit.commands.execute(
            "CreateMaterialComponentCommand",
            path=path,
            prim_paths=[],
            material_list=[],
            ignored_class_list=[],
            grouped_class_list=[],
            loaded_material_paths=[],
            duration=1.0,
            include_children=False,
            seed=12345,
        )
        pass

    def add_mesh_menu(self):
        parent = self._get_current_state(7, "MeshComponent")
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/mesh_component_" + str(self.component_count[7]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/mesh_component_" + str(self.component_count[7]), True
            )

        result, prim = omni.kit.commands.execute(
            "CreateMeshComponentCommand",
            path=path,
            prim_paths=[],
            mesh_list=[],
            mesh_range=(1, 1),
            duration=1.0,
            include_children=False,
            seed=12345,
        )

        pass

    def add_visibility_menu(self):
        parent = self._get_current_state(8, "VisibilityComponent")
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/visibility_component_" + str(self.component_count[8]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/visibility_component_" + str(self.component_count[8]), True
            )

        result, prim = omni.kit.commands.execute(
            "CreateVisibilityComponentCommand",
            path=path,
            prim_paths=[],
            num_visible_range=(1, 1),
            duration=1.0,
            include_children=False,
            seed=12345,
        )

        pass

    def _get_current_state(self, index, component_type):
        self._stage = self._usd_context.get_stage()
        self.component_count = [0] * self.num_components
        for child_prim in self._stage.Traverse():
            if child_prim.GetTypeName() == component_type:
                self.component_count[index] = self.component_count[index] + 1

        selectedPrims = self._usd_context.get_selection().get_selected_prim_paths()
        if len(selectedPrims) > 0:
            curr_prim = selectedPrims[-1]
        else:
            curr_prim = None
        return curr_prim

    def _build_dr_ui(self):
        with self._window.frame:
            with ui.VStack(spacing=5):
                with ui.CollapsableFrame("Manual Mode"):
                    with ui.VStack(spacing=5):
                        with ui.HStack():
                            ui.Spacer(width=5)
                            self.btn_manual_comp = ui.Button("Enable Manual Mode", width=100, height=30)
                            self.btn_manual_comp.set_clicked_fn(self._toggle_manual_mode)
                            self.btn_randomize_once = ui.Button("Randomize Once", width=100, height=30)
                            self.btn_randomize_once.set_clicked_fn(self._randomize_once)

    def _toggle_manual_mode(self):
        if str(self.btn_manual_comp.text) == "Enable Manual Mode":
            self.btn_manual_comp.text = "Disable Manual Mode"
        else:
            self.btn_manual_comp.text = "Enable Manual Mode"
        self._dr.toggle_manual_mode()

    def _randomize_once(self):
        self._dr.randomize_once()

    def shutdown(self):
        remove_menu_items(self._menu_items, "Create")
        self._window = None
