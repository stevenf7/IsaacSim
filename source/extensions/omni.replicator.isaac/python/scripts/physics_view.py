# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import asyncio
from typing import List, Optional, Tuple, Union

import carb
import numpy as np
import torch
import omni.kit
import omni.timeline
import omni.usd

from omni.replicator.core import distribution
from omni.replicator.core.scripts.utils import ReplicatorItem, ReplicatorWrapper, utils
from .context import trigger_randomization

_rigid_body_views = dict()
_articulation_views = dict()
_rigid_body_views_initial_values = dict()
_articulation_views_initial_values = dict()


def register_rigid_body_view(rigid_body_view):
    clone_tensor = rigid_body_view._backend_utils.clone_tensor
    tensor_cat = rigid_body_view._backend_utils.tensor_cat
    create_zeros_tensor = rigid_body_view._backend_utils.create_zeros_tensor
    device = rigid_body_view._device

    name = rigid_body_view.name
    _rigid_body_views[name] = rigid_body_view
    initial_values = dict()
    initial_values["position"] = rigid_body_view._dynamics_default_state.positions
    initial_values["orientation"] = rigid_body_view._dynamics_default_state.orientations
    initial_values["linear_velocity"] = rigid_body_view._dynamics_default_state.linear_velocities
    initial_values["angular_velocity"] = rigid_body_view._dynamics_default_state.angular_velocities
    initial_values["velocity"] = tensor_cat(
        [initial_values["linear_velocity"], initial_values["angular_velocity"]], dim=-1
    )
    initial_values["force"] = create_zeros_tensor(
        shape=[initial_values["position"].shape[0], 3], dtype="float32", device=device
    )
    _rigid_body_views_initial_values[name] = initial_values


def register_articulation_view(articulation_view):
    clone_tensor = articulation_view._backend_utils.clone_tensor
    tensor_cat = articulation_view._backend_utils.tensor_cat
    create_zeros_tensor = articulation_view._backend_utils.create_zeros_tensor
    device = articulation_view._device

    name = articulation_view.name
    _articulation_views[name] = articulation_view
    initial_values = dict()
    initial_values["stiffness"] = articulation_view._default_kps
    initial_values["damping"] = articulation_view._default_kds
    initial_values["joint_friction"] = clone_tensor(
        articulation_view._physics_view.get_dof_friction_coefficients(), device="cpu"
    )
    initial_values["position"] = articulation_view._default_state.positions
    initial_values["orientation"] = articulation_view._default_state.orientations
    initial_values["linear_velocity"] = articulation_view.get_linear_velocities()
    initial_values["angular_velocity"] = articulation_view.get_angular_velocities()
    initial_values["velocity"] = tensor_cat(
        [initial_values["linear_velocity"], initial_values["angular_velocity"]], dim=-1
    )
    initial_values["joint_positions"] = articulation_view._default_joints_state.positions
    initial_values["joint_velocities"] = articulation_view._default_joints_state.positions
    initial_values["lower_dof_limits"] = articulation_view.get_dof_limits()[..., 0]
    initial_values["upper_dof_limits"] = articulation_view.get_dof_limits()[..., 1]
    initial_values["max_efforts"] = articulation_view.get_max_efforts()
    initial_values["joint_armatures"] = clone_tensor(articulation_view._physics_view.get_dof_armatures(), device="cpu")
    initial_values["joint_max_velocities"] = clone_tensor(
        articulation_view._physics_view.get_dof_max_velocities(), device="cpu"
    )
    initial_values["joint_efforts"] = create_zeros_tensor(
        shape=[initial_values["stiffness"].shape[0], initial_values["stiffness"].shape[1]],
        dtype="float32",
        device=device,
    )
    _articulation_views_initial_values[name] = initial_values


def step_randomization(reset_inds: Optional[Union[list, np.ndarray, torch.Tensor]] = list()):
    if torch.is_tensor(reset_inds):
        trigger_randomization(reset_inds.cpu().numpy())
    else:
        trigger_randomization(np.asarray(reset_inds))


@ReplicatorWrapper
def _write_physics_view_node(view, attribute, values, operation, node_type):
    node = utils.create_node(node_type)
    node.get_attribute("inputs:attribute").set(attribute)
    node.get_attribute("inputs:prims").set(view)
    node.get_attribute("inputs:operation").set(operation)
    if not isinstance(values, ReplicatorItem):
        values = uniform(values, values)

    counter = ReplicatorItem(utils.create_node, "omni.replicator.isaac.OgnCountIndices")

    context = ReplicatorItem.get_context()
    context.get_attribute("outputs:indices").connect(counter.node.get_attribute("inputs:indices"), True)
    counter.node.get_attribute("outputs:count").connect(values.node.get_attribute("inputs:numSamples"), True)
    context.get_attribute("outputs:indices").connect(node.get_attribute("inputs:indices"), True)

    utils.auto_connect(values.node, node)
    return node


