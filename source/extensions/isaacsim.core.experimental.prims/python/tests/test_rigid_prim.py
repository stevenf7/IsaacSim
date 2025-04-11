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
from isaacsim.core.experimental.prims import RigidPrim, use_backend
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
                        prim = RigidPrim("/World/A_0" if amount == "one" else "/World/A_.*", masses=[1.0])
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


class TestRigidPrim(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        super().tearDown()

    # --------------------------------------------------------------------

    def check_backend(self, backend, prim):
        if backend == "tensor":
            self.assertTrue(prim.is_physics_tensor_entity_valid(), f"Tensor API should be enabled ({backend})")
        elif backend in ["usd", "usdrt", "fabric"]:
            self.assertFalse(prim.is_physics_tensor_entity_valid(), f"Tensor API should be disabled ({backend})")
        else:
            raise ValueError(f"Invalid backend: {backend}")

    # --------------------------------------------------------------------

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_len(self, prim, num_prims, device, backend):
        self.assertEqual(len(prim), num_prims, f"Invalid RigidPrim ({num_prims} prims) len")

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd", "usdrt", "fabric"], amounts=["one", "many"])
    async def test_world_poses(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output[0], shape=(count, 3), dtype=wp.float32, device=device)
            check_array(output[1], shape=(count, 4), dtype=wp.float32, device=device)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"Positions ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"Orientations ({type(input[1])})\n{input[1]}")

        # check backend and define USD usage
        self.check_backend(backend, prim)
        if backend in ["usdrt", "fabric"]:
            await omni.kit.app.get_app().next_update_async()
        elif backend == "usd":
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

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd", "usdrt", "fabric"], amounts=["one", "many"])
    async def test_local_poses(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output[0], shape=(count, 3), dtype=wp.float32, device=device)
            check_array(output[1], shape=(count, 4), dtype=wp.float32, device=device)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"Translations ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"Orientations ({type(input[1])})\n{input[1]}")

        # check backend and define USD usage
        self.check_backend(backend, prim)
        if backend in ["usdrt", "fabric"]:
            await omni.kit.app.get_app().next_update_async()
        elif backend == "usd":
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

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_velocities(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output[0], shape=(count, 3), dtype=wp.float32, device=device)
            check_array(output[1], shape=(count, 3), dtype=wp.float32, device=device)
            check_allclose(
                expected_output[0], output[0].numpy(), msg=f"Linear Velocities ({type(input[0])})\n{input[0]}"
            )
            check_allclose(
                expected_output[1], output[1].numpy(), msg=f"Angular Velocities ({type(input[1])})\n{input[1]}"
            )

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for (linear_velocities, expected_linear_velocities), (
                angular_velocities,
                expected_angular_velocities,
            ) in zip(
                draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                draw_sample(shape=(expected_count, 3), dtype=wp.float32),
            ):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_velocities(linear_velocities, angular_velocities, indices=indices)
                    output = prim.get_velocities(indices=indices)
                _check(
                    (linear_velocities, angular_velocities),
                    (expected_linear_velocities, expected_angular_velocities),
                    output,
                    expected_count,
                )

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_masses(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output, shape=(count, 1), dtype=wp.float32, device=device)
            check_allclose(
                expected_output, output.numpy(), msg=f"Masses ({type(input)})\n{input}", atol=1e-4, rtol=1e-3
            )

        def _check_inverse(output, inverse_output, count):
            check_array(inverse_output, shape=(count, 1), dtype=wp.float32, device=device)
            expected_inverse = 1.0 / (output.numpy() + 1e-8)
            check_allclose(
                expected_inverse,
                inverse_output.numpy(),
                msg=f"Masses (inverse) ({type(input)})\n{input}",
                atol=1e-4,
                rtol=1e-3,
            )

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for masses, expected_masses in draw_sample(shape=(expected_count, 1), dtype=wp.float32):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_masses(masses, indices=indices)
                    output = prim.get_masses(indices=indices)
                    inverse_output = prim.get_masses(indices=indices, inverse=True)
                _check(masses, expected_masses, output, expected_count)
                _check_inverse(output, inverse_output, expected_count)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_enabled_rigid_bodies(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output, shape=(count, 1), dtype=wp.bool, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Enabled ({type(input)})\n{input}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for enabled, expected_enabled in draw_sample(shape=(expected_count, 1), dtype=wp.bool):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_enabled_rigid_bodies(enabled, indices=indices)
                    output = prim.get_enabled_rigid_bodies(indices=indices)
                _check(enabled, expected_enabled, output, expected_count)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_enabled_gravities(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output, shape=(count, 1), dtype=wp.bool, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Enabled ({type(input)})\n{input}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for enabled, expected_enabled in draw_sample(shape=(expected_count, 1), dtype=wp.bool):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_enabled_gravities(enabled, indices=indices)
                    output = prim.get_enabled_gravities(indices=indices)
                _check(enabled, expected_enabled, output, expected_count)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor"], amounts=["one", "many"])
    async def test_coms(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output[0], shape=(count, 3), dtype=wp.float32, device=device)
            check_array(output[1], shape=(count, 4), dtype=wp.float32, device=device)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"Positions ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"Orientations ({type(input[1])})\n{input[1]}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for (positions, expected_positions), (orientations, expected_orientations) in zip(
                draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                draw_sample(shape=(expected_count, 4), dtype=wp.float32, normalized=True),
            ):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_coms(positions, orientations, indices=indices)
                    output = prim.get_coms(indices=indices)
                _check((positions, orientations), (expected_positions, expected_orientations), output, expected_count)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor"], amounts=["one", "many"])
    async def test_inertias(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output, shape=(count, 9), dtype=wp.float32, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Inertias ({type(input)})\n{input}")

        def _check_inverse(output, inverse_output, count):
            check_array(inverse_output, shape=(count, 9), dtype=wp.float32, device=device)
            expected_inverse = np.linalg.inv(output.numpy().reshape((-1, 3, 3))).reshape((count, 9))
            check_allclose(expected_inverse, inverse_output.numpy())

        def _transform(x):  # transform to a diagonal inertia matrix
            x[:, [1, 2, 3, 5, 6, 7]] = 0.0
            return x

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for inertias, expected_inertias in draw_sample(
                shape=(expected_count, 9), dtype=wp.float32, transform=_transform
            ):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_inertias(inertias, indices=indices)
                    output = prim.get_inertias(indices=indices)
                    inverse_output = prim.get_inertias(indices=indices, inverse=True)
                _check(inertias, expected_inertias, output, expected_count)
                _check_inverse(output, inverse_output, expected_count)

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_densities(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output, shape=(count, 1), dtype=wp.float32, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Densities ({type(input)})\n{input}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for densities, expected_densities in draw_sample(shape=(expected_count, 1), dtype=wp.float32):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_densities(densities, indices=indices)
                    output = prim.get_densities(indices=indices)
                _check(densities, expected_densities, output, expected_count)

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_sleep_thresholds(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output, shape=(count, 1), dtype=wp.float32, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Sleep thresholds ({type(input)})\n{input}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for thresholds, expected_thresholds in draw_sample(shape=(expected_count, 1), dtype=wp.float32):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_sleep_thresholds(thresholds, indices=indices)
                    output = prim.get_sleep_thresholds(indices=indices)
                _check(thresholds, expected_thresholds, output, expected_count)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_default_state(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output[0], shape=(count, 3), dtype=wp.float32, device=device)
            check_array(output[1], shape=(count, 4), dtype=wp.float32, device=device)
            check_array(output[2], shape=(count, 3), dtype=wp.float32, device=device)
            check_array(output[3], shape=(count, 3), dtype=wp.float32, device=device)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"Positions ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"Orientations ({type(input[1])})\n{input[1]}")
            check_allclose(
                expected_output[2], output[2].numpy(), msg=f"Linear Velocities ({type(input[2])})\n{input[2]}"
            )
            check_allclose(
                expected_output[3], output[3].numpy(), msg=f"Angular Velocities ({type(input[3])})\n{input[3]}"
            )

        # check backend
        self.check_backend(backend, prim)
        if backend == "usd":
            prim.reset_xform_op_properties()
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for (
                (positions, expected_positions),
                (orientations, expected_orientations),
                (linear_velocities, expected_linear_velocities),
                (angular_velocities, expected_angular_velocities),
            ) in zip(
                draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                draw_sample(shape=(expected_count, 4), dtype=wp.float32, normalized=True),
                draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                draw_sample(shape=(expected_count, 3), dtype=wp.float32),
            ):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_default_state(
                        positions, orientations, linear_velocities, angular_velocities, indices=indices
                    )
                    output = prim.get_default_state(indices=indices)
                    prim.reset_to_default_state()
                _check(
                    (positions, orientations, linear_velocities, angular_velocities),
                    (
                        expected_positions,
                        expected_orientations,
                        expected_linear_velocities,
                        expected_angular_velocities,
                    ),
                    output,
                    expected_count,
                )

    @parametrize(devices=["cpu", "cuda"], backends=["tensor"], amounts=["one", "many"])
    async def test_apply_forces(self, prim, num_prims, device, backend):
        # check backend
        self.check_backend(backend, prim)

        # test cases (forces)
        for local_frame in [True, False]:
            # - all
            for indices, expected_count in draw_indices(count=num_prims, step=2):
                print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
                for forces, expected_forces in draw_sample(shape=(expected_count, 3), dtype=wp.float32):
                    prim.apply_forces(forces, indices=indices, local_frame=local_frame)

        # test cases (forces and torques at positions)
        for local_frame in [True, False]:
            # - all
            for indices, expected_count in draw_indices(count=num_prims, step=2):
                print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
                for (forces, expected_forces), (torques, expected_torques), (positions, expected_positions) in zip(
                    draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                    draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                    draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.apply_forces_and_torques_at_pos(
                            forces, torques, positions=positions, indices=indices, local_frame=local_frame
                        )
