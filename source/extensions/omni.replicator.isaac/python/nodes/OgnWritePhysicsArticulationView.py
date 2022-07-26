# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import torch
import numpy as np
import carb

import omni.graph.core as og

from omni.replicator.isaac import physics_view as physics
from omni.replicator.isaac import ARTICULATION_ATTRIBUTES
from omni.isaac.core.utils.torch.rotations import euler_angles_to_quats as euler_angles_to_quats_torch
from omni.isaac.core.utils.numpy.rotations import euler_angles_to_quats as euler_angles_to_quats_numpy


OPERATION_TYPES = ["direct", "additive", "scaling"]


def apply_randomization_operation(view_name, operation, attribute_name, samples, indices):
    if operation == "additive":
        return physics._articulation_views_initial_values[view_name][attribute_name][indices] + samples
    elif operation == "scaling":
        return physics._articulation_views_initial_values[view_name][attribute_name][indices] * samples
    else:
        return samples


def apply_randomization_operation_full_tensor(view_name, operation, attribute_name, samples, indices):
    initial_values = physics._articulation_views_initial_values[view_name][attribute_name].clone()
    if operation == "additive":
        initial_values[indices] += samples
    elif operation == "scaling":
        initial_values[indices] *= samples
    else:
        initial_values[indices] = samples
    return initial_values


