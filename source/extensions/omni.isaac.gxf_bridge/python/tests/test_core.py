# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import gc

import gxf
import gxf.core
import gxf.std

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.usd


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestGXFPython(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.gxf_bridge")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)
        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        gc.collect()
        pass

    # Create and destroy the app
    async def test_core(self):
        context = gxf.core.context_create()
        self.assertIsNotNone(context)
        gxf.core.load_extensions(
            context, manifest_filenames=["manifest.yaml"], base_directory=f"{self._reb_extension_path}/lib/"
        )
        gxf.core.graph_load_file(context, f"{self._reb_extension_path}/data/test/test_core.yaml")
        gxf.core.graph_activate(context)
        gxf.core.graph_run(context)
        gxf.core.graph_deactivate(context)
        gxf.core.context_destroy(context)

    async def test_std_tensor(self):
        context = gxf.core.context_create()
        self.assertIsNotNone(context)
        gxf.core.load_extensions(
            context, manifest_filenames=["manifest.yaml"], base_directory=f"{self._reb_extension_path}/lib/"
        )
        gxf.core.graph_load_file(context, f"{self._reb_extension_path}/data/test/test_std_tensor.yaml")

        eid = gxf.core.entity_find(context, "rx")
        cids = gxf.core.component_find(context, eid, component_name="vault")
        self.assertEqual(len(cids), 1)
        cid = cids[0]

        num_steps = 10
        count_per_step = 100

        gxf.core.graph_activate(context)
        gxf.core.graph_run_async(context)

        for i in range(num_steps):
            entities = gxf.std.store_blocking(context, cid, count_per_step)
            tensor = gxf.std.as_tensor(context, entities[0], "tensor")
            acq_time, pub_time = gxf.std.as_timestamp(context, entities[0], "timestamp")
            self.assertIsNotNone(tensor)
            self.assertIsNotNone(acq_time)
            self.assertIsNotNone(pub_time)
            print(tensor)
            print(acq_time)
            print(pub_time)
            self.assertEqual(len(entities), count_per_step)
            self.assertEqual(tensor.shape[0], 2)
            self.assertEqual(tensor.shape[1], 2)
            gxf.std.free(context, cid, entities)

        gxf.core.graph_wait(context)
        gxf.core.graph_deactivate(context)
        gxf.core.context_destroy(context)

    def test_std_vault(self):
        context = gxf.core.context_create()
        self.assertIsNotNone(context)
        gxf.core.load_extensions(
            context, manifest_filenames=["manifest.yaml"], base_directory=f"{self._reb_extension_path}/lib/"
        )
        gxf.core.graph_load_file(context, f"{self._reb_extension_path}/data/test/test_std_vault.yaml")

        eid = gxf.core.entity_find(context, "rx")
        cids = gxf.core.component_find(context, eid, component_name="vault")
        self.assertEqual(len(cids), 1)
        cid = cids[0]
        self.assertEqual(cid, 10)

        # Test with correct tid
        tid = gxf.core.tid_null()
        tid.hash1 = 1227454707155616515
        tid.hash2 = 13403506836782358117
        cids = gxf.core.component_find(context, eid, tid, "vault")
        self.assertEqual(len(cids), 1)
        self.assertEqual(cids[0], cid)
        # Test with wrong tid
        tid.hash1 = 12
        cids = gxf.core.component_find(context, eid, tid, "vault")
        self.assertEqual(len(cids), 0)

        num_steps = 10
        count_per_step = 100

        gxf.core.graph_activate(context)
        gxf.core.graph_run_async(context)

        for i in range(num_steps):
            entities = gxf.std.store_blocking(context, cid, count_per_step)
            print(entities)
            gxf.std.free(context, cid, entities)

        gxf.core.graph_wait(context)
        gxf.core.graph_deactivate(context)
        gxf.core.context_destroy(context)
