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
from isaacsim.core.experimental.prims import Articulation, use_backend
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.storage.native import get_assets_root_path

from .utils import check_allclose, check_array, check_equal, draw_choice, draw_indices, draw_sample


def parametrize(
    devices: list[str],
    backends: list[str],
    amounts: list[str],
    max_num_prims: int = 5,
    articulation_kwargs: dict = {},
    partial_usd_path: str = "Isaac/Robots/IsaacSim/SimpleArticulation/simple_articulation.usd",
):
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
                        usd_path = f"{get_assets_root_path()}/{partial_usd_path}"
                        stage.DefinePrim(f"/World", "Xform")
                        for i in range(max_num_prims):
                            stage_utils.add_reference_to_stage(usd_path=usd_path, prim_path=f"/World/A_{i}")
                        # configure simulation manager
                        SimulationManager.set_backend("warp")
                        SimulationManager.set_physics_sim_device(device)
                        # parametrize test
                        prim = Articulation("/World/A_0" if amount == "one" else "/World/A_.*", **articulation_kwargs)
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


async def play_stop_timeline():
    omni.timeline.get_timeline_interface().play()
    await omni.kit.app.get_app().next_update_async()
    omni.timeline.get_timeline_interface().stop()
    await omni.kit.app.get_app().next_update_async()