class OgnWritePhysicsArticulationView:
    @staticmethod
    def compute(db) -> bool:
        view_name = db.inputs.prims
        attribute_name = db.inputs.attribute
        operation = db.inputs.operation
        values = db.inputs.values

        if db.inputs.indices is None or len(db.inputs.indices) == 0:
            db.outputs.execOut = og.ExecutionAttributeState.DISABLED
            return False
        indices = np.array(db.inputs.indices)

        try:
            view = physics._articulation_views.get(view_name)
            if view is None:
                raise ValueError(f"Expected a registered articulation_view, but instead received {view_name}")
            if attribute_name not in ARTICULATION_ATTRIBUTES:
                raise ValueError(
                    f"Expected an attribute in {ARTICULATION_ATTRIBUTES}, but instead received {attribute_name}"
                )
            if operation not in OPERATION_TYPES:
                raise ValueError(f"Expected an operation type in {OPERATION_TYPES}, but instead received {operation}")

            samples = np.array(values).reshape(len(indices), -1)

            device = view._device
            if attribute_name in [
                "joint_friction",
                "lower_dof_limits",
                "upper_dof_limits",
                "joint_armatures",
                "joint_max_velocities",
                "body_masses",
                "body_inertias",
            ]:
                device = "cpu"
        except Exception as error:
            db.log_error(f"WritePhysics Error: {error}")
            db.outputs.execOut = og.ExecutionAttributeState.DISABLED
            return False

        if view._backend == "torch":
            samples = torch.from_numpy(samples).float().to(device)
            indices = torch.from_numpy(indices).long().to(device)

        if attribute_name == "stiffness":
            stiffnesses = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
            view.set_gains(kps=stiffnesses, indices=indices)
        elif attribute_name == "damping":
            dampings = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
            view.set_gains(kds=dampings, indices=indices)
        elif attribute_name == "joint_friction":
            frictions = apply_randomization_operation_full_tensor(
                view_name, operation, attribute_name, samples, indices
            )
            view._physics_view.set_dof_friction_coefficients(frictions, indices)
        elif attribute_name == "position":
            positions = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
            view.set_world_poses(positions=positions, indices=indices)
        elif attribute_name == "orientation":
            rpys = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
            if view._backend == "torch":
                orientations = euler_angles_to_quats_torch(euler_angles=rpys, degrees=False, device=device).float()
            elif view._backend == "numpy":
                orientations = euler_angles_to_quats_numpy(euler_angles=rpys, degrees=False)
            view.set_world_poses(orientations=orientations, indices=indices)
        elif attribute_name == "linear_velocity":
            linear_velocities = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
            view.set_linear_velocities(linear_velocities, indices)
        elif attribute_name == "angular_velocity":
            angular_velocities = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
            view.set_angular_velocities(angular_velocities, indices)
        elif attribute_name == "velocity":
            velocities = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
            view.set_velocities(velocities, indices)
        elif attribute_name == "joint_positions":
            joint_positions = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
            view.set_joint_positions(positions=joint_positions, indices=indices)
        elif attribute_name == "joint_velocities":
            joint_velocities = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
            view.set_joint_velocities(velocities=joint_velocities, indices=indices)
        elif attribute_name == "lower_dof_limits":
            upper_dof_limits = view.get_dof_limits()[..., 1]
            lower_dof_limits = apply_randomization_operation_full_tensor(
                view_name, operation, attribute_name, samples, indices
            )
            dof_limits = torch.stack((lower_dof_limits, upper_dof_limits), dim=-1)
            view._physics_view.set_dof_limits(dof_limits, indices)
        elif attribute_name == "upper_dof_limits":
            lower_dof_limits = view.get_dof_limits()[..., 0]
            upper_dof_limits = apply_randomization_operation_full_tensor(
                view_name, operation, attribute_name, samples, indices
            )
            dof_limits = torch.stack((lower_dof_limits, upper_dof_limits), dim=-1)
            view._physics_view.set_dof_limits(dof_limits, indices)
        elif attribute_name == "max_efforts":
            max_efforts = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
            view.set_max_efforts(values=max_efforts, indices=indices)
        elif attribute_name == "joint_armatures":
            joint_armatures = apply_randomization_operation_full_tensor(
                view_name, operation, attribute_name, samples, indices
            )
            view._physics_view.set_dof_armatures(joint_armatures, indices)
        elif attribute_name == "joint_max_velocities":
            joint_max_velocities = apply_randomization_operation_full_tensor(
                view_name, operation, attribute_name, samples, indices
            )
            view._physics_view.set_dof_max_velocities(joint_max_velocities, indices)
        elif attribute_name == "joint_efforts":
            view.set_joint_efforts(efforts=samples, indices=indices)
        elif attribute_name == "body_masses":
            body_masses = apply_randomization_operation_full_tensor(
                view_name, operation, attribute_name, samples, indices
            )
            view._physics_view.set_masses(body_masses, indices)
        elif attribute_name == "body_inertias":
            diagonal_inertias = apply_randomization_operation_full_tensor(
                view_name, operation, attribute_name, samples, indices
            )
            inertia_matrices = view._backend_utils.create_zeros_tensor(
                shape=[view.count, view._physics_view.max_links, 9], dtype="float32", device=device
            )
            inertia_matrices[:, :, [0, 4, 8]] = diagonal_inertias.reshape(view.count, view._physics_view.max_links, 3)
            view._physics_view.set_inertias(inertia_matrices, indices)
        elif attribute_name == "tendon_stiffnesses":
            if view._device == "cpu":
                current_stiffnesses = view._physics_view.get_fixed_tendon_stiffnesses()
                current_dampings = view._physics_view.get_fixed_tendon_dampings()
                current_limit_stiffnesses = view._physics_view.get_fixed_tendon_limit_stiffnesses()
                current_limits = view._physics_view.get_fixed_tendon_limits().reshape(
                    view.count, view._physics_view.max_fixed_tendons, 2
                )
                current_rest_lengths = view._physics_view.get_fixed_tendon_rest_lengths()
                current_offsets = view._physics_view.get_fixed_tendon_offsets()

                tendon_stiffnesses = apply_randomization_operation(
                    view_name, operation, attribute_name, samples, indices
                )
                current_stiffnesses[indices] = view._backend_utils.move_data(tendon_stiffnesses, device=device)

                view._physics_view.set_fixed_tendon_properties(
                    current_stiffnesses,
                    current_dampings,
                    current_limit_stiffnesses,
                    current_limits,
                    current_rest_lengths,
                    current_offsets,
                    indices,
                )
            else:
                carb.log_warn("Articulation fixed tendon stiffnesses randomization cannot be applied in GPU pipeline.")
        elif attribute_name == "tendon_dampings":
            if view._device == "cpu":
                current_stiffnesses = view._physics_view.get_fixed_tendon_stiffnesses()
                current_dampings = view._physics_view.get_fixed_tendon_dampings()
                current_limit_stiffnesses = view._physics_view.get_fixed_tendon_limit_stiffnesses()
                current_limits = view._physics_view.get_fixed_tendon_limits().reshape(
                    view.count, view._physics_view.max_fixed_tendons, 2
                )
                current_rest_lengths = view._physics_view.get_fixed_tendon_rest_lengths()
                current_offsets = view._physics_view.get_fixed_tendon_offsets()

                tendon_dampings = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
                current_dampings[indices] = view._backend_utils.move_data(tendon_dampings, device=device)

                view._physics_view.set_fixed_tendon_properties(
                    current_stiffnesses,
                    current_dampings,
                    current_limit_stiffnesses,
                    current_limits,
                    current_rest_lengths,
                    current_offsets,
                    indices,
                )
            else:
                carb.log_warn("Articulation fixed tendon dampings randomization cannot be applied in GPU pipeline.")
        elif attribute_name == "tendon_limit_stiffnesses":
            if view._device == "cpu":
                current_stiffnesses = view._physics_view.get_fixed_tendon_stiffnesses()
                current_dampings = view._physics_view.get_fixed_tendon_dampings()
                current_limit_stiffnesses = view._physics_view.get_fixed_tendon_limit_stiffnesses()
                current_limits = view._physics_view.get_fixed_tendon_limits().reshape(
                    view.count, view._physics_view.max_fixed_tendons, 2
                )
                current_rest_lengths = view._physics_view.get_fixed_tendon_rest_lengths()
                current_offsets = view._physics_view.get_fixed_tendon_offsets()

                tendon_limit_stiffnesses = apply_randomization_operation(
                    view_name, operation, attribute_name, samples, indices
                )
                current_limit_stiffnesses[indices] = view._backend_utils.move_data(
                    tendon_limit_stiffnesses, device=device
                )

                view._physics_view.set_fixed_tendon_properties(
                    current_stiffnesses,
                    current_dampings,
                    current_limit_stiffnesses,
                    current_limits,
                    current_rest_lengths,
                    current_offsets,
                    indices,
                )
            else:
                carb.log_warn(
                    "Articulation fixed tendon limit stiffnesses randomization cannot be applied in GPU pipeline."
                )
        elif attribute_name == "tendon_lower_limits":
            if view._device == "cpu":
                current_stiffnesses = view._physics_view.get_fixed_tendon_stiffnesses()
                current_dampings = view._physics_view.get_fixed_tendon_dampings()
                current_limit_stiffnesses = view._physics_view.get_fixed_tendon_limit_stiffnesses()
                current_limits = view._physics_view.get_fixed_tendon_limits().reshape(
                    view.count, view._physics_view.max_fixed_tendons, 2
                )
                current_rest_lengths = view._physics_view.get_fixed_tendon_rest_lengths()
                current_offsets = view._physics_view.get_fixed_tendon_offsets()

                tendon_lower_limits = apply_randomization_operation(
                    view_name, operation, attribute_name, samples, indices
                )
                current_limits[indices, :, 0] = view._backend_utils.move_data(tendon_lower_limits, device=device)

                view._physics_view.set_fixed_tendon_properties(
                    current_stiffnesses,
                    current_dampings,
                    current_limit_stiffnesses,
                    current_limits,
                    current_rest_lengths,
                    current_offsets,
                    indices,
                )
            else:
                carb.log_warn("Articulation fixed tendon lower limits randomization cannot be applied in GPU pipeline.")
        elif attribute_name == "tendon_upper_limits":
            if view._device == "cpu":
                current_stiffnesses = view._physics_view.get_fixed_tendon_stiffnesses()
                current_dampings = view._physics_view.get_fixed_tendon_dampings()
                current_limit_stiffnesses = view._physics_view.get_fixed_tendon_limit_stiffnesses()
                current_limits = view._physics_view.get_fixed_tendon_limits().reshape(
                    view.count, view._physics_view.max_fixed_tendons, 2
                )
                current_rest_lengths = view._physics_view.get_fixed_tendon_rest_lengths()
                current_offsets = view._physics_view.get_fixed_tendon_offsets()

                tendon_upper_limits = apply_randomization_operation(
                    view_name, operation, attribute_name, samples, indices
                )
                current_limits[indices, :, 1] = view._backend_utils.move_data(tendon_upper_limits, device=device)

                view._physics_view.set_fixed_tendon_properties(
                    current_stiffnesses,
                    current_dampings,
                    current_limit_stiffnesses,
                    current_limits,
                    current_rest_lengths,
                    current_offsets,
                    indices,
                )
            else:
                carb.log_warn("Articulation fixed tendon upper limits randomization cannot be applied in GPU pipeline.")
        elif attribute_name == "tendon_rest_lengths":
            if view._device == "cpu":
                current_stiffnesses = view._physics_view.get_fixed_tendon_stiffnesses()
                current_dampings = view._physics_view.get_fixed_tendon_dampings()
                current_limit_stiffnesses = view._physics_view.get_fixed_tendon_limit_stiffnesses()
                current_limits = view._physics_view.get_fixed_tendon_limits().reshape(
                    view.count, view._physics_view.max_fixed_tendons, 2
                )
                current_rest_lengths = view._physics_view.get_fixed_tendon_rest_lengths()
                current_offsets = view._physics_view.get_fixed_tendon_offsets()

                tendon_rest_lengths = apply_randomization_operation(
                    view_name, operation, attribute_name, samples, indices
                )
                current_rest_lengths[indices] = view._backend_utils.move_data(tendon_rest_lengths, device=device)

                view._physics_view.set_fixed_tendon_properties(
                    current_stiffnesses,
                    current_dampings,
                    current_limit_stiffnesses,
                    current_limits,
                    current_rest_lengths,
                    current_offsets,
                    indices,
                )
            else:
                carb.log_warn("Articulation fixed tendon rest lengths randomization cannot be applied in GPU pipeline.")
        elif attribute_name == "tendon_offsets":
            if view._device == "cpu":
                current_stiffnesses = view._physics_view.get_fixed_tendon_stiffnesses()
                current_dampings = view._physics_view.get_fixed_tendon_dampings()
                current_limit_stiffnesses = view._physics_view.get_fixed_tendon_limit_stiffnesses()
                current_limits = view._physics_view.get_fixed_tendon_limits().reshape(
                    view.count, view._physics_view.max_fixed_tendons, 2
                )
                current_rest_lengths = view._physics_view.get_fixed_tendon_rest_lengths()
                current_offsets = view._physics_view.get_fixed_tendon_offsets()

                tendon_offsets = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
                current_offsets[indices] = view._backend_utils.move_data(tendon_offsets, device=device)

                view._physics_view.set_fixed_tendon_properties(
                    current_stiffnesses,
                    current_dampings,
                    current_limit_stiffnesses,
                    current_limits,
                    current_rest_lengths,
                    current_offsets,
                    indices,
                )
            else:
                carb.log_warn("Articulation fixed tendon offsets randomization cannot be applied in GPU pipeline.")

        return True

    # @staticmethod
    # def initialize(graph_context, node):
    #     function_callback = OgnWritePhysicsArticulationView.on_value_changed_callback
    #     node.get_attribute("inputs:attribute").register_value_changed_callback(function_callback)

    # @staticmethod
    # def on_value_changed_callback(attr) -> None:
    #     node = attr.get_node()
    #     output_attr = node.get_attribute("inputs:values")
    #     if output_attr.get_resolved_type().base_type == og.BaseDataType.UNKNOWN:
    #         specified_type = attr.get_array(False, False, 0)
    #         output_attr.set_resolved_type(og.Controller.attribute_type(f"{specified_type}[]"))
    #         print("RESOLVING TYPE", "="*10)
    #         print(output_attr.get_resolved_type())
