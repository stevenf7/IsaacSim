# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.usd


import carb.tokens
import os
import asyncio
import numpy as np
import weakref
import carb
from pxr import Usd, UsdLux, UsdGeom, Sdf, Gf, Tf, UsdPhysics, PhysicsSchemaTools

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.step_importer.scripts import usd_exporter
from omni.isaac.step_importer import _step_importer


class TestStepImporter(omni.kit.test.AsyncTestCaseFailOnLogError):

    # Before running each test
    async def setUp(self):
        self._si = _step_importer.acquire_interface()
        self.part = _step_importer.Part()
        self.exporter = None
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.step_importer")
        self._extension_path = ext_manager.get_extension_path(ext_id)
        carb.settings.get_settings().set_string(usd_exporter.DEFAULT_TEMP_FOLDER_SETTING, self._extension_path)
        self.path = os.path.abspath(self._extension_path + "/data/step/test.stp")
        print(self.path)
        self.assertTrue(os.path.isfile(self.path))
        print(carb.settings.get_settings().get(usd_exporter.DEFAULT_TEMP_FOLDER_SETTING))
        self.basename = "test"
        self.step_file = None
        pass

    # After running each test
    async def tearDown(self):
        if self.step_file:
            self._si.release_step_file(self.step_file)
            self.step_file = None
        self.exporter = None
        del self.part
        self.part = None
        ## TODO: Fix release interface issue on windows.
        # _step_importer.release_interface(self._si)
        self._si = None
        pass

    async def test_start(self):
        pass

    async def test_load_file(self):
        self.step_file = self._si.load_step_file(self.path)
        pass

    async def test_create_exporter(self):
        await self.test_get_assembly_structure()
        self.exporter = usd_exporter.PartExporter(
            weakref.proxy(self._si), self.step_file, weakref.proxy(self.part), self.path, self.basename
        )
        pass

    async def test_get_assembly_structure(self):
        await self.test_load_file()
        self.assertTrue(self._si.get_assembly_structure(self.step_file, self.part))
        pass

    async def test_export(self):
        await self.test_create_exporter()
        self.exporter.export()
        pass

    async def test_reimport(self):
        await self.test_export()
        props = _step_importer.Tesselation_Properties()

        for i in range(4):
            self.exporter.export_mesh(i, [props], False)
        self.exporter.export(True)
        pass