class TestArticulation(omni.kit.test.AsyncTestCase):
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
        self.assertEqual(len(prim), num_prims, f"Invalid Articulation ({num_prims} prims) len")

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_properties_and_getters(self, prim, num_prims, device, backend):  # check backend
        # check backend
        self.check_backend(backend, prim)
        # test cases (properties)
        # - amount
        self.assertEqual(prim.num_dofs, 2, f"Invalid num_dofs")
        self.assertEqual(prim.num_joints, 2, f"Invalid num_joints")
        self.assertEqual(prim.num_links, 3, f"Invalid num_links")
        # - names
        self.assertEqual(prim.dof_names, ["RevoluteJoint", "PrismaticJoint"], f"Invalid dof_names")
        self.assertEqual(prim.joint_names, ["RevoluteJoint", "PrismaticJoint"], f"Invalid joint_names")
        self.assertEqual(prim.link_names, ["CenterPivot", "Arm", "Slider"], f"Invalid link_names")
        # - paths
        self.assertEqual(len(prim.dof_paths), len(prim), f"Invalid dof_paths")
        for i, dof_paths in enumerate(prim.dof_paths):
            for dof_path, dof_name in zip(dof_paths, prim.dof_names):
                self.assertTrue(dof_path.startswith(f"/World/A_{i}/"), f"Invalid dof_path: {dof_path}")
                self.assertTrue(dof_path.endswith(f"/{dof_name}"), f"Invalid dof_path: {dof_path}")
        self.assertEqual(len(prim.joint_paths), len(prim), f"Invalid joint_paths")
        for i, joint_paths in enumerate(prim.joint_paths):
            for joint_path, joint_name in zip(joint_paths, prim.joint_names):
                self.assertTrue(joint_path.startswith(f"/World/A_{i}/"), f"Invalid joint_path: {joint_path}")
                self.assertTrue(joint_path.endswith(f"/{joint_name}"), f"Invalid joint_path: {joint_path}")
        self.assertEqual(len(prim.link_paths), len(prim), f"Invalid link_paths")
        for i, link_paths in enumerate(prim.link_paths):
            for link_path, link_name in zip(link_paths, prim.link_names):
                self.assertTrue(link_path.startswith(f"/World/A_{i}/"), f"Invalid link_path: {link_path}")
                self.assertTrue(link_path.endswith(f"/{link_name}"), f"Invalid link_path: {link_path}")
        # - types
        self.assertEqual(
            prim.dof_types,
            [omni.physics.tensors.DofType.Rotation, omni.physics.tensors.DofType.Translation],
            f"Invalid dof_types",
        )
        # test cases (getters)
        self.assertEqual(prim.get_dof_indices("RevoluteJoint").numpy().tolist(), [0], f"Invalid get_dof_indices")
        self.assertEqual(
            prim.get_dof_indices(["PrismaticJoint", "RevoluteJoint"]).numpy().tolist(),
            [1, 0],
            f"Invalid get_dof_indices",
        )
        self.assertEqual(prim.get_joint_indices("RevoluteJoint").numpy().tolist(), [0], f"Invalid get_joint_indices")
        self.assertEqual(
            prim.get_joint_indices(["PrismaticJoint", "RevoluteJoint"]).numpy().tolist(),
            [1, 0],
            f"Invalid get_joint_indices",
        )
        self.assertEqual(prim.get_link_indices("CenterPivot").numpy().tolist(), [0], f"Invalid get_link_indices")
        self.assertEqual(
            prim.get_link_indices(["Arm", "Slider", "CenterPivot"]).numpy().tolist(),
            [1, 2, 0],
            f"Invalid get_link_indices",
        )
        # test cases (Physics tensor initialization requirement for USD backend)
        if backend == "usd":
            await play_stop_timeline()  # ensure the articulation tensor API is initialized
            assert prim.is_physics_tensor_entity_initialized(), "Tensor API should be initialized"
        # - properties
        self.assertEqual(
            prim.joint_types,
            [omni.physics.tensors.JointType.Revolute, omni.physics.tensors.JointType.Prismatic],
            f"Invalid joint_types",
        )
        self.assertEqual(prim.num_shapes, 3, f"Invalid num_shapes")
        self.assertEqual(prim.num_fixed_tendons, 0, f"Invalid num_fixed_tendons")
        # - getters

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

    @parametrize(devices=["cpu", "cuda"], backends=["tensor"], amounts=["one", "many"])
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

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_enabled_self_collisions(self, prim, num_prims, device, backend):
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
                    prim.set_enabled_self_collisions(enabled, indices=indices)
                    output = prim.get_enabled_self_collisions(indices=indices)
                _check(enabled, expected_enabled, output, expected_count)

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

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_stabilization_thresholds(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output, shape=(count, 1), dtype=wp.float32, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Stabilization thresholds ({type(input)})\n{input}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for thresholds, expected_thresholds in draw_sample(shape=(expected_count, 1), dtype=wp.float32):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_stabilization_thresholds(thresholds, indices=indices)
                    output = prim.get_stabilization_thresholds(indices=indices)
                _check(thresholds, expected_thresholds, output, expected_count)

    @parametrize(devices=["cpu", "cuda"], backends=["usd"], amounts=["one", "many"])
    async def test_solver_iteration_counts(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count):
            check_array(output[0], shape=(count, 1), dtype=wp.int32, device=device)
            check_array(output[1], shape=(count, 1), dtype=wp.int32, device=device)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"Position counts ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"Velocity counts ({type(input[1])})\n{input[1]}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for (position_counts, expected_position_counts), (velocity_counts, expected_velocity_counts) in zip(
                draw_sample(shape=(expected_count, 1), dtype=wp.int32, high=10),
                draw_sample(shape=(expected_count, 1), dtype=wp.int32, high=10),
            ):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_solver_iteration_counts(position_counts, velocity_counts, indices=indices)
                    output = prim.get_solver_iteration_counts(indices=indices)
                _check(
                    (position_counts, velocity_counts),
                    (expected_position_counts, expected_velocity_counts),
                    output,
                    expected_count,
                )

    @parametrize(devices=["cpu", "cuda"], backends=["tensor"], amounts=["one", "many"])
    async def test_jacobians_and_mass_matrices(self, prim, num_prims, device, backend):
        # check backend
        self.check_backend(backend, prim)
        # test cases (shapes)
        jacobian_matrix_shape = prim.jacobian_matrix_shape
        self.assertEqual(jacobian_matrix_shape, (2, 6, 2), f"Invalid Jacobian matrix shape ({jacobian_matrix_shape})")
        mass_matrix_shape = prim.mass_matrix_shape
        self.assertEqual(mass_matrix_shape, (2, 2), f"Invalid Mass matrix shape ({mass_matrix_shape})")
        # test cases (values)
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                jacobian_matrices = prim.get_jacobian_matrices(indices=indices)
                mass_matrices = prim.get_mass_matrices(indices=indices)
            check_array(jacobian_matrices, shape=(expected_count, 2, 6, 2), dtype=wp.float32, device=device)
            check_array(mass_matrices, shape=(expected_count, 2, 2), dtype=wp.float32, device=device)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_link_masses(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_links):
            check_array(output, shape=(count, num_links), dtype=wp.float32, device=device)
            check_allclose(
                expected_output, output.numpy(), msg=f"Masses ({type(input)})\n{input}", atol=1e-4, rtol=1e-3
            )

        def _check_inverse(output, inverse_output, count, num_links):
            check_array(inverse_output, shape=(count, num_links), dtype=wp.float32, device=device)
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
            print(f"  |    |-- indices: {type(indices).__name__}, count: {expected_count}")
            for link_indices, expected_link_count in draw_indices(count=prim.num_links, step=2):
                print(f"  |    |    |-- link_indices: {type(link_indices).__name__}, count: {expected_link_count}")
                for masses, expected_masses in draw_sample(
                    shape=(expected_count, expected_link_count), dtype=wp.float32
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_link_masses(masses, indices=indices, link_indices=link_indices)
                        output = prim.get_link_masses(indices=indices, link_indices=link_indices)
                        inverse_output = prim.get_link_masses(indices=indices, link_indices=link_indices, inverse=True)
                    _check(masses, expected_masses, output, expected_count, expected_link_count)
                    _check_inverse(output, inverse_output, expected_count, expected_link_count)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor"], amounts=["one", "many"])
    async def test_link_inertias(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_links):
            check_array(output, shape=(count, num_links, 9), dtype=wp.float32, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Inertias ({type(input)})\n{input}")

        def _check_inverse(output, inverse_output, count, num_links):
            check_array(inverse_output, shape=(count, num_links, 9), dtype=wp.float32, device=device)
            expected_inverse = np.linalg.inv(output.numpy().reshape((-1, num_links, 3, 3))).reshape(
                (count, num_links, 9)
            )
            check_allclose(expected_inverse, inverse_output.numpy())

        def _transform(x):  # transform to a diagonal inertia matrix
            x[:, :, [1, 2, 3, 5, 6, 7]] = 0.0
            return x

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, count: {expected_count}")
            for link_indices, expected_link_count in draw_indices(count=prim.num_links, step=2):
                print(f"  |    |    |-- link_indices: {type(link_indices).__name__}, count: {expected_link_count}")
                for inertias, expected_inertias in draw_sample(
                    shape=(expected_count, expected_link_count, 9), dtype=wp.float32, transform=_transform
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_link_inertias(inertias, indices=indices, link_indices=link_indices)
                        output = prim.get_link_inertias(indices=indices, link_indices=link_indices)
                        inverse_output = prim.get_link_inertias(
                            indices=indices, link_indices=link_indices, inverse=True
                        )
                    _check(inertias, expected_inertias, output, expected_count, expected_link_count)
                    _check_inverse(output, inverse_output, expected_count, expected_link_count)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor"], amounts=["one", "many"])
    async def test_link_coms(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_links):
            check_array(output[0], shape=(count, num_links, 3), dtype=wp.float32, device=device)
            check_array(output[1], shape=(count, num_links, 4), dtype=wp.float32, device=device)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"Positions ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"Orientations ({type(input[1])})\n{input[1]}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for link_indices, expected_link_count in draw_indices(count=prim.num_links, step=2):
                print(f"  |    |    |-- link_indices: {type(link_indices).__name__}, count: {expected_link_count}")
                for (positions, expected_positions), (orientations, expected_orientations) in zip(
                    draw_sample(shape=(expected_count, expected_link_count, 3), dtype=wp.float32),
                    draw_sample(shape=(expected_count, expected_link_count, 4), dtype=wp.float32, normalized=True),
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_link_coms(positions, orientations, indices=indices, link_indices=link_indices)
                        output = prim.get_link_coms(indices=indices, link_indices=link_indices)
                    _check(
                        (positions, orientations),
                        (expected_positions, expected_orientations),
                        output,
                        expected_count,
                        expected_link_count,
                    )

    @parametrize(devices=["cpu", "cuda"], backends=["tensor"], amounts=["one", "many"])
    async def test_dof_compensation_forces(self, prim, num_prims, device, backend):
        # check backend
        self.check_backend(backend, prim)
        # test cases (coriolis and centrifugal compensation forces)
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for dof_indices, expected_dof_count in draw_indices(count=prim.num_dofs, step=2):
                print(f"  |    |    |-- dof_indices: {type(dof_indices).__name__}, count: {expected_dof_count}")
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    forces = prim.get_dof_coriolis_and_centrifugal_compensation_forces(
                        indices=indices, dof_indices=dof_indices
                    )
                check_array(forces, shape=(expected_count, expected_dof_count), dtype=wp.float32, device=device)
        # test cases (gravity compensation forces)
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for dof_indices, expected_dof_count in draw_indices(count=prim.num_dofs, step=2):
                print(f"  |    |    |-- dof_indices: {type(dof_indices).__name__}, count: {expected_dof_count}")
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    forces = prim.get_dof_gravity_compensation_forces(indices=indices, dof_indices=dof_indices)
                check_array(forces, shape=(expected_count, expected_dof_count), dtype=wp.float32, device=device)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_link_enabled_gravities(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_links):
            check_array(output, shape=(count, num_links), dtype=wp.bool, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Enabled ({type(input)})\n{input}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for link_indices, expected_link_count in draw_indices(count=prim.num_links, step=2):
                print(f"  |    |    |-- link_indices: {type(link_indices).__name__}, count: {expected_link_count}")
                for enabled, expected_enabled in draw_sample(
                    shape=(expected_count, expected_link_count), dtype=wp.bool
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_link_enabled_gravities(enabled, indices=indices, link_indices=link_indices)
                        output = prim.get_link_enabled_gravities(indices=indices, link_indices=link_indices)
                    _check(enabled, expected_enabled, output, expected_count, expected_link_count)

    @parametrize(
        devices=["cpu", "cuda"],
        backends=["tensor", "usd"],
        amounts=["one", "many"],
        articulation_kwargs={"enable_residual_reports": True},
    )
    async def test_solver_residual_reports(self, prim, num_prims, device, backend):
        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                position_residuals, velocity_residuals = prim.get_solver_residual_reports(indices=indices)
            check_array(position_residuals, shape=(expected_count, 1), dtype=wp.float32, device=device)
            check_array(velocity_residuals, shape=(expected_count, 1), dtype=wp.float32, device=device)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_dof_armatures(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_dofs):
            check_array(output, shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Armatures ({type(input)})\n{input}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for dof_indices, expected_dof_count in draw_indices(count=prim.num_dofs, step=2):
                print(f"  |    |    |-- dof_indices: {type(dof_indices).__name__}, count: {expected_dof_count}")
                for armatures, expected_armatures in draw_sample(
                    shape=(expected_count, expected_dof_count), dtype=wp.float32
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_dof_armatures(armatures, indices=indices, dof_indices=dof_indices)
                        output = prim.get_dof_armatures(indices=indices, dof_indices=dof_indices)
                    _check(armatures, expected_armatures, output, expected_count, expected_dof_count)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_dof_max_efforts(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_dofs):
            check_array(output, shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Max efforts ({type(input)})\n{input}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for dof_indices, expected_dof_count in draw_indices(count=prim.num_dofs, step=2):
                print(f"  |    |    |-- dof_indices: {type(dof_indices).__name__}, count: {expected_dof_count}")
                for max_efforts, expected_max_efforts in draw_sample(
                    shape=(expected_count, expected_dof_count), dtype=wp.float32
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_dof_max_efforts(max_efforts, indices=indices, dof_indices=dof_indices)
                        output = prim.get_dof_max_efforts(indices=indices, dof_indices=dof_indices)
                    _check(max_efforts, expected_max_efforts, output, expected_count, expected_dof_count)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_dof_max_velocities(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_dofs):
            check_array(output, shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Max DOF velocities ({type(input)})\n{input}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for dof_indices, expected_dof_count in draw_indices(count=prim.num_dofs, step=2):
                print(f"  |    |    |-- dof_indices: {type(dof_indices).__name__}, count: {expected_dof_count}")
                for max_velocities, expected_max_velocities in draw_sample(
                    shape=(expected_count, expected_dof_count), dtype=wp.float32
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_dof_max_velocities(max_velocities, indices=indices, dof_indices=dof_indices)
                        output = prim.get_dof_max_velocities(indices=indices, dof_indices=dof_indices)
                    _check(max_velocities, expected_max_velocities, output, expected_count, expected_dof_count)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_dof_gains(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_dofs):
            check_array(output[0], shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_array(output[1], shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"Stiffnesses ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"Dampings ({type(input[1])})\n{input[1]}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for dof_indices, expected_dof_count in draw_indices(count=prim.num_dofs, step=2):
                print(f"  |    |    |-- dof_indices: {type(dof_indices).__name__}, count: {expected_dof_count}")
                for (stiffnesses, expected_stiffnesses), (dampings, expected_dampings) in zip(
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32),
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32),
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_dof_gains(stiffnesses, dampings, indices=indices, dof_indices=dof_indices)
                        output = prim.get_dof_gains(indices=indices, dof_indices=dof_indices)
                    _check(
                        (stiffnesses, dampings),
                        (expected_stiffnesses, expected_dampings),
                        output,
                        expected_count,
                        expected_dof_count,
                    )

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_dof_targets(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_dofs):
            check_array(output, shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Input ({type(input)})\n{input}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for dof_indices, expected_dof_count in draw_indices(count=prim.num_dofs, step=2):
                print(f"  |    |    |-- dof_indices: {type(dof_indices).__name__}, count: {expected_dof_count}")
                # position targets
                for positions, expected_positions in draw_sample(
                    shape=(expected_count, expected_dof_count), dtype=wp.float32
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_dof_position_targets(positions, indices=indices, dof_indices=dof_indices)
                        output = prim.get_dof_position_targets(indices=indices, dof_indices=dof_indices)
                    _check(positions, expected_positions, output, expected_count, expected_dof_count)
                # velocity targets
                for velocities, expected_velocities in draw_sample(
                    shape=(expected_count, expected_dof_count), dtype=wp.float32
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_dof_velocity_targets(velocities, indices=indices, dof_indices=dof_indices)
                        output = prim.get_dof_velocity_targets(indices=indices, dof_indices=dof_indices)
                    _check(velocities, expected_velocities, output, expected_count, expected_dof_count)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor"], amounts=["one", "many"])
    async def test_dof_states(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_dofs):
            check_array(output, shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_allclose(expected_output, output.numpy(), msg=f"Input ({type(input)})\n{input}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            # DOF-related
            for dof_indices, expected_dof_count in draw_indices(count=prim.num_dofs, step=2):
                print(f"  |    |    |-- dof_indices: {type(dof_indices).__name__}, count: {expected_dof_count}")
                # positions
                for positions, expected_positions in draw_sample(
                    shape=(expected_count, expected_dof_count), dtype=wp.float32
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_dof_positions(positions, indices=indices, dof_indices=dof_indices)
                        output = prim.get_dof_positions(indices=indices, dof_indices=dof_indices)
                    _check(positions, expected_positions, output, expected_count, expected_dof_count)
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        output = prim.get_dof_position_targets(indices=indices, dof_indices=dof_indices)
                    _check(positions, expected_positions, output, expected_count, expected_dof_count)
                # velocities
                for velocities, expected_velocities in draw_sample(
                    shape=(expected_count, expected_dof_count), dtype=wp.float32
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_dof_velocities(velocities, indices=indices, dof_indices=dof_indices)
                        output = prim.get_dof_velocities(indices=indices, dof_indices=dof_indices)
                    _check(velocities, expected_velocities, output, expected_count, expected_dof_count)
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        output = prim.get_dof_velocity_targets(indices=indices, dof_indices=dof_indices)
                    _check(velocities, expected_velocities, output, expected_count, expected_dof_count)
                # efforts
                for efforts, expected_efforts in draw_sample(
                    shape=(expected_count, expected_dof_count), dtype=wp.float32
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_dof_efforts(efforts, indices=indices, dof_indices=dof_indices)
                        output = prim.get_dof_efforts(indices=indices, dof_indices=dof_indices)
                    _check(efforts, expected_efforts, output, expected_count, expected_dof_count)
                # projected joint forces
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    output = prim.get_dof_projected_joint_forces(indices=indices, dof_indices=dof_indices)
                check_array(output, shape=(expected_count, expected_dof_count), dtype=wp.float32, device=device)
            # link-related
            for link_indices, expected_link_count in draw_indices(count=prim.num_links, step=2):
                print(f"  |    |    |-- link_indices: {type(link_indices).__name__}, count: {expected_link_count}")
                # measured forces
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    output = prim.get_link_incoming_joint_force(indices=indices, link_indices=link_indices)
                check_array(output[0], shape=(expected_count, expected_link_count, 3), dtype=wp.float32, device=device)
                check_array(output[1], shape=(expected_count, expected_link_count, 3), dtype=wp.float32, device=device)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_dof_drive_types(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_dofs):
            assert len(expected_output) == len(
                output
            ), f"Unexpected drive types length: expected {len(expected_output)}, got {len(output)}"
            for expected, value in zip(expected_output, output):
                assert expected == value, f"Unexpected drive type: expected {expected}, got {value}"

        types = ["acceleration", "force"]
        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for dof_indices, expected_dof_count in draw_indices(count=prim.num_dofs, step=2):
                print(f"  |    |    |-- dof_indices: {type(dof_indices).__name__}, count: {expected_dof_count}")
                for types, expected_types in draw_choice(shape=(expected_count, expected_dof_count), choices=types):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_dof_drive_types(types, indices=indices, dof_indices=dof_indices)
                        output = prim.get_dof_drive_types(indices=indices, dof_indices=dof_indices)
                    _check(types, expected_types, output, expected_count, expected_dof_count)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_dof_limits(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_dofs):
            check_array(output[0], shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_array(output[1], shape=(count, num_dofs), dtype=wp.float32, device=device)
            if backend == "usd":
                check_allclose(expected_output[0], output[0].numpy(), msg=f"Lower ({type(input[0])})\n{input[0]}")
                check_allclose(expected_output[1], output[1].numpy(), msg=f"Upper ({type(input[1])})\n{input[1]}")
                return
            with self.assertRaises(AssertionError, msg="This fails if the issue has been fixed. Update test!"):
                check_allclose(expected_output[0], output[0].numpy(), msg=f"Lower ({type(input[0])})\n{input[0]}")
                check_allclose(expected_output[1], output[1].numpy(), msg=f"Upper ({type(input[1])})\n{input[1]}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for dof_indices, expected_dof_count in draw_indices(count=prim.num_dofs, step=2):
                print(f"  |    |    |-- dof_indices: {type(dof_indices).__name__}, count: {expected_dof_count}")
                for (lower, expected_lower), (upper, expected_upper) in zip(
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32, high=0.49),
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32, low=0.51),
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_dof_limits(lower, upper, indices=indices, dof_indices=dof_indices)
                        output = prim.get_dof_limits(indices=indices, dof_indices=dof_indices)
                    _check((lower, upper), (expected_lower, expected_upper), output, expected_count, expected_dof_count)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_dof_friction_properties(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_dofs):
            check_array(output[0], shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_array(output[1], shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_array(output[2], shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"v0 ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"v1 ({type(input[1])})\n{input[1]}")
            check_allclose(expected_output[2], output[2].numpy(), msg=f"v2 ({type(input[2])})\n{input[2]}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for dof_indices, expected_dof_count in draw_indices(count=prim.num_dofs, step=2):
                print(f"  |    |    |-- dof_indices: {type(dof_indices).__name__}, count: {expected_dof_count}")
                for (v0, expected_v0), (v1, expected_v1), (v2, expected_v2) in zip(
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32, low=0.51),
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32, high=0.49),
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32),
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_dof_friction_properties(v0, v1, v2, indices=indices, dof_indices=dof_indices)
                        output = prim.get_dof_friction_properties(indices=indices, dof_indices=dof_indices)
                    _check(
                        (v0, v1, v2),
                        (expected_v0, expected_v1, expected_v2),
                        output,
                        expected_count,
                        expected_dof_count,
                    )

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_dof_drive_model_properties(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_dofs):
            check_array(output[0], shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_array(output[1], shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_array(output[2], shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"v0 ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"v1 ({type(input[1])})\n{input[1]}")
            check_allclose(expected_output[2], output[2].numpy(), msg=f"v2 ({type(input[2])})\n{input[2]}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for dof_indices, expected_dof_count in draw_indices(count=prim.num_dofs, step=2):
                print(f"  |    |    |-- dof_indices: {type(dof_indices).__name__}, count: {expected_dof_count}")
                for (v0, expected_v0), (v1, expected_v1), (v2, expected_v2) in zip(
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32),
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32),
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32),
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_dof_drive_model_properties(v0, v1, v2, indices=indices, dof_indices=dof_indices)
                        output = prim.get_dof_drive_model_properties(indices=indices, dof_indices=dof_indices)
                    _check(
                        (v0, v1, v2),
                        (expected_v0, expected_v1, expected_v2),
                        output,
                        expected_count,
                        expected_dof_count,
                    )

    @parametrize(
        devices=["cpu", "cuda"],
        backends=["tensor"],
        amounts=["many"],
        articulation_kwargs={"positions": [[x, 0, 0] for x in range(5)], "reset_xform_op_properties": True},
        partial_usd_path="Isaac/Robots/ShadowRobot/ShadowHand/shadow_hand.usd",
    )
    async def test_fixed_tendons_properties(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_tendons):
            check_array(output, shape=(count, num_tendons), dtype=wp.float32, device=device)
            if device == "cuda":
                with self.assertRaises(AssertionError, msg="This fails if the issue has been fixed. Update test!"):
                    check_allclose(expected_output, output.numpy(), msg=f"Input ({type(input)})\n{input}")
            else:
                check_allclose(expected_output, output.numpy(), msg=f"Input ({type(input)})\n{input}")

        assert prim.num_fixed_tendons == 4, f"Expected 4 fixed tendons, got {prim.num_fixed_tendons}"
        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for tendon_indices, expected_tendon_count in draw_indices(count=prim.num_fixed_tendons, step=2):
                print(
                    f"  |    |    |-- tendon_indices: {type(tendon_indices).__name__}, count: {expected_tendon_count}"
                )
                for (
                    (stiffnesses, expected_stiffnesses),
                    (dampings, expected_dampings),
                    (limit_stiffnesses, expected_limit_stiffnesses),
                    (lower_limits, expected_lower_limits),
                    (upper_limits, expected_upper_limits),
                    (rest_lengths, expected_rest_lengths),
                    (offsets, expected_offsets),
                ) in zip(
                    draw_sample(shape=(expected_count, expected_tendon_count), dtype=wp.float32),
                    draw_sample(shape=(expected_count, expected_tendon_count), dtype=wp.float32),
                    draw_sample(shape=(expected_count, expected_tendon_count), dtype=wp.float32),
                    draw_sample(shape=(expected_count, expected_tendon_count), dtype=wp.float32, high=0.49),
                    draw_sample(shape=(expected_count, expected_tendon_count), dtype=wp.float32, low=0.51),
                    draw_sample(shape=(expected_count, expected_tendon_count), dtype=wp.float32),
                    draw_sample(shape=(expected_count, expected_tendon_count), dtype=wp.float32),
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_fixed_tendon_properties(
                            stiffnesses=stiffnesses,
                            dampings=dampings,
                            limit_stiffnesses=limit_stiffnesses,
                            lower_limits=lower_limits,
                            upper_limits=upper_limits,
                            rest_lengths=rest_lengths,
                            offsets=offsets,
                            indices=indices,
                            tendon_indices=tendon_indices,
                        )
                        output_stiffnesses = prim.get_fixed_tendon_stiffnesses(
                            indices=indices, tendon_indices=tendon_indices
                        )
                        output_dampings = prim.get_fixed_tendon_dampings(indices=indices, tendon_indices=tendon_indices)
                        output_limit_stiffnesses = prim.get_fixed_tendon_limit_stiffnesses(
                            indices=indices, tendon_indices=tendon_indices
                        )
                        output_lower_limits, output_upper_limits = prim.get_fixed_tendon_limits(
                            indices=indices, tendon_indices=tendon_indices
                        )
                        output_rest_lengths = prim.get_fixed_tendon_rest_lengths(
                            indices=indices, tendon_indices=tendon_indices
                        )
                        output_offsets = prim.get_fixed_tendon_offsets(indices=indices, tendon_indices=tendon_indices)

                    _check(stiffnesses, expected_stiffnesses, output_stiffnesses, expected_count, expected_tendon_count)
                    _check(dampings, expected_dampings, output_dampings, expected_count, expected_tendon_count)
                    _check(
                        limit_stiffnesses,
                        expected_limit_stiffnesses,
                        output_limit_stiffnesses,
                        expected_count,
                        expected_tendon_count,
                    )
                    _check(
                        lower_limits, expected_lower_limits, output_lower_limits, expected_count, expected_tendon_count
                    )
                    _check(
                        upper_limits, expected_upper_limits, output_upper_limits, expected_count, expected_tendon_count
                    )
                    _check(
                        rest_lengths, expected_rest_lengths, output_rest_lengths, expected_count, expected_tendon_count
                    )
                    _check(offsets, expected_offsets, output_offsets, expected_count, expected_tendon_count)

    @parametrize(devices=["cpu", "cuda"], backends=["tensor", "usd"], amounts=["one", "many"])
    async def test_default_state(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_dofs):
            check_array(output[0], shape=(count, 3), dtype=wp.float32, device=device)
            check_array(output[1], shape=(count, 4), dtype=wp.float32, device=device)
            check_array(output[2], shape=(count, 3), dtype=wp.float32, device=device)
            check_array(output[3], shape=(count, 3), dtype=wp.float32, device=device)
            check_array(output[4], shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_array(output[5], shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_array(output[6], shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"Positions ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"Orientations ({type(input[1])})\n{input[1]}")
            check_allclose(
                expected_output[2], output[2].numpy(), msg=f"Linear Velocities ({type(input[2])})\n{input[2]}"
            )
            check_allclose(
                expected_output[3], output[3].numpy(), msg=f"Angular Velocities ({type(input[3])})\n{input[3]}"
            )
            check_allclose(expected_output[4], output[4].numpy(), msg=f"Dof Positions ({type(input[4])})\n{input[4]}")
            check_allclose(expected_output[5], output[5].numpy(), msg=f"Dof Velocities ({type(input[5])})\n{input[5]}")
            check_allclose(expected_output[6], output[6].numpy(), msg=f"Dof Efforts ({type(input[6])})\n{input[6]}")

        # check backend
        if backend == "usd":
            prim.reset_xform_op_properties()
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for dof_indices, expected_dof_count in draw_indices(count=prim.num_dofs, step=2):
                print(f"  |    |    |-- dof_indices: {type(dof_indices).__name__}, count: {expected_dof_count}")
                for (
                    (positions, expected_positions),
                    (orientations, expected_orientations),
                    (linear_velocities, expected_linear_velocities),
                    (angular_velocities, expected_angular_velocities),
                    (dof_positions, expected_dof_positions),
                    (dof_velocities, expected_dof_velocities),
                    (dof_efforts, expected_dof_efforts),
                ) in zip(
                    draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                    draw_sample(shape=(expected_count, 4), dtype=wp.float32, normalized=True),
                    draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                    draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32),
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32),
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32),
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_default_state(
                            positions,
                            orientations,
                            linear_velocities,
                            angular_velocities,
                            dof_positions,
                            dof_velocities,
                            dof_efforts,
                            indices=indices,
                            dof_indices=dof_indices,
                        )
                        output = prim.get_default_state(indices=indices, dof_indices=dof_indices)
                        if backend == "tensor":
                            prim.reset_to_default_state()
                    _check(
                        (
                            positions,
                            orientations,
                            linear_velocities,
                            angular_velocities,
                            dof_positions,
                            dof_velocities,
                            dof_efforts,
                        ),
                        (
                            expected_positions,
                            expected_orientations,
                            expected_linear_velocities,
                            expected_angular_velocities,
                            expected_dof_positions,
                            expected_dof_velocities,
                            expected_dof_efforts,
                        ),
                        output,
                        expected_count,
                        expected_dof_count,
                    )

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
    async def test_switch_control_mode(self, prim, num_prims, device, backend):
        def _check(input, expected_output, output, count, num_dofs):
            check_array(output[0], shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_array(output[1], shape=(count, num_dofs), dtype=wp.float32, device=device)
            check_allclose(expected_output[0], output[0].numpy(), msg=f"Stiffnesses ({type(input[0])})\n{input[0]}")
            check_allclose(expected_output[1], output[1].numpy(), msg=f"Dampings ({type(input[1])})\n{input[1]}")

        # check backend
        self.check_backend(backend, prim)
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for dof_indices, expected_dof_count in draw_indices(count=prim.num_dofs, step=2):
                print(f"  |    |    |-- dof_indices: {type(dof_indices).__name__}, count: {expected_dof_count}")
                for (stiffnesses, expected_stiffnesses), (dampings, expected_dampings) in zip(
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32),
                    draw_sample(shape=(expected_count, expected_dof_count), dtype=wp.float32),
                ):
                    with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                        prim.set_dof_gains(stiffnesses, dampings, indices=indices, dof_indices=dof_indices)
                        default_stiffnesses, default_dampings = prim.get_dof_gains()
                    for mode in ["position", "velocity", "effort"]:
                        with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                            prim.switch_dof_control_mode(mode, indices=indices, dof_indices=dof_indices)
                            output = prim.get_dof_gains(indices=indices, dof_indices=dof_indices)
                        if mode == "position":
                            expected_output = (expected_stiffnesses, expected_dampings)
                        elif mode == "velocity":
                            expected_output = (np.zeros_like(expected_stiffnesses), expected_dampings)
                        elif mode == "effort":
                            expected_output = (
                                np.zeros_like(expected_stiffnesses),
                                np.zeros_like(expected_dampings),
                            )
                        _check(
                            (stiffnesses, dampings),
                            expected_output,
                            output,
                            expected_count,
                            expected_dof_count,
                        )
                        # check that the default (internal) gains are not updated
                        _check(
                            (default_stiffnesses.numpy(), default_dampings.numpy()),
                            (default_stiffnesses.numpy(), default_dampings.numpy()),
                            (prim._default_dof_stiffnesses, prim._default_dof_dampings),
                            num_prims,
                            prim.num_dofs,
                        )
