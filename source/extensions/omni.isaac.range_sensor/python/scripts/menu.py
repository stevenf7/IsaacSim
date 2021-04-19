import carb
import omni.kit.commands
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from pxr import Sdf, UsdGeom, Gf
import weakref


class RangeSensorMenu:
    def __init__(self):
        menu_items = [
            MenuItemDescription(
                name="Lidar",
                sub_menu=[
                    MenuItemDescription(name="Rotating", onclick_fn=lambda a=weakref.proxy(self): a._add_lidar()),
                    MenuItemDescription(name="Generic", onclick_fn=lambda a=weakref.proxy(self): a._add_generic()),
                ],
            ),
            MenuItemDescription(
                name="Ultrasonic",
                sub_menu=[
                    MenuItemDescription(
                        name="Array", onclick_fn=lambda a=weakref.proxy(self): a._add_ultrasonic_array()
                    ),
                    MenuItemDescription(
                        name="Emitter", onclick_fn=lambda a=weakref.proxy(self): a._add_ultrasonic_emitter()
                    ),
                    MenuItemDescription(
                        name="FiringGroup", onclick_fn=lambda a=weakref.proxy(self): a._add_ultrasonic_firing_group()
                    ),
                ],
            ),
        ]

        self._menu_items = [
            MenuItemDescription(
                name="Isaac", glyph="plug.svg", sub_menu=[MenuItemDescription(name="Sensors", sub_menu=menu_items)]
            )
        ]
        add_menu_items(self._menu_items, "Create")

    def _get_stage_and_path(self):
        self._stage = omni.usd.get_context().get_stage()
        selectedPrims = omni.usd.get_context().get_selection().get_selected_prim_paths()

        if len(selectedPrims) > 0:
            curr_prim = selectedPrims[-1]
        else:
            curr_prim = None
        return curr_prim

    def _add_lidar(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "CreateRangeSensorLidarCommand",
            path="/Lidar",
            parent=self._get_stage_and_path(),
            min_range=0.4,
            max_range=100.0,
            draw_points=False,
            draw_lines=False,
            horizontal_fov=360.0,
            vertical_fov=30.0,
            horizontal_resolution=0.4,
            vertical_resolution=4.0,
            rotation_rate=20.0,
            high_lod=False,
            yaw_offset=0.0,
        )

    def _add_ultrasonic_array(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "CreateRangeSensorUltrasonicArrayCommand",
            path="/UltrasonicArray",
            parent=self._get_stage_and_path(),
            min_range=0.4,
            max_range=3.0,
            draw_points=False,
            draw_lines=False,
            horizontal_fov=15.0,
            vertical_fov=10.0,
            horizontal_resolution=0.5,
            vertical_resolution=0.5,
            num_bins=224,
            emitter_prims=[],
            firing_group_prims=[],
        )

    def _add_ultrasonic_emitter(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "CreateRangeSensorUltrasonicEmitterCommand",
            path="/UltrasonicEmitter",
            parent=self._get_stage_and_path(),
            per_ray_intensity=1.0,
            yaw_offset=0.0,
            adjacency_list=[],
        )

    def _add_ultrasonic_firing_group(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "CreateRangeSensorUltrasonicFiringGroupCommand",
            path="/UltrasonicFiringGroup",
            parent=self._get_stage_and_path(),
            emitter_modes=[],
            receiver_modes=[],
        )

    def _add_generic(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "CreateRangeSensorGenericCommand",
            path="/GenericSensor",
            parent=self._get_stage_and_path(),
            min_range=0.4,
            max_range=100.0,
            draw_points=False,
            draw_lines=False,
            sampling_rate=60,
        )

    def shutdown(self):
        remove_menu_items(self._menu_items, "Create")
        self.menus = None
