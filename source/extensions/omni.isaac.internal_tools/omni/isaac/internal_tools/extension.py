# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import omni.ext
from omni import ui
from .utils.file_utils import *
import weakref
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
import asyncio

EXTENSION_NAME = "Internal Tools"


class InternalTools(omni.ext.IExt):
    def on_startup(self):
        self._menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        add_menu_items(self._menu_items, "Isaac Utils")
        self._window = ui.Window(
            title=EXTENSION_NAME, width=800, height=400, visible=False, dockPreference=ui.DockPreference.LEFT_BOTTOM
        )
        default_server = carb.settings.get_settings().get("/persistent/isaac/asset_root/isaac")
        with self._window.frame:
            with ui.VStack(height=0):
                with ui.HStack(height=0):
                    ui.Label("Base Path:", width=0)
                    self.path_txt = ui.StringField()
                    self.path_txt.model.set_value(default_server)
                ui.Button("Check for Absolute Path References", clicked_fn=self.check_for_abs_paths)
                ui.Button("Check for References Outside base folder", clicked_fn=self.check_for_external_refs)
                ui.Button("Check for missing refs", clicked_fn=self.check_for_missing_refs)
                ui.Button("Assets not referenced by other assets", clicked_fn=self.get_assets_ref_count)
                ui.Button("Check for assets that cannot be released", clicked_fn=self.get_unreleasable)
                ui.Button("Check for deprecated physics schema", clicked_fn=self.check_physics_schema)
                ui.Button("List All MDLs", clicked_fn=self.print_mdls)
                ui.Button("Check If Instances Exist", clicked_fn=self.check_instancing)
                # ui.Button("Check Untyped", clicked_fn=self.remove_untyped)

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Utils")
        self._window = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def check_for_abs_paths(self):
        print("checking for absolute paths")

        async def check():
            items = await check_for_abs_paths(self.path_txt.model.get_value_as_string())
            if len(items):
                for key, value in items.items():
                    print(key, value)
            else:
                print("No absolute path references found")

        asyncio.ensure_future(check())

    def check_for_external_refs(self):
        print("checking for external refs")

        async def check():
            items = await check_for_external_refs(self.path_txt.model.get_value_as_string())
            if len(items):
                for key, value in items.items():
                    print(key, value)
            else:
                print("No external references found")

        asyncio.ensure_future(check())

    def check_for_missing_refs(self):
        print("checking for missing refs")

        async def check():
            await check_for_missing_refs(self.path_txt.model.get_value_as_string())

        asyncio.ensure_future(check())
        print("done checking")

    def get_assets_ref_count(self):
        async def check():
            items = await get_assets_ref_count(self.path_txt.model.get_value_as_string())
            for key, value in items.items():
                if value == 0:
                    print(value, ":", key)

        asyncio.ensure_future(check())

    def get_unreleasable(self):
        asset_paths = [
            "/Isaac/Robots/UR10/robotiq",
            "/Isaac/Robots/UR10/ur10_robotiq.usd",
            "/Isaac/Robots/UR10/ur10_schmalz.usd",
            "/Isaac/Samples/Leonardo/Stage/ur10_bin_stacking_robotiq.usd",
        ]

        async def check():
            for asset in asset_paths:
                path = "{}{}".format(self.path_txt.model.get_value_as_string(), asset)
                if await check_if_exists(path):
                    carb.log_error("Asset {} should not exist on this server for release".format(path))
                else:
                    print("Asset {} not found".format(path))

        asyncio.ensure_future(check())

    def check_physics_schema(self):
        from omni.physx import get_physx_interface

        base_path = self.path_txt.model.get_value_as_string()
        print("Checking for deprecated physx schemas")

        async def setup():
            carb.settings.get_settings().set_int("/persistent/physics/backwardCompatibilityCheckMode", 0)
            carb.settings.get_settings().set("/exts/omni.kit.thumbnails.usd/thumbnail_on_save", False)
            carb.settings.get_settings().set("/omni.kit.plugin/syncUsdLoads", True)
            carb.settings.get_settings().set("/rtx/hydra/materialSyncLoads", True)
            carb.settings.get_settings().set("/rtx/materialDb/syncLoads", True)
            # carb.settings.get_settings().set_int("/rtx/debugMaterialType", 0) # this causes issues when saving, as its a file setting
            await omni.kit.app.get_app().next_update_async()

        async def check_schema():
            await omni.kit.app.get_app().next_update_async()
            omni.kit.viewport_legacy.get_default_viewport_window().set_visible(False)
            await omni.kit.app.get_app().next_update_async()
            await omni.kit.app.get_app().next_update_async()
            await omni.kit.app.get_app().next_update_async()

            bad_files = []
            for item in await list_sub_files(base_path, filter_usd):
                await omni.kit.app.get_app().next_update_async()
                await omni.usd.get_context().open_stage_async(item)
                await omni.kit.app.get_app().next_update_async()
                await setup()
                if get_physx_interface().check_backwards_compatibility():
                    print("Bad File", item)
                    # HAMMAD: Comment out below to store changes, disabled to prevent accidents
                    # get_physx_interface().run_backwards_compatibility()
                    # await omni.kit.app.get_app().next_update_async()
                    # await omni.usd.get_context().save_stage_async()
                    # await omni.kit.app.get_app().next_update_async()
                    bad_files.append(item)
                else:
                    # print("GOOD", item)
                    pass
                # closing causes things to crash randomly
                # await omni.kit.app.get_app().next_update_async()
                # await omni.usd.get_context().close_stage_async()
                # await omni.kit.app.get_app().next_update_async()
            print(bad_files)
            print("Deprecated physx schema check complete")

        asyncio.ensure_future(check_schema())

    def print_mdls(self):
        async def check():
            base_path = self.path_txt.model.get_value_as_string()
            for item in await list_sub_files(base_path, filter_mdl):
                print(item)

        asyncio.ensure_future(check())

    def check_instancing(self):
        import pxr

        async def check():
            print("Starting check for any instances")
            base_path = self.path_txt.model.get_value_as_string()
            for item in await list_sub_files(base_path, filter_usd):
                stage = pxr.Usd.Stage.Open(item)
                for prim in stage.Traverse():
                    if prim.IsInstanceable():
                        print(item, prim)

        asyncio.ensure_future(check())
        print("Instance check complete")

    # def remove_untyped(self):
    #     import pxr

    #     base_path = self.path_txt.model.get_value_as_string()
    #     for item in list_sub_files(base_path, filter_usd):
    #         stage = pxr.Usd.Stage.Open(item)
    #         changed = False
    #         print("opened:", item)
    #         to_delete = []
    #         for prim in stage.Traverse():
    #             if len(prim.GetTypeName()) == 0:
    #                 if prim.GetName() == "collision":
    #                     to_delete.append(prim.GetPath())
    #         for prim_path in to_delete:
    #             print("deleting: ", prim_path)
    #             stage.RemovePrim(prim_path)
    #             changed = True
    #         if changed:
    #             print("saving:", item)
    #             stage.Save()
