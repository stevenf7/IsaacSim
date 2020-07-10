import omni.ext
import omni.kit.commands
import omni.kit.editor
import omni.ui as ui
import os
import gc
import carb
from . import usd_exporter
from .assembly_widget import *

import asyncio
from functools import wraps, partial
from pathlib import Path

# from .. import _step_importer
from omni.isaac.step_importer import _step_importer

EXTENSION_NAME = "Step Importer"


def wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


def labeled_FloatDrag(props, parent, label, min, max, default=0, width=80, spacing=10, tooltipFn=None):
    with parent:
        with ui.HStack(spacing=spacing, width=width + 130, height=20, tooltip_fn=tooltipFn, tooltip_offset_y=25):
            ui.Label(label, width=120, name=label)
            props[label] = ui.FloatDrag(min=min, max=max, width=width)
            props[label].model.set_value(default)


def labeled_CheckBox(props, parent, label, checked=False, spacing=10, tooltipFn=None):
    with parent:
        with ui.HStack(spacing=spacing, height=20):
            ui.Label(label, width=120, name=label, tooltip_fn=tooltipFn)
            props[label] = ui.CheckBox()
            props[label].model.set_value(checked)


def image_tooltip(text, image_src, width, height):
    """ Base Image tooltip function used on the UI"""
    with ui.VStack(width=width, height=height):
        ui.Label(text, width=width, height=20)
        ui.Image(image_src, height=height - 20)


def lin_deflection_tooltip():
    image_tooltip(
        " limits the distance between a curve and its tessellation",
        str(Path(__file__).parent.joinpath("data/linear_displacement.png")),
        400,
        220,
    )


def ang_deflection_tooltip():
    image_tooltip(
        "  limits the angle between subsequent segments in a polyline",
        str(Path(__file__).parent.joinpath("data/angular_displacement.png")),
        400,
        220,
    )


def surface_area_tooltip():
    ui.Label("Minimum area for each triangle in the Mesh. Negative values means no limit.")


def rel_offset_tooltip():
    ui.Label("Scales the linear deflection offset by the segment length.")


def int_verts_tooltip():
    ui.Label("Takes internal vertices in consideration when building the mesh.")


def com_tooltip():
    ui.Label("Exports meshes with origin at volumetric center of mass")


class Callback_Exporter:
    def __init__(self, exporter):
        self.exporter = exporter

    def __call__(self, a, b):
        print(a, b)
        result = omni.usd.get_context().close_stage(self.exporter)
        print(result)


