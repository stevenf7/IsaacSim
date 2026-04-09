# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Example demonstrating PINK multi-task IK with weighted frame, posture, and damping tasks."""


from __future__ import annotations

from typing import Any

import isaacsim.robot_motion.experimental.motion_generation as mg
import numpy as np
import pink.tasks
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import Articulation
from isaacsim.core.experimental.utils import transform as transform_utils
from isaacsim.core.experimental.utils.stage import add_reference_to_stage
from isaacsim.robot_motion.pink import PinkIKController, load_pink_supported_robot
from isaacsim.storage.native import get_assets_root_path_async

_FRANKA_TOOL_FRAME = "panda_hand"


class FrankaMultiTaskExample:
    """Example demonstrating multiple weighted PINK tasks via PinkIKController.

    Shows how to combine a FrameTask for end-effector tracking, a PostureTask for
    joint regularization, and a DampingTask for velocity smoothing. The user can
    adjust cost weights to observe the trade-off between tracking accuracy and
    motion smoothness.
    """

    def __init__(self) -> None:
        self._controller: PinkIKController | None = None
        self._articulation: Articulation | None = None
        self._target: Cube | None = None
        self._damping_task: pink.tasks.DampingTask | None = None
        self._sim_time: float = 0.0
        self._controller_reset: bool = False
        self._robot_joint_space: list[str] = []
        self._robot_site_space: list[str] = [_FRANKA_TOOL_FRAME]

    async def load_example_assets(self) -> tuple:
        """Load robot and target assets to the stage."""
        self._robot_prim_path = "/panda"
        path_to_robot_usd = await get_assets_root_path_async() + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"

        add_reference_to_stage(path_to_robot_usd, self._robot_prim_path)
        self._articulation = Articulation(self._robot_prim_path)

        self._target = Cube(paths="/World/target", sizes=0.04, positions=[0.5, 0.0, 0.25])

        return self._articulation, self._target

    def setup(
        self,
        position_cost: float = 1.0,
        orientation_cost: float = 1.0,
        posture_cost: float = 1e-3,
        damping_cost: float = 1e-4,
    ) -> None:
        """Set up multi-task IK with configurable cost weights.

        Args:
            position_cost: Cost for end-effector position tracking.
            orientation_cost: Cost for end-effector orientation tracking.
            posture_cost: Cost for posture regularization.
            damping_cost: Cost for velocity damping.
        """
        pink_robot = load_pink_supported_robot("franka")
        self._robot_joint_space = self._articulation.dof_names

        self._damping_task = pink.tasks.DampingTask(cost=damping_cost)

        self._controller = PinkIKController(
            pink_robot=pink_robot,
            robot_joint_space=self._robot_joint_space,
            robot_site_space=self._robot_site_space,
            tool_frame=_FRANKA_TOOL_FRAME,
            position_cost=position_cost,
            orientation_cost=orientation_cost,
            posture_cost=posture_cost,
            gain=0.8,
            extra_tasks=[self._damping_task],
            dt=1.0 / 60.0,
        )

        # Use a softer gain for posture regularization than for EE tracking
        posture_task = self._controller.get_posture_task()
        if posture_task is not None:
            posture_task.gain = 0.5

        # Set initial target cube position
        quat = transform_utils.euler_angles_to_quaternion([0, np.pi, 0]).numpy()
        self._target.set_world_poses(positions=np.array([[0.5, 0.0, 0.7]]), orientations=np.array([quat]))

        self._sim_time = 0.0
        self._controller_reset = False

    def update_costs(
        self,
        position_cost: float | None = None,
        orientation_cost: float | None = None,
        posture_cost: float | None = None,
        damping_cost: float | None = None,
    ) -> None:
        """Update task cost weights at runtime.

        Args:
            position_cost: New position tracking cost, or None to keep current.
            orientation_cost: New orientation tracking cost, or None to keep current.
            posture_cost: New posture regularization cost, or None to keep current.
            damping_cost: New velocity damping cost, or None to keep current.
        """
        if self._controller is None:
            return
        frame_task = self._controller.get_frame_task()
        if position_cost is not None:
            frame_task.set_position_cost(position_cost)
        if orientation_cost is not None:
            frame_task.set_orientation_cost(orientation_cost)
        posture_task = self._controller.get_posture_task()
        if posture_task is not None and posture_cost is not None:
            posture_task.cost = posture_cost
        if self._damping_task is not None and damping_cost is not None:
            self._damping_task.cost = damping_cost

    def update(self, step: float) -> None:
        """Update the IK solve on each physics step.

        Args:
            step: Physics timestep in seconds.
        """
        if self._controller is None:
            return

        if not self._articulation.is_physics_tensor_entity_valid():
            return

        estimated_state = mg.RobotState(
            joints=mg.JointState.from_name(
                robot_joint_space=self._robot_joint_space,
                positions=(self._robot_joint_space, self._articulation.get_dof_positions()),
                velocities=(self._robot_joint_space, self._articulation.get_dof_velocities()),
            )
        )

        target_positions, target_orientations = self._target.get_world_poses()

        setpoint_state = mg.RobotState(
            sites=mg.SpatialState.from_name(
                spatial_space=self._robot_site_space,
                positions=([_FRANKA_TOOL_FRAME], target_positions),
                orientations=([_FRANKA_TOOL_FRAME], target_orientations),
            ),
        )

        if not self._controller_reset:
            self._controller_reset = self._controller.reset(estimated_state, setpoint_state, self._sim_time)

        desired_state = self._controller.forward(estimated_state, setpoint_state, self._sim_time)

        if desired_state is not None and desired_state.joints.positions is not None:
            self._articulation.set_dof_position_targets(
                positions=desired_state.joints.positions,
                dof_indices=desired_state.joints.position_indices,
            )

        self._sim_time += step

    def reset(self, **kwargs: Any) -> None:
        """Reset the example.

        Args:
            **kwargs: Cost weight overrides forwarded to setup().
        """
        self.setup(**kwargs)
