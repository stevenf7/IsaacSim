# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Kinematic locomotion controller for VR-driven base movement.

VR controller mapping:
- Left thumbstick Y:       Forward / backward slide (local frame)
- Left thumbstick X:       Left / right slide (local frame)
- Right thumbstick X:      Yaw rotation (turn left/right)
- Right primary button:    Move down (world Z-axis, ``A`` on Meta)
- Right secondary button:  Move up (world Z-axis, ``B`` on Meta)
- Left primary button:     Toggle Carry Tracking Space (``X`` on Meta)

All horizontal movement is in the prim's local frame so "forward" always
means the direction the prim is currently facing (+X in Isaac Sim Z-up).
"""

from __future__ import annotations

import math
import time
from contextlib import nullcontext

import numpy as np
from isaacsim.core.experimental.prims import XformPrim
from isaacsim.core.experimental.utils.stage import get_current_stage
from pxr import Gf, Sdf, Usd


class LocomotionController:
    """Kinematic locomotion controller - moves a base prim via VR input.

    Reads thumbstick and grab-trigger values each frame and applies
    incremental position and yaw changes through ``XformPrim`` world-pose API.
    No physics simulation is involved.

    When Carry Tracking Space is toggled on, the same movement delta is also
    applied to the tracking-space prim so the entire VR workspace
    moves together with the robot.
    """

    DEADZONE = 0.1

    def __init__(self):
        self._prim_path: str = ""
        self._tracking_space_prim_path: str = ""
        self._base_xform: XformPrim | None = None
        self._tracking_space_xform: XformPrim | None = None

        self._initial_base_pose: tuple[np.ndarray, np.ndarray] | None = None
        self._initial_tracking_space_pose: tuple[np.ndarray, np.ndarray] | None = None

        self._edit_layer: Sdf.Layer | None = None

        self._linear_speed: float = 0.2
        self._angular_speed: float = 0.2
        self._running = False
        self._last_update_time: float = 0.0
        self._carry_tracking_space: bool = False
        self._prev_left_primary_click: bool = False

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    @property
    def prim_path(self) -> str:
        return self._prim_path

    @property
    def tracking_space_prim_path(self) -> str:
        return self._tracking_space_prim_path

    @property
    def linear_speed(self) -> float:
        return self._linear_speed

    @property
    def angular_speed(self) -> float:
        return self._angular_speed

    @property
    def is_running(self) -> bool:
        return self._running

    def set_prim_path(self, path: str) -> None:
        self._prim_path = path

    def set_tracking_space_prim_path(self, path: str) -> None:
        """Sets the tracking-space prim carried with the base when Carry Tracking Space is enabled."""
        self._tracking_space_prim_path = path
        self._refresh_tracking_space_xform()

    def set_linear_speed(self, speed: float) -> None:
        self._linear_speed = max(0.0, speed)

    def set_angular_speed(self, speed: float) -> None:
        self._angular_speed = max(0.0, speed)

    def set_edit_layer(self, layer: Sdf.Layer | None) -> None:
        """Sets the USD layer for prim writes.

        Marker prims have their xformOps in an anonymous session sublayer.
        Without directing writes to that layer, ``set_world_poses`` writes
        to the root layer, which is shadowed by the session sublayer.
        """
        self._edit_layer = layer

    # ------------------------------------------------------------------
    # Validate / Enable / Disable
    # ------------------------------------------------------------------

    def validate(self) -> tuple[bool, str]:
        """Validates the target prim and caches XformPrim wrappers.

        Uses ``XformPrim.reset_xform_op_properties()`` to normalise the prim's
        xform stack to ``xformOp:translate`` / ``xformOp:orient`` / ``xformOp:scale``
        in double precision (world pose is preserved).

        Returns:
            (is_valid, message) tuple.
        """
        stage = get_current_stage()
        if not stage:
            return False, "No USD stage available"

        if not self._prim_path or not Sdf.Path.IsValidPathString(self._prim_path):
            return False, "Invalid prim path"

        prim = stage.GetPrimAtPath(self._prim_path)
        if not prim or not prim.IsValid():
            return False, f"Prim not found at '{self._prim_path}'"

        ctx = (
            Usd.EditContext(stage, self._edit_layer)
            if self._edit_layer and self._prim_path.startswith("/Teleop/")
            else nullcontext()
        )
        with ctx:
            try:
                self._base_xform = XformPrim(self._prim_path, reset_xform_op_properties=True)
            except Exception as exc:
                return False, f"XformPrim error: {exc}"

        self._refresh_tracking_space_xform()

        return True, "Valid"

    def enable(self) -> tuple[bool, str]:
        """Validates, caches initial poses, and enables the controller.

        Returns:
            (success, message) tuple.
        """
        ok, msg = self.validate()
        if not ok:
            return False, msg

        self._cache_initial_poses()
        self._running = True
        self._last_update_time = 0.0
        return True, "Running"

    def disable(self) -> None:
        """Disables the controller and restores prims to their initial poses."""
        self._restore_initial_poses()
        self._running = False
        self._last_update_time = 0.0
        self._carry_tracking_space = False
        self._prev_left_primary_click = False

    # ------------------------------------------------------------------
    # Per-frame update
    # ------------------------------------------------------------------

    def update(self, left_ctrl, right_ctrl) -> None:
        """Applies one frame of locomotion from VR controller data.

        Args:
            left_ctrl: Left VR controller snapshot (or None).
            right_ctrl: Right VR controller snapshot (or None).
        """
        if not self._running or self._base_xform is None:
            return

        now = time.monotonic()
        dt = now - self._last_update_time if self._last_update_time > 0 else 1.0 / 60.0
        dt = min(dt, 0.1)
        self._last_update_time = now

        left_stick_x = self._get_input(left_ctrl, "thumbstick_x")
        left_stick_y = self._get_input(left_ctrl, "thumbstick_y")
        right_stick_x = self._get_input(right_ctrl, "thumbstick_x")
        right_primary = self._get_bool_input(right_ctrl, "primary_click")
        right_secondary = self._get_bool_input(right_ctrl, "secondary_click")
        left_primary = self._get_bool_input(left_ctrl, "primary_click")

        if left_primary and not self._prev_left_primary_click:
            if not self._tracking_space_prim_path:
                print("[Teleop][Locomotion] Carry Tracking Space toggle ignored: no tracking-space prim selected.")
            elif self._tracking_space_xform is None:
                print("[Teleop][Locomotion] Carry Tracking Space toggle ignored: tracking-space prim is unavailable.")
            else:
                self._carry_tracking_space = not self._carry_tracking_space
                state = "enabled" if self._carry_tracking_space else "disabled"
                print(f"[Teleop][Locomotion] Carry Tracking Space: {state}")
        self._prev_left_primary_click = left_primary

        left_stick_x = self._apply_deadzone(left_stick_x)
        left_stick_y = self._apply_deadzone(left_stick_y)
        right_stick_x = self._apply_deadzone(right_stick_x)

        if (
            left_stick_x == 0.0
            and left_stick_y == 0.0
            and right_stick_x == 0.0
            and not right_primary
            and not right_secondary
        ):
            return

        delta_yaw = -right_stick_x * self._angular_speed * dt
        delta_forward = left_stick_y * self._linear_speed * dt
        delta_lateral = left_stick_x * self._linear_speed * dt
        delta_up = (float(right_secondary) - float(right_primary)) * self._linear_speed * dt

        self._apply_movement(delta_forward, delta_lateral, delta_up, delta_yaw, self._carry_tracking_space)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_input(ctrl, attr: str) -> float:
        """Safely reads a float attribute from a VR controller snapshot."""
        if ctrl is None:
            return 0.0
        return getattr(ctrl.inputs, attr, 0.0)

    @staticmethod
    def _get_bool_input(ctrl, attr: str) -> bool:
        """Safely reads a bool attribute from a VR controller snapshot."""
        if ctrl is None:
            return False
        return bool(getattr(ctrl.inputs, attr, False))

    def _apply_deadzone(self, value: float) -> float:
        """Zeros out values within the deadzone, remaps the rest to [0, 1]."""
        if abs(value) < self.DEADZONE:
            return 0.0
        sign = 1.0 if value > 0 else -1.0
        return sign * (abs(value) - self.DEADZONE) / (1.0 - self.DEADZONE)

    def _refresh_tracking_space_xform(self) -> None:
        """Refresh the cached tracking-space wrapper if one is configured."""
        self._tracking_space_xform = None
        if not self._tracking_space_prim_path:
            return

        stage = get_current_stage()
        if not stage:
            return

        tracking_space_prim = stage.GetPrimAtPath(self._tracking_space_prim_path)
        if not tracking_space_prim or not tracking_space_prim.IsValid():
            return

        ctx = (
            Usd.EditContext(stage, self._edit_layer)
            if self._edit_layer and self._tracking_space_prim_path.startswith("/Teleop/")
            else nullcontext()
        )
        with ctx:
            try:
                self._tracking_space_xform = XformPrim(self._tracking_space_prim_path, reset_xform_op_properties=False)
            except Exception:
                try:
                    self._tracking_space_xform = XformPrim(
                        self._tracking_space_prim_path, reset_xform_op_properties=True
                    )
                except Exception:
                    pass

    def _cache_initial_poses(self) -> None:
        """Snapshots the current world poses of base and tracking-space prims."""
        if self._base_xform is not None:
            positions, orientations = self._base_xform.get_world_poses()
            self._initial_base_pose = (positions.numpy().copy(), orientations.numpy().copy())
        if self._tracking_space_xform is not None:
            positions, orientations = self._tracking_space_xform.get_world_poses()
            self._initial_tracking_space_pose = (positions.numpy().copy(), orientations.numpy().copy())

    def _restore_initial_poses(self) -> None:
        """Restores base and tracking-space prims to the poses cached on enable."""
        stage = get_current_stage()
        if self._initial_base_pose is not None and self._base_xform is not None:
            base_ctx = (
                Usd.EditContext(stage, self._edit_layer)
                if stage and self._edit_layer and self._prim_path.startswith("/Teleop/")
                else nullcontext()
            )
            with base_ctx:
                self._base_xform.set_world_poses(
                    positions=self._initial_base_pose[0],
                    orientations=self._initial_base_pose[1],
                )
        if self._initial_tracking_space_pose is not None and self._tracking_space_xform is not None:
            ts_ctx = (
                Usd.EditContext(stage, self._edit_layer)
                if stage and self._edit_layer and self._tracking_space_prim_path.startswith("/Teleop/")
                else nullcontext()
            )
            with ts_ctx:
                self._tracking_space_xform.set_world_poses(
                    positions=self._initial_tracking_space_pose[0],
                    orientations=self._initial_tracking_space_pose[1],
                )
        self._initial_base_pose = None
        self._initial_tracking_space_pose = None

    def _apply_movement(
        self,
        delta_forward: float,
        delta_lateral: float,
        delta_up: float,
        delta_yaw: float,
        carry_tracking_space: bool = False,
    ) -> None:
        """Applies incremental translation and yaw rotation to the target prim.

        Translation is in the prim's local frame (+X forward, -Y right).
        Vertical movement and yaw rotation are in world frame (Z-up).

        When ``carry_tracking_space`` is True, the tracking-space prim receives
        the same rigid transform as the base. This means turns rotate the
        tracking-space offset around the base pivot instead of only rotating the
        tracking-space prim in place.
        """
        if self._base_xform is None:
            return
        positions, orientations = self._base_xform.get_world_poses()
        pos_np = positions.numpy()[0]
        orient_wxyz = orientations.numpy()[0]
        pos = Gf.Vec3d(float(pos_np[0]), float(pos_np[1]), float(pos_np[2]))
        quat = Gf.Quatd(
            float(orient_wxyz[0]),
            float(orient_wxyz[1]),
            float(orient_wxyz[2]),
            float(orient_wxyz[3]),
        )

        rot = Gf.Rotation(quat)
        forward = rot.TransformDir(Gf.Vec3d(1, 0, 0))
        right = rot.TransformDir(Gf.Vec3d(0, -1, 0))

        dp = forward * delta_forward + right * delta_lateral + Gf.Vec3d(0, 0, delta_up)
        new_pos = Gf.Vec3d(pos[0] + dp[0], pos[1] + dp[1], pos[2] + dp[2])

        half = delta_yaw * 0.5
        yaw_q = Gf.Quatd(math.cos(half), 0.0, 0.0, math.sin(half))
        yaw_rot = Gf.Rotation(yaw_q)
        new_orient = yaw_q * quat

        stage = get_current_stage()
        base_ctx = (
            Usd.EditContext(stage, self._edit_layer)
            if stage and self._edit_layer and self._prim_path.startswith("/Teleop/")
            else nullcontext()
        )
        with base_ctx:
            self._base_xform.set_world_poses(
                positions=np.array([[new_pos[0], new_pos[1], new_pos[2]]], dtype=np.float32),
                orientations=np.array(
                    [[new_orient.GetReal(), *new_orient.GetImaginary()]],
                    dtype=np.float32,
                ),
            )

        if (
            carry_tracking_space
            and self._tracking_space_xform is not None
            and self._tracking_space_prim_path != self._prim_path
        ):
            o_positions, o_orientations = self._tracking_space_xform.get_world_poses()
            o_pos_np = o_positions.numpy()[0]
            o_orient_wxyz = o_orientations.numpy()[0]
            o_pos = Gf.Vec3d(float(o_pos_np[0]), float(o_pos_np[1]), float(o_pos_np[2]))
            o_quat = Gf.Quatd(
                float(o_orient_wxyz[0]),
                float(o_orient_wxyz[1]),
                float(o_orient_wxyz[2]),
                float(o_orient_wxyz[3]),
            )
            carried_offset = yaw_rot.TransformDir(o_pos - pos)
            new_o_pos = Gf.Vec3d(
                new_pos[0] + carried_offset[0],
                new_pos[1] + carried_offset[1],
                new_pos[2] + carried_offset[2],
            )
            new_o_orient = yaw_q * o_quat
            ts_ctx = (
                Usd.EditContext(stage, self._edit_layer)
                if stage and self._edit_layer and self._tracking_space_prim_path.startswith("/Teleop/")
                else nullcontext()
            )
            with ts_ctx:
                self._tracking_space_xform.set_world_poses(
                    positions=np.array([[new_o_pos[0], new_o_pos[1], new_o_pos[2]]], dtype=np.float32),
                    orientations=np.array(
                        [[new_o_orient.GetReal(), *new_o_orient.GetImaginary()]],
                        dtype=np.float32,
                    ),
                )
