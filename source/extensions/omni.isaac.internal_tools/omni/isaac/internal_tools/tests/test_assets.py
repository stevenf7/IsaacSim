# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.test

import omni.kit.usd
import omni.kit.commands
from omni.isaac.internal_tools.utils.file_utils import list_sub_files, filter_usd
import carb
import asyncio
import os
from pxr import UsdGeom, UsdUtils, Usd, Sdf
from omni.physx import get_physx_interface
from omni.isaac.internal_tools.utils.file_utils import list_references, is_external, has_missing_reference, isabs
import omni.kit.viewport.utility

# This test is part of internal utils because it needs internal servers
class TestAssets(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        # set these settings to make sure we load deterministically
        await self.setup_stage()
        await omni.kit.app.get_app().next_update_async()
        # Hide viewport to reduce load times
        omni.kit.viewport.utility.get_active_viewport_window().set_visible(False)
        # await omni.kit.app.get_app().next_update_async()
        self.root_path = carb.settings.get_settings().get("/persistent/isaac/asset_root/isaac")
        self.nvidia_path = carb.settings.get_settings().get("/persistent/isaac/asset_root/nvidia")
        self.search_path = [
            self.root_path,
            self.nvidia_path + "/Assets/AnimGraph",
            self.nvidia_path + "/Assets/ArchVis",
            self.nvidia_path + "/Assets/Audio2Face",
            self.nvidia_path + "/Assets/Characters",
            self.nvidia_path + "/Assets/Particles",
            self.nvidia_path + "/Assets/Scenes",
            self.nvidia_path + "/Assets/Skies",
            self.nvidia_path + "/Assets/Vegetation",
            self.nvidia_path + "/Materials",
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

    async def test_validate_all_assets(self):
        print("Starting validation")
        count = 0
        sub_files = await list_sub_files(self.search_path, filter_usd)
        total_files = len(sub_files)
        results = []
        for item in sub_files:

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
                file_results.extend(self.check_properties(item, prim))
            # TODO: Instance Check?
            file_results.extend(self.check_abs_refs(item))
            # file_results.extend(self.check_external_refs(item))
            print(f"opened: {count} of {total_files}, {item}, found {len(file_results)} issues")
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
