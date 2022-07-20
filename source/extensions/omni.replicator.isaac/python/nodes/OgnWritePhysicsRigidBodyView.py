# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import torch
import numpy as np

import omni.graph.core as og

from omni.replicator.isaac import physics_view as physics
from omni.replicator.isaac import RIGID_BODY_ATTRIBUTES
from omni.isaac.core.utils.torch.rotations import euler_angles_to_quats as euler_angles_to_quats_torch
from omni.isaac.core.utils.numpy.rotations import euler_angles_to_quats as euler_angles_to_quats_numpy


OPERATION_TYPES = ["direct", "additive", "scaling"]


def apply_randomization_operation(view_name, operation, attribute_name, samples, indices):
    if operation == "additive":
        return physics._rigid_body_views_initial_values[view_name][attribute_name][indices] + samples
    elif operation == "scaling":
        return physics._rigid_body_views_initial_values[view_name][attribute_name][indices] * samples
    else:
        return samples


class OgnWritePhysicsRigidBodyView:
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
            view = physics._rigid_body_views.get(view_name)
            if view is None:
                raise ValueError(f"Expected a registered rigid_body_view, but instead received {view_name}")
            if attribute_name not in RIGID_BODY_ATTRIBUTES:
                raise ValueError(
                    f"Expected an attribute in {RIGID_BODY_ATTRIBUTES}, but instead received {attribute_name}"
                )
            if operation not in OPERATION_TYPES:
                raise ValueError(f"Expected an operation type in {OPERATION_TYPES}, but instead received {operation}")
            samples = np.array(values.attribute_by_name("values").value).reshape(len(indices), -1)
            device = view._device
        except Exception as error:
            db.log_error(f"WritePhysics Error: {error}")
            db.outputs.execOut = og.ExecutionAttributeState.DISABLED
            return False

        if view._backend == "torch":
            samples = torch.from_numpy(samples).float().to(device)
            indices = torch.from_numpy(indices).long().to(device)

        if attribute_name == "angular_velocity":
            angular_velocities = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
            view.set_angular_velocities(angular_velocities, indices)
        elif attribute_name == "linear_velocity":
            linear_velocities = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
            view.set_linear_velocities(linear_velocities, indices)
        elif attribute_name == "velocity":
            velocities = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
            view.set_velocities(velocities, indices)
        elif attribute_name == "position":
            positions = apply_randomization_operation(view_name, operation, attribute_name, samples, indices)
            view.set_world_poses(positions=positions, indices=indices)
        elif attribute_name == "orientation":
            # TODO: Add additive and scaling operation for orientation using core utils
            if view._backend == "torch":
                orientations = euler_angles_to_quats_torch(euler_angles=samples, degrees=False, device=device).float()
            elif view._backend == "numpy":
                orientations = euler_angles_to_quats_numpy(euler_angles=samples, degrees=False)
            view.set_world_poses(orientations=orientations, indices=indices)
        elif attribute_name == "force":
            view.apply_forces(samples, indices)

        return True
