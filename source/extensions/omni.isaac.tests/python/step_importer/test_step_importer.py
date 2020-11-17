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
from pxr import Usd, UsdLux, UsdGeom, Sdf, Gf, Tf, UsdPhysics, PhysicsSchemaTools
from omni.physx import _physx as physx

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.step_importer.scripts import usd_exporter
from omni.isaac.step_importer import _step_importer


class TestStepImporter(omni.kit.test.AsyncTestCaseFailOnLogError):

    # Before running each test
    async def setUp(self):
        self._si = _step_importer.acquire_interface()
        self.part = _step_importer.Part()
        self.exporter = None
        self.path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve(os.path.join(os.path.dirname(__file__), "../data/test.stp"))
        )
        self.assertTrue(os.path.isfile(self.path))
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
