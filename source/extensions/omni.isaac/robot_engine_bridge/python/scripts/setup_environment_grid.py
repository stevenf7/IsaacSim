# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from pxr import Usd, UsdGeom, Sdf, Gf
import omni.kit.editor
import omni.usd
import omni.ext


# Utility function to specify the stage with the z axis as "up"
def setUpZAxis(stage):
    rootLayer = stage.GetRootLayer()
    rootLayer.SetPermissionToEdit(True)
    with Usd.EditContext(stage, rootLayer):
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)


# Specify position of a given prim, reuse any existing transform ops when possible
def setTranslate(prim, new_loc):
    properties = prim.GetPropertyNames()
    if "xformOp:translate" in properties:
        translate_attr = prim.GetAttribute("xformOp:translate")
        translate_attr.Set(new_loc)
    elif "xformOp:translation" in properties:
        translation_attr = prim.GetAttribute("xformOp:translate")
        translation_attr.Set(new_loc)
    elif "xformOp:transform" in properties:
        transform_attr = prim.GetAttribute("xformOp:transform")
        matrix = prim.GetAttribute("xformOp:transform").Get()
        matrix.SetTranslateOnly(new_loc)
        transform_attr.Set(matrix)
    else:
        xform = UsdGeom.Xformable(prim)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
        xform_op.Set(Gf.Matrix4d().SetTranslate(new_loc))


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._editor = omni.kit.editor.get_editor_interface()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        extension_name = "Setup Environment Grid"
        menu_path = f"Window/Isaac/{extension_name}"
        self._window = omni.kit.ui.Window(
            "Setup Environment Grid",
            960,
            300,
            menu_path=menu_path,
            open=False,
            dock=omni.kit.ui.DockPreference.LEFT_BOTTOM,
        )
        self._create_ui()
        pass

    def _create_ui(self):
        ui_layout = omni.kit.ui.RowColumnLayout(2, True)
        self._window.layout.add_child(ui_layout)
        ui_layout.set_column_width(0, 250)
        ui_layout.set_column_width(1, 350)
        ui_layout.add_child(omni.kit.ui.Label("Environment USD Path"))
        self._usd_env_txt = omni.kit.ui.TextBox("omniverse://ov-isaac-dev/Library/IsaacSDK/Stage/simple_rl_env.usd")
        self._usd_env_txt.width = -1
        ui_layout.add_child(self._usd_env_txt)
        ui_layout.add_child(omni.kit.ui.Label("Number of rows"))
        self._num_env_rows_int = omni.kit.ui.FieldInt("", 3)
        self._num_env_rows_int.width = -1
        ui_layout.add_child(self._num_env_rows_int)
        ui_layout.add_child(omni.kit.ui.Label("Number of columns"))
        self._num_env_cols_int = omni.kit.ui.FieldInt("", 3)
        self._num_env_cols_int.width = -1
        ui_layout.add_child(self._num_env_cols_int)
        ui_layout.add_child(omni.kit.ui.Label("Width between environments"))
        self._width_env_dbl = omni.kit.ui.FieldDouble("", 1700)
        self._width_env_dbl.width = -1
        ui_layout.add_child(self._width_env_dbl)
        ui_layout.add_child(omni.kit.ui.Label("Height Offset"))
        self._height_offset_dbl = omni.kit.ui.FieldDouble("", 40)
        self._height_offset_dbl.width = -1
        ui_layout.add_child(self._height_offset_dbl)
        ui_layout.add_child(omni.kit.ui.Label("Contact Publisher Path in Environment USD"))
        self._reb_contact_monitor = omni.kit.ui.TextBox("/REB_ContactMonitor")
        self._reb_contact_monitor.width = -1
        ui_layout.add_child(self._reb_contact_monitor)
        ui_layout.add_child(omni.kit.ui.Label("Prim To Ignore Contact With"))
        self._ignored_contacts = omni.kit.ui.TextBox("/World/staticPlaneActor/collisionPlane")
        self._ignored_contacts.width = -1
        ui_layout.add_child(self._ignored_contacts)
        self._capture_btn = ui_layout.add_child(omni.kit.ui.Button("Setup Environment"))
        self._capture_btn.set_clicked_fn(self._on_setup_fn)

    def _on_setup_fn(self, widget):
        print("Setup Started")
        self._stage = self._usd_context.get_stage()
        setUpZAxis(self._stage)

        self._num_rows = int(self._num_env_rows_int.value)
        self._num_cols = int(self._num_env_cols_int.value)
        self._num_envs = self._num_rows * self._num_cols
        self._row_width = float(self._width_env_dbl.value)
        self._usd_path = str(self._usd_env_txt.value)
        env_path = "/World/environments"
        self._stage.DefinePrim(env_path, "Xform")
        # TiledAssetSpawner
        for row_idx in range(self._num_rows):
            for col_idx in range(self._num_cols):
                path = env_path + "/env_" + str(row_idx) + "_" + str(col_idx)
                envPrim = self._stage.DefinePrim(path, "Xform")
                envPrim.GetReferences().AddReference(self._usd_path)
                setTranslate(
                    envPrim,
                    Gf.Vec3d(row_idx * self._row_width, col_idx * self._row_width, self._height_offset_dbl.value),
                )

        # SceneIndexer
        supported_channels = ["inputChannel", "outputChannel", "teleportInputChannel", "rigidBodySinkOutputChannel"]
        for row_idx in range(self._num_rows):
            for col_idx in range(self._num_cols):
                i = row_idx * self._num_cols + col_idx + 1
                path = env_path + "/env_" + str(row_idx) + "_" + str(col_idx)
                envPrim = self._stage.GetPrimAtPath(path)
                for child_prim in Usd.PrimRange(envPrim):
                    if "RobotEngine" in str(child_prim.GetTypeName()):
                        for channel_name in supported_channels:
                            if child_prim.HasAttribute(channel_name):
                                channelAttr = child_prim.GetAttribute(channel_name)
                                channelAttr.Set(channelAttr.Get() + "_" + str(i))
                contact_pub = self._stage.GetPrimAtPath(path + self._reb_contact_monitor.value)
                ignored_contacts = str(self._ignored_contacts.value).split(",")
                if contact_pub and contact_pub.GetTypeName() == "RobotEngineContactMonitor":
                    for ignored_contact in ignored_contacts:
                        contact_pub.GetRelationship("ignoredPrims").AddTarget(ignored_contact)

    def on_shutdown(self):
        print("Shutting down environment grid setup")
