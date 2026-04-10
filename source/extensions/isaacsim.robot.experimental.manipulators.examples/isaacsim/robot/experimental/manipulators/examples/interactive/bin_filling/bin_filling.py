# SPDX-FileCopyrightText: Copyright (c) 2021-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Interactive bin filling example with UR10 robot"""

from __future__ import annotations

import random

import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim
from isaacsim.core.experimental.utils.transform import euler_angles_to_quaternion
from isaacsim.core.rendering_manager import ViewportManager
from isaacsim.core.simulation_manager import SimulationEvent, SimulationManager
from isaacsim.examples.base.base_sample_experimental import BaseSample
from isaacsim.robot.experimental.manipulators.examples.universal_robots.ur10 import UR10
from isaacsim.storage.native import get_assets_root_path

ROBOT_PRIM_PATH = "/World/Scene/ur10"
BIN_PRIM_PATH = "/World/Scene/bin"
SCENE_USD_PATH = "/Isaac/Samples/Leonardo/Stage/ur10_bin_filling.usd"

PIPE_POSITION = [0.0, 0.85, 1.2]
TARGET_POSITION = [0.0, 0.85, -0.44]
EE_OFFSET = [0.0, -0.15, 0.03]

SUCTION_TIP_LOCAL_OFFSET = [0.161709, 0.0, 0.0]

CUBE_SIZE = 0.05
MAX_CUBES = 50

EVENTS_DT = [0.01, 0.0035, 0.01, 1.0, 0.008, 0.005, 0.005]
INITIAL_EE_HEIGHT = 0.3


