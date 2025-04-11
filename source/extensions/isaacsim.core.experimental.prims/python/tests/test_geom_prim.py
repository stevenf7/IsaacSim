# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import isaacsim.core.utils.stage as stage_utils
import numpy as np
import omni.kit.test
import omni.usd
import warp as wp
from isaacsim.core.experimental.prims import GeomPrim
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
                        prim = GeomPrim("/World/A_0" if amount == "one" else "/World/A_.*")
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
                        elif backend in ["usd", "fabric"]:
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


class TestGeomPrim(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        super().tearDown()

    # --------------------------------------------------------------------

    def check_backend(self, backend, rigid_prim):
        pass

    # --------------------------------------------------------------------

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_len(self, prim, num_prims, device, backend):
        self.assertEqual(len(prim), num_prims, f"Invalid GeomPrim ({num_prims} prims) len")

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_enabled_collisions(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output, shape=(count, 1), dtype=wp.bool, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Enabled ({type(input)})\n{input}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for enabled, expected_enabled in draw_sample(shape=(expected_count, 1), dtype=wp.bool):
                prim.set_enabled_collisions(enabled, indices=indices)
                output = prim.get_enabled_collisions(indices=indices)
                _check(enabled, expected_enabled, output, expected_count)

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_collision_approximations(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            assert len(expected_output) == len(
                output
            ), f"Unexpected collision approximations length: expected {len(expected_output)}, got {len(output)}"
            for expected, value in zip(expected_output, output):
                assert expected == value, f"Unexpected collision approximation: expected {expected}, got {value}"

        collision_approximations = [
            "none",
            "convexDecomposition",
            "convexHull",
            "boundingSphere",
            "boundingCube",
            "meshSimplification",
            "sdf",
            "sphereFill",
        ]
        # test cases
        # - check the collision approximations before applying any approximation
        approximations = prim.get_collision_approximations()
        _check(None, ["none"] * num_prims, approximations, num_prims)
        # - by indices
        for indices, expected_count in draw_indices(count=num_prims, step=2, types=[list, np.ndarray, wp.array]):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            count = expected_count
            for value, expected_value in draw_choice(shape=(count,), choices=collision_approximations):
                prim.set_collision_approximations(value, indices=indices)
                output = prim.get_collision_approximations(indices=indices)
                _check(value, expected_value, output, count)
        # - all
        count = num_prims
        for value, expected_value in draw_choice(shape=(count,), choices=collision_approximations):
            prim.set_collision_approximations(value)
            output = prim.get_collision_approximations()
            _check(value, expected_value, output, count)

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_offsets(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output[0], shape=(count, 1), dtype=wp.float32, device=device)
            check_array(output[1], shape=(count, 1), dtype=wp.float32, device=device)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"Contact offsets ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"Rest offsets ({type(input[1])})\n{input[1]}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for (contact_offsets, expected_contact_offsets), (rest_offsets, expected_rest_offsets) in zip(
                draw_sample(shape=(expected_count, 1), dtype=wp.float32),
                draw_sample(shape=(expected_count, 1), dtype=wp.float32),
            ):
                prim.set_offsets(contact_offsets, rest_offsets, indices=indices)
                output = prim.get_offsets(indices=indices)
                _check(
                    (contact_offsets, rest_offsets),
                    (expected_contact_offsets, expected_rest_offsets),
                    output,
                    expected_count,
                )

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_torsional_patch_radii(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output, shape=(count, 1), dtype=wp.float32, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Torsional patch radii ({type(input)})\n{input}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        # - standard
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for radii, expected_radii in draw_sample(shape=(expected_count, 1), dtype=wp.float32):
                prim.set_torsional_patch_radii(radii, indices=indices)
                output = prim.get_torsional_patch_radii(indices=indices)
                _check(radii, expected_radii, output, expected_count)
        # - minimum
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for radii, expected_radii in draw_sample(shape=(expected_count, 1), dtype=wp.float32):
                prim.set_torsional_patch_radii(radii, indices=indices, minimum=True)
                output = prim.get_torsional_patch_radii(indices=indices, minimum=True)

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_physics_materials(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            assert len(expected_output) == len(
                output
            ), f"Unexpected materials length: expected {len(expected_output)}, got {len(output)}"
            for expected, value in zip(expected_output, output):
                assert (
                    expected.prim_path == value.prim_path
                ), f"Unexpected material path: expected {expected.prim_path}, got {value.prim_path}"

        from isaacsim.core.api.materials import PhysicsMaterial

        materials = [
            PhysicsMaterial(
                prim_path="/physics_materials/aluminum", dynamic_friction=0.4, static_friction=1.1, restitution=0.1
            ),
            PhysicsMaterial(
                prim_path="/physics_materials/wood", dynamic_friction=0.2, static_friction=0.5, restitution=0.6
            ),
        ]
        # test cases
        # - check the number of applied materials before applying any material
        output = prim.get_applied_physics_materials()
        number_of_materials = sum(1 for material in output if material is not None)
        assert number_of_materials == 0, f"No material should have been applied. Applied: {number_of_materials}"
        # - by indices
        for indices, expected_count in draw_indices(count=num_prims, step=2, types=[list, np.ndarray, wp.array]):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            count = expected_count
            for value, expected_value in draw_choice(shape=(count,), choices=materials):
                prim.apply_physics_materials(value, indices=indices)
                output = prim.get_applied_physics_materials(indices=indices)
                _check(value, expected_value, output, count)
        # - check the number of applied materials after applying materials by indices
        output = prim.get_applied_physics_materials()
        number_of_materials = sum(1 for material in output if material is not None)
        assert (
            number_of_materials == count
        ), f"{count} materials should have been applied. Applied: {number_of_materials}"
        # - all
        count = num_prims
        for value, expected_value in draw_choice(shape=(count,), choices=materials):
            prim.apply_physics_materials(value)
            output = prim.get_applied_physics_materials()
            _check(value, expected_value, output, count)
        # - check the number of applied materials after applying materials by all
        output = prim.get_applied_physics_materials()
        number_of_materials = sum(1 for material in output if material is not None)
        assert (
            number_of_materials == count
        ), f"{count} materials should have been applied. Applied: {number_of_materials}"
