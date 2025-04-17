# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import isaacsim.core.utils.stage as stage_utils
import numpy as np
import omni.kit.test
import omni.usd
import warp as wp
from isaacsim.core.experimental.prims import XformPrim, use_backend
from isaacsim.core.simulation_manager import IsaacEvents, SimulationManager

from .utils import check_allclose, check_array, check_equal, draw_choice, draw_indices, draw_sample


def parametrize(devices: list[str], backends: list[str], amounts: list[str], max_num_prims: int = 5):
    def decorator(func):
        async def wrapper(self):
            for device in devices:
                for backend in backends:
                    for amount in amounts:
                        print(f"  |-- device: {device}, backend: {backend}, amount: {amount}")
                        # create new stage
                        await stage_utils.create_new_stage_async()
                        # define prims
                        stage = omni.usd.get_context().get_stage()
                        for i in range(max_num_prims):
                            stage.DefinePrim(f"/World/A_{i}", "Xform")
                            stage.DefinePrim(f"/World/A_{i}/B", "Cube")
                        # configure simulation manager
                        SimulationManager.set_backend("warp")
                        SimulationManager.set_physics_sim_device(device)
                        # parametrize test
                        prim = XformPrim("/World/A_0" if amount == "one" else "/World/A_.*")
                        num_prims = 1 if amount == "one" else max_num_prims
                        # call test method according to backend
                        if backend == "tensor":
                            omni.timeline.get_timeline_interface().play()
                            await omni.kit.app.get_app().next_update_async()
                            await func(
                                self,
                                prim=prim,
                                num_prims=num_prims,
                                device=device,
                                backend=backend,
                            )
                            omni.timeline.get_timeline_interface().stop()
                        elif backend in ["usd", "usdrt", "fabric"]:
                            await func(
                                self,
                                prim=prim,
                                num_prims=num_prims,
                                device=device,
                                backend=backend,
                            )
                        else:
                            raise ValueError(f"Invalid backend: {backend}")

        return wrapper

    return decorator