class BinFilling(BaseSample):
    """Interactive bin filling example using a UR10 robot with experimental APIs.

    A UR10 robot picks up a bin and moves it under a pipe where cubes drop from
    above. The example uses a 7-phase pick-and-hold state machine with IK-based
    end-effector control and dynamic cube spawning.

    Phase summary:
        0: Move EE above bin at initial height.
        1: Lower EE to bin height.
        2: Wait for inertia to settle.
        3: Close gripper (grasp bin).
        4: Lift EE back to initial height.
        5: Move EE to placing position (IK handles the motion).
        6: Pause, trigger cube drop, and hold bin indefinitely.
    """

    def __init__(self) -> None:
        super().__init__()
        self._robot: UR10 | None = None
        self._bin_prim: RigidPrim | None = None
        self._physics_callback_id: int | None = None

        self._cube_pool: RigidPrim | None = None
        self._active_cubes = 0
        self._cubes_to_add = 0

        self._event = 0
        self._t = 0.0
        self._pick_height = 0.0
        self._pause = False
        self._added_cubes = False
        self._step_index = 0

        self._ee_orientation: np.ndarray | None = None
        self._suction_offset_world: np.ndarray | None = None

    # ------------------------------------------------------------------
    # Scene lifecycle
    # ------------------------------------------------------------------

    def setup_scene(self) -> None:
        """Load the USD scene, wrap the robot and bin, and pre-allocate the cube pool."""
        assets_root = get_assets_root_path()
        stage_utils.add_reference_to_stage(usd_path=assets_root + SCENE_USD_PATH, path="/World/Scene")

        self._robot = UR10(robot_path=ROBOT_PRIM_PATH, create_robot=False, attach_gripper=True)
        self._robot.set_default_state(dof_positions=[-np.pi / 2, -np.pi / 2, -np.pi / 2, -np.pi / 2, np.pi / 2, 0])

        self._bin_prim = RigidPrim(BIN_PRIM_PATH)

        self._create_cube_pool()

    async def setup_post_load(self) -> None:
        """Set the camera, pre-compute the EE orientation and suction tip offset."""
        ViewportManager.set_camera_view(eye=[2.0, 1.5, 1.0], target=[0.0, 0.3, 0.0], camera="/OmniverseKit_Persp")
        self._ee_orientation = euler_angles_to_quaternion([np.pi, 0.0, -np.pi / 2.0], extrinsic=False).numpy()
        q = self._ee_orientation
        w, u = q[0], q[1:]
        v = np.asarray(SUCTION_TIP_LOCAL_OFFSET)
        self._suction_offset_world = v + 2.0 * w * np.cross(u, v) + 2.0 * np.cross(u, np.cross(u, v))

    async def setup_pre_reset(self) -> None:
        """Deregister physics callback, deactivate cubes, and reset state machine."""
        self._remove_physics_callback()
        self._deactivate_all_cubes()
        self._reset_state_machine()

    async def setup_post_reset(self) -> None:
        """Reset the robot to its default pose."""
        if self._robot is not None:
            self._robot.reset_to_default_pose()

    async def setup_post_clear(self) -> None:
        """Release all references when the scene is cleared."""
        self._cleanup_all()

    def physics_cleanup(self) -> None:
        """Release all references on extension hot-reload."""
        self._cleanup_all()

    def _cleanup_all(self) -> None:
        """Release all internal references and reset state."""
        self._remove_physics_callback()
        self._robot = None
        self._bin_prim = None
        self._cube_pool = None
        self._active_cubes = 0
        self._cubes_to_add = 0
        self._ee_orientation = None
        self._suction_offset_world = None
        self._reset_state_machine()

    def _reset_state_machine(self) -> None:
        """Reset the pick-place state machine to its initial state."""
        self._event = 0
        self._t = 0.0
        self._pick_height = 0.0
        self._pause = False
        self._added_cubes = False
        self._step_index = 0

    # ------------------------------------------------------------------
    # Physics callback management
    # ------------------------------------------------------------------

    def _remove_physics_callback(self) -> None:
        """Deregister the active physics callback if one exists."""
        if self._physics_callback_id is not None:
            SimulationManager.deregister_callback(self._physics_callback_id)
            self._physics_callback_id = None

    # ------------------------------------------------------------------
    # Cube pool management
    # ------------------------------------------------------------------

    def _create_cube_pool(self) -> None:
        """Pre-create cubes off-screen, hidden, with collision and rigid body APIs.

        Cubes are kept physics-enabled (to avoid tensor view errors on disabled
        bodies) but positioned far off-screen and invisible. Velocities are
        zeroed when a cube is activated.
        """
        offscreen = [0.0, 0.0, -1000.0]
        for i in range(MAX_CUBES):
            path = f"/World/cube_{i}"
            Cube(path, sizes=CUBE_SIZE, positions=offscreen, colors=[0.6, 0.6, 0.6])
            GeomPrim(path, apply_collision_apis=True)

        cube_paths = [f"/World/cube_{i}" for i in range(MAX_CUBES)]
        self._cube_pool = RigidPrim(cube_paths, resolve_paths=False)
        self._cube_pool.set_visibilities(False)
        self._active_cubes = 0

    def _deactivate_all_cubes(self) -> None:
        """Hide all active cubes and move them off-screen."""
        if self._cube_pool is None or self._active_cubes == 0:
            return
        indices = list(range(self._active_cubes))
        self._cube_pool.set_visibilities(False, indices=indices)
        self._cube_pool.set_world_poses(positions=[0.0, 0.0, -1000.0], indices=indices)
        self._active_cubes = 0
        self._cubes_to_add = 0

    def _activate_next_cube(self) -> None:
        """Activate one cube from the pool at the pipe position with a random orientation."""
        if self._cube_pool is None or self._active_cubes >= len(self._cube_pool):
            self._cubes_to_add = 0
            return

        orientation = np.array([random.random(), random.random(), random.random(), random.random()])
        orientation = orientation / np.linalg.norm(orientation)

        idx = self._active_cubes
        self._cube_pool.set_world_poses(positions=PIPE_POSITION, orientations=orientation, indices=idx)
        self._cube_pool.set_visibilities(True, indices=idx)
        self._cube_pool.set_velocities(
            linear_velocities=[0.0, 0.0, 0.0], angular_velocities=[0.0, 0.0, 0.0], indices=idx
        )

        self._active_cubes += 1
        self._cubes_to_add -= 1

    # ------------------------------------------------------------------
    # Start event (called from extension UI)
    # ------------------------------------------------------------------

    async def on_fill_bin_event_async(self) -> None:
        """Start the bin filling simulation by registering the physics callback."""
        if self._robot is None:
            return

        if not app_utils.is_playing():
            app_utils.play()
            await app_utils.update_app_async()

        self._physics_callback_id = SimulationManager.register_callback(
            self._physics_step, event=SimulationEvent.PHYSICS_POST_STEP
        )

    # ------------------------------------------------------------------
    # 7-phase pick-and-hold state machine
    # ------------------------------------------------------------------

    def _physics_step(self, dt: float, context: object) -> None:
        """Execute one step of the pick-and-hold state machine and handle cube spawning."""
        if self._robot is None or self._bin_prim is None:
            return

        if (
            self._cubes_to_add > 0
            and self._cube_pool is not None
            and self._active_cubes < len(self._cube_pool)
            and self._step_index % 30 == 0
        ):
            self._activate_next_cube()
        self._step_index += 1

        if self._pause or self._is_done():
            return

        bin_pos, _ = self._bin_prim.get_world_poses()
        picking_position = bin_pos.numpy().flatten()
        placing_position = TARGET_POSITION

        if self._event in [0, 1]:
            self._pick_height = picking_position[2]

        if self._event == 2:
            pass
        elif self._event == 3:
            self._robot.close_gripper()
        else:
            if self._event < 5:
                target_x, target_y = picking_position[0], picking_position[1]
            else:
                target_x, target_y = placing_position[0], placing_position[1]

            if self._event == 1:
                target_height = INITIAL_EE_HEIGHT + self._t * (self._pick_height - INITIAL_EE_HEIGHT)
            elif self._event == 4:
                target_height = self._pick_height + self._t * (INITIAL_EE_HEIGHT - self._pick_height)
            elif self._event == 6:
                target_height = INITIAL_EE_HEIGHT + self._t * (placing_position[2] - INITIAL_EE_HEIGHT)
            else:
                target_height = INITIAL_EE_HEIGHT

            suction_target = np.array(
                [
                    target_x + EE_OFFSET[0],
                    target_y + EE_OFFSET[1],
                    target_height + EE_OFFSET[2],
                ]
            )
            ee_link_target = suction_target - self._suction_offset_world

            self._robot.set_end_effector_pose(
                position=ee_link_target,
                orientation=self._ee_orientation,
            )

        self._t += EVENTS_DT[self._event]
        if self._t >= 1.0:
            self._event += 1
            self._t = 0.0

        if not self._added_cubes and self._event == 6 and not self._pause:
            self._pause = True
            self._cubes_to_add += 20
            self._added_cubes = True

        if self._is_done():
            app_utils.pause()

    def _is_done(self) -> bool:
        """Return whether the state machine has completed all phases."""
        return self._event >= len(EVENTS_DT)