@ReplicatorWrapper
def randomize_rigid_body_view(
    view_name,
    operation: str = "direct",
    position: Union[ReplicatorItem, Tuple[float, float, float]] = None,
    orientation: Union[ReplicatorItem, Tuple[float, float, float]] = None,
    linear_velocity: Union[ReplicatorItem, Tuple[float, float, float]] = None,
    angular_velocity: Union[ReplicatorItem, Tuple[float, float, float]] = None,
    velocity: Union[ReplicatorItem, Tuple[float, float, float]] = None,
    force: Union[ReplicatorItem, Tuple[float, float, float]] = None,
):
    # check whether randomization occurs within the correct context
    context = ReplicatorItem.get_context().get_node_type().get_node_type()
    if context != "omni.replicator.isaac.OgnIntervalFiltering":
        raise ValueError(
            "randomize_rigid_body_view() is expected to be called within the omni.replicator.isaac.randomize.on_interval"
            + " or omni.replicator.isaac.randomize.on_env_reset context managers."
        )

    node_type = "omni.replicator.isaac.OgnWritePhysicsRigidBodyView"

    if _rigid_body_views.get(view_name) is None:
        raise ValueError(f"Expected a registered rigid body view, but instead received {view_name}")

    if position is not None:
        _write_physics_view_node(view_name, "position", position, operation, node_type)
    if orientation is not None:
        _write_physics_view_node(view_name, "orientation", orientation, operation, node_type)
    if linear_velocity is not None:
        _write_physics_view_node(view_name, "linear_velocity", linear_velocity, operation, node_type)
    if angular_velocity is not None:
        _write_physics_view_node(view_name, "angular_velocity", angular_velocity, operation, node_type)
    if velocity is not None:
        _write_physics_view_node(view_name, "velocity", velocity, operation, node_type)
    if force is not None:
        _write_physics_view_node(view_name, "force", force, operation, node_type)


@ReplicatorWrapper
def randomize_articulation_view(
    view_name,
    operation: str = "direct",
    stiffness: Union[ReplicatorItem, Tuple[float]] = None,
    damping: Union[ReplicatorItem, Tuple[float]] = None,
    joint_friction: Union[ReplicatorItem, Tuple[float]] = None,
    position: Union[ReplicatorItem, Tuple[float, float, float]] = None,
    orientation: Union[ReplicatorItem, Tuple[float, float, float]] = None,
    linear_velocity: Union[ReplicatorItem, Tuple[float, float, float]] = None,
    angular_velocity: Union[ReplicatorItem, Tuple[float, float, float]] = None,
    velocity: Union[ReplicatorItem, Tuple[float, float, float]] = None,
    joint_positions: Union[ReplicatorItem, Tuple[float]] = None,
    joint_velocities: Union[ReplicatorItem, Tuple[float]] = None,
    lower_dof_limits: Union[ReplicatorItem, Tuple[float]] = None,
    upper_dof_limits: Union[ReplicatorItem, Tuple[float]] = None,
    max_efforts: Union[ReplicatorItem, Tuple[float]] = None,
    joint_armatures: Union[ReplicatorItem, Tuple[float]] = None,
    joint_max_velocities: Union[ReplicatorItem, Tuple[float]] = None,
    joint_efforts: Union[ReplicatorItem, Tuple[float]] = None,
):
    # check whether randomization occurs within the correct context
    context = ReplicatorItem.get_context().get_node_type().get_node_type()
    if context != "omni.replicator.isaac.OgnIntervalFiltering":
        raise ValueError(
            "randomize_articulation_view() is expected to be called within the omni.replicator.isaac.randomize.on_interval"
            + " or omni.replicator.isaac.randomize.on_env_reset context managers."
        )

    node_type = "omni.replicator.isaac.OgnWritePhysicsArticulationView"

    if _articulation_views.get(view_name) is None:
        raise ValueError(f"Expected a registered articulation view, but instead received {view_name}")

    if stiffness is not None:
        _write_physics_view_node(view_name, "stiffness", stiffness, operation, node_type)
    if damping is not None:
        _write_physics_view_node(view_name, "damping", damping, operation, node_type)
    if joint_friction is not None:
        _write_physics_view_node(view_name, "joint_friction", joint_friction, operation, node_type)
    if position is not None:
        _write_physics_view_node(view_name, "position", position, operation, node_type)
    if orientation is not None:
        _write_physics_view_node(view_name, "orientation", orientation, operation, node_type)
    if linear_velocity is not None:
        _write_physics_view_node(view_name, "linear_velocity", linear_velocity, operation, node_type)
    if angular_velocity is not None:
        _write_physics_view_node(view_name, "angular_velocity", angular_velocity, operation, node_type)
    if velocity is not None:
        _write_physics_view_node(view_name, "velocity", velocity, operation, node_type)
    if joint_positions is not None:
        _write_physics_view_node(view_name, "joint_positions", joint_positions, operation, node_type)
    if joint_velocities is not None:
        _write_physics_view_node(view_name, "joint_velocities", joint_velocities, operation, node_type)
    if lower_dof_limits is not None:
        _write_physics_view_node(view_name, "lower_dof_limits", lower_dof_limits, operation, node_type)
    if upper_dof_limits is not None:
        _write_physics_view_node(view_name, "upper_dof_limits", upper_dof_limits, operation, node_type)
    if max_efforts is not None:
        _write_physics_view_node(view_name, "max_efforts", max_efforts, operation, node_type)
    if joint_armatures is not None:
        _write_physics_view_node(view_name, "joint_armatures", joint_armatures, operation, node_type)
    if joint_max_velocities is not None:
        _write_physics_view_node(view_name, "joint_max_velocities", joint_max_velocities, operation, node_type)
    if joint_efforts is not None:
        _write_physics_view_node(view_name, "joint_efforts", joint_efforts, operation, node_type)
