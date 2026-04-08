# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Callable, Literal

import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import omni.kit.test
import warp as wp
from isaacsim.core.experimental.prims.tests.common import cprint
from isaacsim.core.rendering_manager import ViewportManager
from isaacsim.sensors.experimental.rtx import (
    Acoustic,
    AcousticSensor,
    parse_generic_model_output_data,
    parse_stable_id_map_data,
)

from .common import create_sarcophagus

EXPECTED_ANNOTATOR_SPEC = {
    "stable-id-map": {"dtype": wp.uint8, "type": wp.array},
    "generic-model-output": {"dtype": wp.uint8, "type": wp.array},
}


def parametrize(
    *,
    instances: list[Literal["one", "many"]] = ["one"],
    operations: list[Literal["wrap", "create"]] = ["wrap", "create"],
    sensor_class: type,
    sensor_class_kwargs: dict = {},
    populate_stage_func: Callable[[int, Literal["wrap", "create"]], None],
    populate_stage_func_kwargs: dict = {},
    max_num_prims: int = 1,
):
    def decorator(func):
        async def wrapper(self):
            for instance in instances:
                for operation in operations:
                    assert instance in ["one"], f"Invalid instance: {instance}. Only one instance is supported"
                    assert operation in ["wrap", "create"], f"Invalid operation: {operation}"
                    cprint(f"  |-- instance: {instance}, operation: {operation}")
                    # populate stage
                    await populate_stage_func(max_num_prims, operation, **populate_stage_func_kwargs)
                    # parametrize test
                    if operation == "wrap":
                        paths = "/World/A_0" if instance == "one" else "/World/A_.*"
                    elif operation == "create":
                        paths = "/World/A_0" if instance == "one" else [f"/World/A_{i}" for i in range(max_num_prims)]
                    sensor = sensor_class(paths, **sensor_class_kwargs)
                    num_prims = 1 if instance == "one" else max_num_prims
                    # run test function
                    app_utils.play(commit=True)
                    await app_utils.update_app_async(steps=10)
                    try:
                        await func(self, sensor=sensor, num_prims=num_prims, operation=operation)
                    finally:
                        app_utils.stop(commit=True)
                        await app_utils.update_app_async()
                        del sensor  # needed to destroy/release everything before the next test
                        await app_utils.update_app_async(steps=3)

        return wrapper

    return decorator


async def populate_stage(max_num_prims: int, operation: Literal["wrap", "create"], **kwargs) -> None:
    # create new stage
    await stage_utils.create_new_stage_async()
    # wait for the viewport to be ready
    await ViewportManager.wait_for_viewport_async()
    # define some shapes
    create_sarcophagus()
    # define acoustic prims
    if operation == "wrap":
        for i in range(max_num_prims):
            prim = stage_utils.define_prim(f"/World/A_{i}", "OmniAcoustic")
            prim.ApplyAPI("OmniSensorGenericAcousticWpmAPI")


class TestAcousticSensor(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()
        self.maxDiff = None  # show all diffs

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        super().tearDown()

    # --------------------------------------------------------------------

    @parametrize(
        sensor_class=AcousticSensor,
        sensor_class_kwargs={"annotators": list(EXPECTED_ANNOTATOR_SPEC.keys())},
        populate_stage_func=populate_stage,
    )
    async def test_data(self, sensor, num_prims, operation):
        for annotator in sorted(list(EXPECTED_ANNOTATOR_SPEC.keys())):
            cprint(f"  |    |-- annotator: {annotator}")
            spec = EXPECTED_ANNOTATOR_SPEC[annotator]
            data, info = None, {}
            for i in range(10):
                await app_utils.update_app_async()
                data, info = sensor.get_data(annotator)
                # if data is not None:
                #     break
            if data is None:
                raise RuntimeError(f"No data available from '{annotator}' annotator after {i + 1} steps")
            else:
                cprint(f"  |    |    |-- data available after {i + 1} steps")

                # check data
                # - type
                self.assertIsInstance(
                    data, spec["type"], f"'{annotator}' annotator type {type(data)} != {spec['type']}"
                )
                # - dtype
                dtype = spec["dtype"]
                self.assertEqual(data.dtype, dtype, f"'{annotator}' annotator dtype {data.dtype} != {dtype}")
                # - data
                if annotator == "stable-id-map":
                    stable_id_map = parse_stable_id_map_data(data)
                    self.assertTrue(len(set(stable_id_map.values())), "Expected one or more stable IDs")
                    for value in stable_id_map.values():
                        self.assertTrue(value.startswith("/World/cube_"), f"Unexpected stable ID value: {value}")
                elif annotator == "generic-model-output":
                    generic_model_output = parse_generic_model_output_data(data)
                    self.assertTrue(generic_model_output.x.size, msg=f"Expected non-empty X coordinates")
                    self.assertTrue(generic_model_output.y.size, msg=f"Expected non-empty Y coordinates")
                    self.assertTrue(generic_model_output.z.size, msg=f"Expected non-empty Z coordinates")
                else:
                    raise ValueError(f"Unsupported annotator '{annotator}' for testing")
                # - info
                self.assertDictEqual({}, info, msg=f"Annotator info mismatch for '{annotator}'")
