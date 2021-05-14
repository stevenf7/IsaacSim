import carb
from omni.kit.widget.settings import create_setting_widget, create_setting_widget_combo, SettingType
import omni.ui as ui
from pxr import Gf
from .globals import *
from .shape import addShapePrim
import random
from .globals import g_default_omni_server


class ShapenetSettings:
    def __init__(self):
        """ build ShapeNet Settings window"""
        self._window = ui.Window(title="Shapenet Settings", visible=True, dockPreference=ui.DockPreference.LEFT_BOTTOM)

        self._settings = carb.settings.get_settings()

        # note: Not sure this is the best place to set default values.
        self._settings.set_default_string("/isaac/shapenet/omniverseServer", g_default_omni_server)
        self._settings.set_default_string("/isaac/shapenet/synsetId", "random")
        self._settings.set_default_string("/isaac/shapenet/modelId", "random")
        self._settings.set_default_float("/isaac/shapenet/posx", 0.0)
        self._settings.set_default_float("/isaac/shapenet/posy", 0.0)
        self._settings.set_default_float("/isaac/shapenet/posz", 0.0)
        self._settings.set_default_float("/isaac/shapenet/rotx", 0.0)
        self._settings.set_default_float("/isaac/shapenet/roty", 1.0)
        self._settings.set_default_float("/isaac/shapenet/rotz", 0.0)
        self._settings.set_default_float("/isaac/shapenet/rotangle", 0.0)
        self._settings.set_default_float("/isaac/shapenet/scale", 1.0)
        self._settings.set_default_bool("/isaac/shapenet/auto_add_physics", False)
        self._settings.set_default_bool("/isaac/shapenet/use_convex_decomp", False)

        self._build_window_ui()

    def _build_window_ui(self):
        """ Add Shape Settings """
        with self._window.frame:
            with ui.VStack(height=-0):
                with ui.CollapsableFrame(title="create_setting_widget"):
                    with ui.VStack(spacing=2):
                        with ui.HStack(height=24):
                            ui.Label("Omniverse Server", word_wrap=True, width=ui.Percent(35))
                            create_setting_widget("/isaac/shapenet/omniverseServer", SettingType.STRING)
                        with ui.HStack(height=24):
                            ui.Label("synsetId to add", word_wrap=True, width=ui.Percent(35))
                            create_setting_widget("/isaac/shapenet/synsetId", SettingType.STRING)
                        with ui.HStack(height=24):
                            ui.Label("modelId to add", word_wrap=True, width=ui.Percent(35))
                            create_setting_widget("/isaac/shapenet/modelId", SettingType.STRING)
                        with ui.HStack(height=24):
                            ui.Label("X Position of add", word_wrap=True, width=ui.Percent(35))
                            create_setting_widget("/isaac/shapenet/posx", SettingType.FLOAT)
                        with ui.HStack(height=24):
                            ui.Label("Y Position of add", word_wrap=True, width=ui.Percent(35))
                            create_setting_widget("/isaac/shapenet/posy", SettingType.FLOAT)
                        with ui.HStack(height=24):
                            ui.Label("Z Position of add", word_wrap=True, width=ui.Percent(35))
                            create_setting_widget("/isaac/shapenet/posz", SettingType.FLOAT)
                        with ui.HStack(height=24):
                            ui.Label("X Axis of Rotation of add", word_wrap=True, width=ui.Percent(35))
                            create_setting_widget("/isaac/shapenet/rotx", SettingType.FLOAT)
                        with ui.HStack(height=24):
                            ui.Label("Y Axis of Rotation of add", word_wrap=True, width=ui.Percent(35))
                            create_setting_widget("/isaac/shapenet/roty", SettingType.FLOAT)
                        with ui.HStack(height=24):
                            ui.Label("Z Axis of Rotation of add", word_wrap=True, width=ui.Percent(35))
                            create_setting_widget("/isaac/shapenet/rotz", SettingType.FLOAT)
                        with ui.HStack(height=24):
                            ui.Label("Angle of Rotation of add", word_wrap=True, width=ui.Percent(35))
                            create_setting_widget("/isaac/shapenet/rotangle", SettingType.FLOAT)
                        with ui.HStack(height=24):
                            ui.Label("Scale of add", word_wrap=True, width=ui.Percent(35))
                            create_setting_widget("/isaac/shapenet/scale", SettingType.FLOAT)
                        with ui.HStack(height=24):
                            ui.Label("Automatically add physics", word_wrap=True, width=ui.Percent(35))
                            create_setting_widget("/isaac/shapenet/auto_add_physics", SettingType.BOOL)
                        with ui.HStack(height=24):
                            ui.Label("Use convex decomponsition", word_wrap=True, width=ui.Percent(35))
                            create_setting_widget("/isaac/shapenet/use_convex_decomp", SettingType.BOOL)
                        with ui.HStack(height=24):
                            ui.Button("Add a model", clicked_fn=lambda b=None: self._on_add_model_fn(b))

    def _on_add_model_fn(self, widget):
        pos = self.getPos()
        rot = self.getRot()
        scale = self.getScale()

        global g_shapenet_db
        g_shapenet_db = get_database()
        if g_shapenet_db == None:
            print("Please create an Shapenet ID Database with the menu.")
            return

        synsetId = self.getSynsetId()
        if synsetId == None or synsetId == "random":
            synsetId = random.choice(list(g_shapenet_db))

        modelId = self.getModelId()
        if modelId == None or modelId == "random":
            modelId = random.choice(list(g_shapenet_db[synsetId]))

        return addShapePrim(
            self._settings.get("/isaac/shapenet/omniverseServer"),
            synsetId,
            modelId,
            pos,
            rot,
            scale,
            self._settings.get("/isaac/shapenet/auto_add_physics"),
            self._settings.get("/isaac/shapenet/use_convex_decomp"),
        )

    def getPos(self):
        x = self._settings.get("/isaac/shapenet/posx")
        y = self._settings.get("/isaac/shapenet/posy")
        z = self._settings.get("/isaac/shapenet/posz")
        return Gf.Vec3d(x, y, z)

    def getRot(self):
        x = self._settings.get("/isaac/shapenet/rotx")
        y = self._settings.get("/isaac/shapenet/roty")
        z = self._settings.get("/isaac/shapenet/rotz")
        a = self._settings.get("/isaac/shapenet/rotangle")
        return Gf.Rotation(Gf.Vec3d(x, y, z), a)

    def getScale(self):
        s = self._settings.get("/isaac/shapenet/scale")
        return s

    def getSynsetId(self):
        s = self._settings.get("/isaac/shapenet/synsetId")
        return s

    def getModelId(self):
        s = self._settings.get("/isaac/shapenet/modelId")
        return s
