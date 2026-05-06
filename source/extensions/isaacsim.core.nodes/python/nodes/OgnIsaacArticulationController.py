# SPDX-FileCopyrightText: Copyright (c) 2022-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import numpy as np
from isaacsim.core.experimental.prims import Articulation
from isaacsim.core.nodes import BaseResetNode
from isaacsim.core.nodes.ogn.OgnIsaacArticulationControllerDatabase import OgnIsaacArticulationControllerDatabase


class OgnIsaacArticulationControllerInternalState(BaseResetNode):
    """nodes for moving an articulated robot with joint commands."""

    def __init__(self):
        self.prim_path = None
        self.articulation = None
        self.joint_names = None
        self.joint_indices = None
        self.joint_picked = False
        self.node = None
        super().__init__(initialize=False)

    def initialize_controller(self):
        self.articulation = Articulation(self.prim_path)
        self.initialized = True

    def joint_indicator(self):
        if self.joint_names:
            self.joint_indices = self.articulation.get_dof_indices(self.joint_names).numpy().flatten()
        elif np.size(self.joint_indices) > 0:
            self.joint_indices = self.joint_indices
        else:
            # when indices is none (not []), it defaults too all DOFs
            self.joint_indices = None
        self.joint_picked = True

    def apply_action(
        self,
        joint_positions: np.ndarray | list | tuple,
        joint_velocities: np.ndarray | list | tuple,
        joint_efforts: np.ndarray | list | tuple,
    ) -> bool:
        """Apply position, velocity, and effort commands to the articulation.

        All commands are validated and filtered before any targets are written, so an invalid command prevents partial
        application of the remaining valid commands.

        Args:
            joint_positions: Position targets for the selected joints.
            joint_velocities: Velocity targets for the selected joints.
            joint_efforts: Effort targets for the selected joints.

        Returns:
            True when all provided commands were valid and applied; False when the controller is not initialized or any
            command is invalid.
        """
        if not self.initialized:
            return False

        position_command = self._prepare_command(joint_positions)
        velocity_command = self._prepare_command(joint_velocities)
        effort_command = self._prepare_command(joint_efforts)
        if position_command is None or velocity_command is None or effort_command is None:
            return False

        joint_positions, position_indices = position_command
        joint_velocities, velocity_indices = velocity_command
        joint_efforts, effort_indices = effort_command
        if np.size(joint_positions) > 0:
            self.articulation.set_dof_position_targets(joint_positions, dof_indices=position_indices)
        if np.size(joint_velocities) > 0:
            self.articulation.set_dof_velocity_targets(joint_velocities, dof_indices=velocity_indices)
        if np.size(joint_efforts) > 0:
            self.articulation.set_dof_efforts(joint_efforts, dof_indices=effort_indices)
        return True

    def _prepare_command(
        self, command: np.ndarray | list | tuple
    ) -> tuple[np.ndarray | list | tuple, np.ndarray | list | None] | None:
        """Validate and filter a command before any articulation targets are written.

        Args:
            command: Joint command values for the currently selected joints.

        Returns:
            A tuple of filtered command values and matching DOF indices. Returns None if the command width does not
            match the explicit joint selection or if the command shape cannot be resolved.
        """
        if np.size(command) == 0:
            return command, self.joint_indices
        command_valid, dof_indices = self._resolve_command_indices(command)
        if not command_valid:
            return None
        command, dof_indices = self._filter_finite_command(command, dof_indices)
        if command is None:
            return None
        return command, dof_indices

    def _resolve_command_indices(self, command: np.ndarray | list | tuple) -> tuple[bool, np.ndarray | list | None]:
        """Validate that a command width matches the explicitly selected joints."""
        if self.joint_indices is None:
            return True, self.joint_indices
        command_size = np.size(command)
        joint_indices = np.asarray(self.joint_indices).reshape(-1)
        if command_size == joint_indices.size:
            return True, self.joint_indices
        return False, self.joint_indices

    def _filter_finite_command(
        self, command: np.ndarray | list | tuple, dof_indices: np.ndarray | list | None
    ) -> tuple[np.ndarray | list | tuple | None, np.ndarray | list | None]:
        """Drop NaN entries so omitted targets are left unchanged by the backend."""
        command_array = np.asarray(command)
        if not np.isnan(command_array).any():
            return command, dof_indices

        command_values = command_array.reshape(-1)
        # NaN command entries mean "leave the current target unchanged".  Write
        # only the finite entries so backends without local tensor state do not
        # need to read the previous target value.
        finite_mask = ~np.isnan(command_values)
        if dof_indices is None:
            selected_dof_indices = np.arange(command_values.size, dtype=np.int64)
        else:
            selected_dof_indices = np.asarray(dof_indices).reshape(-1)
            if selected_dof_indices.size != command_values.size:
                return None, dof_indices

        return command_values[finite_mask], selected_dof_indices[finite_mask]

    def custom_reset(self):
        self.articulation = None
        if self.initialized:
            self.node.get_attribute("inputs:positionCommand").set(np.empty(shape=(0, 0), dtype=np.double))
            self.node.get_attribute("inputs:velocityCommand").set(np.empty(shape=(0, 0), dtype=np.double))
            self.node.get_attribute("inputs:effortCommand").set(np.empty(shape=(0, 0), dtype=np.double))


class OgnIsaacArticulationController:
    """nodes for moving an articulated robot with joint commands."""

    @staticmethod
    def init_instance(node, graph_instance_id):
        state = OgnIsaacArticulationControllerDatabase.get_internal_state(node, graph_instance_id)
        state.node = node

    @staticmethod
    def internal_state():
        return OgnIsaacArticulationControllerInternalState()

    @staticmethod
    def compute(db) -> bool:
        state = db.per_instance_state
        try:
            if not state.initialized:
                if len(db.inputs.robotPath) != 0:
                    state.prim_path = db.inputs.robotPath
                else:
                    if len(db.inputs.targetPrim) == 0:
                        db.log_error("No robot prim found for the articulation controller")
                        return False
                    else:
                        state.prim_path = db.inputs.targetPrim[0].GetString()

                # initialize the controller handle for the robot
                state.initialize_controller()

            # pick the joints that are being commanded, this can be different at every step
            joint_names = db.inputs.jointNames
            if joint_names and np.asarray([joint_names != state.joint_names]).flatten().any():
                state.joint_names = joint_names
                state.joint_picked = False

            joint_indices = db.inputs.jointIndices
            if np.asarray(joint_indices).any() and not np.array_equal(joint_indices, state.joint_indices):
                state.joint_indices = np.array(joint_indices)
                state.joint_picked = False

            if not state.joint_picked:
                state.joint_indicator()

            if not state.apply_action(db.inputs.positionCommand, db.inputs.velocityCommand, db.inputs.effortCommand):
                db.log_warn(
                    "Articulation controller command length does not match the selected joint count; ignoring command."
                )
                return False

        except Exception as error:
            db.log_warn(str(error))
            return False

        return True

    @staticmethod
    def release_instance(node, graph_instance_id):
        try:
            state = OgnIsaacArticulationControllerDatabase.get_internal_state(node, graph_instance_id)
        except Exception:
            state = None
            pass

        if state is not None:
            state.reset()
            state.initialized = False
