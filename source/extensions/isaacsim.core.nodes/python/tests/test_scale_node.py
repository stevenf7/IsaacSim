# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


import omni.graph.core as og
import omni.graph.core.tests as ogts
import omni.kit.test


class TestScaleFromStageUnit(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Set up  test environment, to be torn down when done"""
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()

    # ----------------------------------------------------------------------
    async def tearDown(self):
        pass

    # ----------------------------------------------------------------------
    async def test_create_scale_node(self):
        graph_path = "/ActionGraph"
        nodeName = "isaac_test_node"

        (test_graph, new_nodes, _, _) = og.Controller.edit(
            {"graph_path": graph_path, "evaluator_name": "execution"},
            {
                og.Controller.Keys.CREATE_NODES: [
                    (nodeName, "isaacsim.core.nodes.OgnIsaacScaleToFromStageUnit"),
                ],
            },
        )

        await omni.kit.app.get_app().next_update_async()