class StepImporter(omni.ext.IExt):
    def on_startup(self):
        print("Loading Step Importer Extension")
        self._si = _step_importer.acquire_interface()
        self.async_import = wrap(self._si.import_step_file)
        self._editor = omni.kit.editor.get_editor_interface()
        self.part = _step_importer.Part()
        self._filepicker = None
        self.path = ""

        try:
            self._style = self._editor.get_ui_style()
        except:
            self._style = None
        finally:
            if not self._style:
                self._style = "NvidiaDark"

        self._menu = omni.kit.ui.get_editor_menu().add_item(
            "Window/Isaac/" + EXTENSION_NAME, self.show_window, toggle=True, value=True
        )

        if self._style == "NvidiaLight":
            self.tree_style = {
                "Field": {"background_color": 0xFF535354, "color": 0xFFCCCCCC},
                "ScrollingFrame": {"background_color": 0xFFE0E0E0, "secondary_color": 0xFF444444},
                "TreeView": {
                    "background_color": 0xFFE0E0E0,
                    "background_selected_color": 0x109D905C,
                    "secondary_color": 0xFFACACAC,
                },
                "TreeView.ScrollingFrame": {"background_color": 0xFFE0E0E0},
                "TreeView.Header": {"color": 0xFFCCCCCC},
                "TreeView.Header::background": {
                    "background_color": 0xFF535354,
                    "border_color": 0xFF707070,
                    "border_width": 0.5,
                },
                "TreeView.Header::columnname": {"margin": 3},
                "TreeView.Image::object_icon_grey": {"color": 0x80FFFFFF},
                "TreeView.Item": {"color": 0xFF535354, "font_size": 16},
                "TreeView.Item::object_name": {"margin": 3},
                "TreeView.Item::object_name_grey": {"color": 0xFFACACAC},
                "TreeView.Item:selected": {"color": 0xFF2A2825},
                "TreeView:selected": {"background_color": 0x409D905C},
            }
        else:
            self.tree_style = {
                "TreeView": {
                    "background_color": 0xFF23211F,
                    "background_selected_color": 0x664F4D43,
                    "secondary_color": 0xFF403B3B,
                },
                "TreeView.ScrollingFrame": {"background_color": 0xFF23211F},
                "TreeView.Header": {"background_color": 0xFF343432, "color": 0xFFCCCCCC, "font_size": 13.0},
                "TreeView.Image::object_icon_grey": {"color": 0x80FFFFFF},
                "TreeView.Item": {"color": 0xFF8A8777},
                "TreeView.Item::object_name_grey": {"color": 0xFF4D4B42},
                "TreeView.Item:selected": {"color": 0xFF23211F},
                "TreeView:selected": {"background_color": 0xFF8A8777},
            }

        self._delegate = AssemblyDelegate()

        self.show_window(None, True)

    def show_window(self, menu, value):
        if value:
            self._window = ui.Window(
                EXTENSION_NAME,
                width=300,
                height=200,
                menu_path="Isaac Robotics/Importers/" + EXTENSION_NAME,
                open=value,
                dock=ui.DockPreference.LEFT_BOTTOM,
            )
            self.props = {}
            with self._window.frame:
                self._hstack = ui.HStack(spacing=10)
                with self._hstack:
                    self._vstack = ui.VStack(spacing=5)
                    with self._vstack:
                        labeled_FloatDrag(
                            self.props,
                            self._vstack,
                            "Max Linear Deflection",
                            0,
                            100,
                            0.001,
                            80,
                            tooltipFn=lin_deflection_tooltip,
                        )
                        labeled_FloatDrag(
                            self.props,
                            self._vstack,
                            "Max Angular Deflection",
                            0,
                            10,
                            0.5,
                            80,
                            tooltipFn=ang_deflection_tooltip,
                        )
                        labeled_FloatDrag(
                            self.props, self._vstack, "Min Surface Area", -1, 10, -1, 80, tooltipFn=surface_area_tooltip
                        )
                        labeled_CheckBox(
                            self.props, self._vstack, "Use Relative Offset", True, tooltipFn=rel_offset_tooltip
                        )
                        labeled_CheckBox(
                            self.props, self._vstack, "Use Internal Vertices", True, tooltipFn=int_verts_tooltip
                        )
                        labeled_CheckBox(self.props, self._vstack, "Re-Center meshes", True, tooltipFn=com_tooltip)
                        self._step_picker_button = ui.Button(
                            "load STEP", clicked_fn=lambda a=self: self._select_file(a)
                        )
                    self._model = AssemblyTreeModel()
                    with ui.VStack(spacing=10):
                        self._sf = ui.ScrollingFrame(
                            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                            style_type_name_override="TreeView.ScrollingFrame",
                            style=self.tree_style,
                            height=ui.Percent(100)
                            # mouse_pressed_fn=lambda x, y, b, _: self._delegate.on_mouse_pressed(b, None, False),
                        )
                        with self._sf:
                            self._treeView = ui.TreeView(
                                self._model,
                                column_widths=[ui.Fraction(1), 80],
                                root_visible=False,
                                header_visible=True,
                                delegate=self._delegate,
                                style=self.tree_style,
                            )
                            # self._treeView.build_header = self.build_header
                            # self._sf.visible = False

        else:
            self._window = None
            self._model.reset()
            self._model = None
            self.part = _step_importer.Part()

    @staticmethod
    def dummy(a, b):
        pass

    def on_shutdown(self):
        print("Shutting down Step Importer")
        if self._filepicker:
            self._filepicker.set_file_selected_fn(None)
            self._filepicker = None
        self._menu = None
        self._model.reset()
        self._model = None
        del self.part
        self.part = None
        gc.collect()
        # _step_importer.release_interface(self._si)

    def _select_file(self, btn_widget):
        if not self._filepicker:
            self._filepicker = omni.kit.ui.FilePicker(
                "Select STEP File", file_type=omni.kit.ui.FileDialogSelectType.FILE
            )
            self._filepicker.set_file_selected_fn(self._select_picked_folder_callback)
            self._filepicker.add_filter("STEP Files (*.step | *.stp)", r".*.step$|.*.stp$")
        self._filepicker.show()

    async def _import_file(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            path, basename = os.path.split(self.path)
            basename = os.path.splitext(basename)[0]
            exporter = usd_exporter.PartExporter(self.part, path, basename, self._model)
            self._model.reset()
            # Close current stage to ensure it can override
            if omni.usd.get_context().can_close_stage():
                omni.usd.get_context().close_stage(on_finish_fn=exporter)
            else:
                omni.usd.get_context().new_stage(on_finish_fn=Callback_Exporter(exporter))
            self._sf.visible = True

    def _select_picked_folder_callback(self, path):
        print(path)
        if not path.startswith("omniverse://"):
            self.path = path
            props = _step_importer.Tesselation_Properties()
            props.max_linear_offset = float(self.props["Max Linear Deflection"].model.get_value_as_float())
            props.max_angular_offset = float(self.props["Max Angular Deflection"].model.get_value_as_float())
            props.min_surface = float(self.props["Min Surface Area"].model.get_value_as_float())
            props.use_relative_offset = self.props["Use Relative Offset"].model.get_value_as_bool()
            props.use_internal_vertices = self.props["Use Internal Vertices"].model.get_value_as_bool()
            props.volumetric_center_meshes = self.props["Re-Center meshes"].model.get_value_as_bool()

            task = asyncio.ensure_future(self.async_import(path, props, self.part))

            asyncio.ensure_future(self._import_file(task))
        else:
            self._model.reset()
            self.path = ""
            self._exporter_button.enabled = False
            carb.log_error("Only Local Paths supported")