class TestXformPrim(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        super().tearDown()

    # --------------------------------------------------------------------

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_len(self, prim, num_prims, device, backend):
        self.assertEqual(len(prim), num_prims, f"Invalid XformPrim ({num_prims} prims) len")

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_visibilities(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output, shape=(count, 1), dtype=wp.bool)
            check_equal(expected_output, output.numpy(), msg=f"Visibilities ({type(input)}): {input}")

        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for value, expected_value in draw_sample(shape=(expected_count, 1), dtype=wp.bool):
                prim.set_visibilities(value, indices=indices)
                output = prim.get_visibilities(indices=indices)
                _check(value, expected_value, output, expected_count)

    @parametrize(devices=["cpu", "cuda"], backends=["usd", "usdrt", "fabric"], amounts=["one", "many"])
    async def test_world_poses(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output[0], shape=(count, 3), dtype=wp.float32, device=device)
            check_array(output[1], shape=(count, 4), dtype=wp.float32, device=device)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"Positions ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"Orientations ({type(input[1])})\n{input[1]}")

        # check backend
        if backend in ["usdrt", "fabric"]:
            await omni.kit.app.get_app().next_update_async()
        else:
            prim.reset_xform_op_properties()
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for (positions, expected_positions), (orientations, expected_orientations) in zip(
                draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                draw_sample(shape=(expected_count, 4), dtype=wp.float32, normalized=True),
            ):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_world_poses(positions, orientations, indices=indices)
                    output = prim.get_world_poses(indices=indices)
                _check((positions, orientations), (expected_positions, expected_orientations), output, expected_count)

    @parametrize(devices=["cpu", "cuda"], backends=["usd", "usdrt", "fabric"], amounts=["one", "many"])
    async def test_local_poses(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output[0], shape=(count, 3), dtype=wp.float32)
            check_array(output[1], shape=(count, 4), dtype=wp.float32)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"Translations ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"Orientations ({type(input[1])})\n{input[1]}")

        # check backend
        if backend in ["usdrt", "fabric"]:
            await omni.kit.app.get_app().next_update_async()
        else:
            prim.reset_xform_op_properties()
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for (translations, expected_translations), (orientations, expected_orientations) in zip(
                draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                draw_sample(shape=(expected_count, 4), dtype=wp.float32, normalized=True),
            ):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_local_poses(translations, orientations, indices=indices)
                    output = prim.get_local_poses(indices=indices)
                _check(
                    (translations, orientations), (expected_translations, expected_orientations), output, expected_count
                )

    @parametrize(devices=["cpu", "cuda"], backends=["usd", "usdrt", "fabric"], amounts=["one", "many"])
    async def test_local_scales(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output, shape=(count, 3), dtype=wp.float32)
            check_allclose(expected_output, output.numpy(), msg=f"Scales ({type(input)}): {input}")

        # check backend
        if backend in ["usdrt", "fabric"]:
            await omni.kit.app.get_app().next_update_async()
        else:
            prim.reset_xform_op_properties()
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for value, expected_value in draw_sample(shape=(expected_count, 3), dtype=wp.float32):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_local_scales(value, indices=indices)
                    output = prim.get_local_scales(indices=indices)
                _check(value, expected_value, output, expected_count)

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_default_state(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output[0], shape=(count, 3), dtype=wp.float32)
            check_array(output[1], shape=(count, 4), dtype=wp.float32)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"Positions ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"Orientations ({type(input[1])})\n{input[1]}")

        prim.reset_xform_op_properties()
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for (positions, expected_positions), (orientations, expected_orientations) in zip(
                draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                draw_sample(shape=(expected_count, 4), dtype=wp.float32, normalized=True),
            ):
                prim.set_default_state(positions, orientations, indices=indices)
                output = prim.get_default_state(indices=indices)
                prim.reset_to_default_state()
                _check((positions, orientations), (expected_positions, expected_orientations), output, expected_count)

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_visual_materials(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            assert len(expected_output) == len(
                output
            ), f"Unexpected materials length: expected {len(expected_output)}, got {len(output)}"
            for expected, value in zip(expected_output, output):
                assert type(expected) == type(
                    value
                ), f"Unexpected material type: expected {type(expected)}, got {type(value)}"

        from isaacsim.core.api.materials import OmniGlass, OmniPBR, PreviewSurface

        materials = [
            OmniGlass(prim_path="/materials/omni_glass"),
            OmniPBR(prim_path="/materials/omni_pbr"),
            PreviewSurface(prim_path="/materials/preview_surface"),
        ]
        # test cases
        # - check the number of applied materials before applying any material
        output = prim.get_applied_visual_materials()
        number_of_materials = sum(1 for material in output if material is not None)
        assert number_of_materials == 0, f"No material should have been applied. Applied: {number_of_materials}"
        # - by indices
        for indices, expected_count in draw_indices(count=num_prims, step=2, types=[list, np.ndarray, wp.array]):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            count = expected_count
            for value, expected_value in draw_choice(shape=(count,), choices=materials):
                prim.apply_visual_materials(value, indices=indices)
                output = prim.get_applied_visual_materials(indices=indices)
                _check(value, expected_value, output, count)
        # - check the number of applied materials after applying materials by indices
        output = prim.get_applied_visual_materials()
        number_of_materials = sum(1 for material in output if material is not None)
        assert (
            number_of_materials == count
        ), f"{count} materials should have been applied. Applied: {number_of_materials}"
        # - all
        count = num_prims
        for value, expected_value in draw_choice(shape=(count,), choices=materials):
            prim.apply_visual_materials(value)
            output = prim.get_applied_visual_materials()
            _check(value, expected_value, output, count)
        # - check the number of applied materials after applying materials by all
        output = prim.get_applied_visual_materials()
        number_of_materials = sum(1 for material in output if material is not None)
        assert (
            number_of_materials == count
        ), f"{count} materials should have been applied. Applied: {number_of_materials}"

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_events(self, prim, num_prims, device, backend):
        prim.reset_xform_op_properties()
        # trigger events automatically
        timeline = omni.timeline.get_timeline_interface()
        for _ in range(2):
            timeline.play()
            for _ in range(2):
                await omni.kit.app.get_app().next_update_async()
            timeline.stop()
        # trigger events manually
        event_dispatcher = carb.eventdispatcher.get_eventdispatcher()
        event_dispatcher.dispatch_event(IsaacEvents.PHYSICS_WARMUP.value, payload={})
        event_dispatcher.dispatch_event(IsaacEvents.SIMULATION_VIEW_CREATED.value, payload={})
        event_dispatcher.dispatch_event(IsaacEvents.PHYSICS_READY.value, payload={})
        event_dispatcher.dispatch_event(IsaacEvents.POST_RESET.value, payload={})
        event_dispatcher.dispatch_event(IsaacEvents.PRIM_DELETION.value, payload={})
        event_dispatcher.dispatch_event(IsaacEvents.PRE_PHYSICS_STEP.value, payload={})
        event_dispatcher.dispatch_event(IsaacEvents.POST_PHYSICS_STEP.value, payload={})
        event_dispatcher.dispatch_event(IsaacEvents.TIMELINE_STOP.value, payload={})
