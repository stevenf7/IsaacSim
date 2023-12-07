# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import os

import carb
import omni.kit.commands
import omni.kit.test
import omni.kit.usd
import omni.kit.viewport.utility
import omni.usd
from omni.isaac.internal_tools.utils.file_utils import (
    filter_usd,
    has_missing_reference,
    is_external,
    isabs,
    list_references,
    list_sub_files,
)
from omni.physx import get_physx_interface
from pxr import Sdf, Usd, UsdGeom, UsdUtils


# This test is part of internal utils because it needs internal servers
class TestAssets(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        # set these settings to make sure we load deterministically
        await self.setup_stage()
        await omni.kit.app.get_app().next_update_async()
        # Hide viewport to reduce load times
        window = omni.kit.viewport.utility.get_active_viewport_window()
        window.viewport_api.updates_enabled = False
        # await omni.kit.app.get_app().next_update_async()
        self.root_path = carb.settings.get_settings().get("/persistent/isaac/asset_root/isaac")
        self.nvidia_path = carb.settings.get_settings().get("/persistent/isaac/asset_root/nvidia")
        self.search_path = [
            self.root_path,
            # self.nvidia_path + "/Assets/AnimGraph",
            # self.nvidia_path + "/Assets/ArchVis",
            # self.nvidia_path + "/Assets/Audio2Face",
            # self.nvidia_path + "/Assets/Characters",
            # self.nvidia_path + "/Assets/Particles",
            # self.nvidia_path + "/Assets/Scenes",
            # self.nvidia_path + "/Assets/Skies",
            # self.nvidia_path + "/Assets/Vegetation",
            # self.nvidia_path + "/Materials",
        ]

        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    async def setup_stage(self):
        await omni.kit.app.get_app().next_update_async()

    async def close_stage(self):
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await asyncio.sleep(0.25)
            await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        await omni.usd.get_context().close_stage_async()
        await asyncio.sleep(0.25)
        await omni.kit.app.get_app().next_update_async()

    def duplicate_check(self, all_files):
        file_names = [os.path.basename(file) for file in all_files]

        def indices(lst, item):
            return [i for i, x in enumerate(lst) if x == item]

        for idx, file in enumerate(all_files):
            # print(idx, x)
            if ".thumbs" not in file:
                idx = indices(file_names, file_names[idx])
                if len(idx) > 1:
                    print(f"duplicate entry for {file}")
                    [print(all_files[id]) for id in idx]

    async def test_validate_all_assets(self):
        print("Starting validation")
        count = 0
        all_files = await list_sub_files(self.search_path)
        sub_files = [file for file in all_files if filter_usd(file)]
        print(f"found a total of {len(all_files)} files and {len(sub_files)} usd* files")
        # check for duplicate base filenames
        # self.duplicate_check(all_files)

        total_files = len(sub_files)
        results = []
        for item in sub_files:
            # print(f"opening: {item}")
            file_results = []
            # first make sure all assets open
            await omni.kit.app.get_app().next_update_async()
            if False:
                await self.close_stage()
                await omni.kit.app.get_app().next_update_async()
                await omni.usd.get_context().open_stage_async(item)
                await omni.kit.app.get_app().next_update_async()
                await self.setup_stage()
                await omni.kit.app.get_app().next_update_async()
                self._stage = omni.usd.get_context().get_stage()
                self.check_physics_schema(item)
            else:
                self._stage = Usd.Stage.Open(item)
                await omni.kit.app.get_app().next_update_async()

            # file_results.extend(self.check_stage_units(item))

            # TODO: Old Camera Prim Check
            for prim in self._stage.Traverse():
                file_results.extend(self.check_missing_ref(item, prim))
                file_results.extend(self.check_deleted_ref(item, prim))
                file_results.extend(self.check_deleted_payload(item, prim))
                file_results.extend(self.check_properties(item, prim))
            # TODO: Instance Check?
            file_results.extend(self.check_abs_refs(item))
            # file_results.extend(self.check_external_refs(item))
            # print(f"opened: {count} of {total_files}, {item}, found {len(file_results)} issues")
            results.extend(file_results)
            count = count + 1
        if len(results) > 0:
            for l in results:
                carb.log_error(l)
        self.assertEqual(len(results), 0)

    def check_stage_units(self, usd_path):
        units = UsdGeom.GetStageMetersPerUnit(self._stage)
        if units != 1.0:
            return [f"stage: {usd_path}, has stage which are not in meters"]
        else:
            return []

    def check_physics_schema(self, usd_path):
        if get_physx_interface().check_backwards_compatibility() is True:
            return [f"stage: {usd_path}, has an old physics schema"]
        else:
            return []

    def check_missing_ref(self, usd_path, prim):
        if has_missing_reference(prim) is True:
            return [f"stage: {usd_path}, has missing references for {prim}"]
        else:
            return []

    def check_external_refs(self, usd_path):
        ext_refs = [i for i in list_references(usd_path, resolve_relatives=False) if is_external(i, self.root_path)]
        if len(ext_refs) != 0:
            return [f"stage: {usd_path}, has external references {ext_refs}"]
        else:
            return []

    def check_abs_refs(self, usd_path):
        abs_refs = [i for i in list_references(usd_path) if isabs(i)]
        if len(abs_refs) != 0:
            return [f"stage: {usd_path}, has absolute references {abs_refs}"]
        else:
            return []

    def check_properties(self, item, prim):
        abs_refs = []
        try:
            if prim.GetAttributes() is not None:
                for attr in prim.GetAttributes():
                    if attr.GetTypeName() == Sdf.ValueTypeNames.String:
                        if attr.Get() is not None:
                            if "omniverse://" in attr.Get():
                                abs_refs.append(attr.Get())

            if len(abs_refs) != 0:
                return [f"File:{item} Prim {prim} Contains a absolute reference {abs_refs}"]
            else:
                return []
        except Exception as e:
            carb.log_error(f"{e} fail to check {item}, {prim}")

    def check_deleted_ref(self, usd_path, prim):
        stage = omni.usd.get_context().get_stage()
        if stage is None:
            return []
        ref_prim_spec = stage.GetRootLayer().GetPrimAtPath(prim.GetPath())
        if ref_prim_spec:
            references_info = ref_prim_spec.GetInfo("references")
            if len(references_info.deletedItems) > 0:
                return [f"stage: {usd_path}, has deleted references {references_info.deletedItems}"]
            else:
                return []

    def check_deleted_payload(self, usd_path, prim):
        stage = omni.usd.get_context().get_stage()
        if stage is None:
            return []
        ref_prim_spec = stage.GetRootLayer().GetPrimAtPath(prim.GetPath())
        if ref_prim_spec:
            payload_info = ref_prim_spec.GetInfo("payload")
            if len(payload_info.deletedItems) > 0:
                return [f"stage: {usd_path}, has deleted payload {payload_info.deletedItems}"]
            else:
                return []
