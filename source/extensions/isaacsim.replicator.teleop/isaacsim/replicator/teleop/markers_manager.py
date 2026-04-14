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

"""Visual markers manager for teleop ground truth display.

Provides frame-based visual markers that display VR poses in the scene.
Left, right, and head markers are **children** of the TrackingOrigin
marker under ``/Teleop/Markers/TrackingOrigin/``, mirroring the CloudXR
play-space model where all tracked devices are relative to the origin.
Moving the origin in the viewport automatically moves all child markers
via USD transform inheritance.

In VR mode, child markers receive **origin-local** poses (coord-converted,
pre-tracking-space offset) while the origin marker receives the
tracking-space **world** pose.  USD composes the final world transforms.

In debug mode, markers are the authoritative pose source —
``get_marker_world_pose`` returns composed world poses via
``XformPrim.get_world_poses()``.

Marker prims are authored into an **anonymous USD session sublayer**
so they never pollute the user's stage, are not saved with the scene,
and are removed cleanly when the layer is dropped.  **All** writes
(creation, xformOp reset, scale, per-frame pose) go through a
``Usd.EditContext`` targeting this layer to prevent stale overrides
from leaking into the root layer.
"""

from contextlib import contextmanager

import omni.usd
from isaacsim.core.experimental.prims import XformPrim
from isaacsim.core.experimental.utils.stage import (
    add_reference_to_stage,
    get_current_stage,
)
from isaacsim.storage.native import get_assets_root_path
from pxr import Sdf, Usd


class MarkersManager:
    """Manages visual frame markers for VR pose ground truth visualization.

    The origin marker lives at ``/Teleop/Markers/TrackingOrigin`` and
    left, right, head markers are its USD children.  This mirrors the
    CloudXR play-space model and keeps the user's stage clean — markers
    are authored in an anonymous session sublayer, never saved, and
    removing the layer instantly removes all teleop prims.

    The origin marker receives **world-space** poses while child markers
    (left, right, head) receive **origin-local** poses.  USD composes
    the final world transforms via the parent-child hierarchy.
    """

    MARKERS_SCOPE = "/Teleop/Markers"
    ORIGIN_PATH = f"{MARKERS_SCOPE}/TrackingOrigin"
    MARKER_PATHS: dict[str, str] = {
        "origin": ORIGIN_PATH,
        "left": f"{ORIGIN_PATH}/Left",
        "right": f"{ORIGIN_PATH}/Right",
        "head": f"{ORIGIN_PATH}/Head",
    }
    DEFAULT_MARKER_POSES: dict[str, tuple[tuple[float, float, float], tuple[float, float, float, float]]] = {
        "origin": ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
        "left": ((0.0, 0.3, 1.0), (0.0, 0.0, 0.0, 1.0)),
        "right": ((0.0, -0.3, 1.0), (0.0, 0.0, 0.0, 1.0)),
        "head": ((0.0, 0.0, 1.5), (0.0, 0.0, 0.0, 1.0)),
    }

    FRAME_ASSET_PATH = "/Isaac/Props/UIElements/frame_prim.usd"
    DEFAULT_FRAME_SCALE = 0.05
    FRAME_CHILD_NAME = "FramePrim"

    def __init__(self):
        self._frame_scale: float = self.DEFAULT_FRAME_SCALE
        self._markers: dict[str, XformPrim] = {}
        self._assets_root_path: str | None = None
        self._layer: Sdf.Layer | None = None

    # ------------------------------------------------------------------
    # Anonymous session sublayer
    # ------------------------------------------------------------------

    def _ensure_layer(self, stage: Usd.Stage) -> Sdf.Layer:
        """Returns the anonymous teleop layer, creating it if needed.

        On first call also cleans up any stale ``/Teleop`` specs that may
        have leaked into the root layer from earlier sessions (before the
        anonymous-layer approach was introduced).
        """
        if self._layer is not None:
            return self._layer

        self._cleanup_root_layer_overs(stage)

        self._layer = Sdf.Layer.CreateAnonymous("anon_teleop_markers")
        session = stage.GetSessionLayer()
        session.subLayerPaths.append(self._layer.identifier)
        print(f"[Teleop][Markers] Created anonymous marker layer: {self._layer.identifier}")
        return self._layer

    @staticmethod
    def _cleanup_root_layer_overs(stage: Usd.Stage) -> None:
        """Removes stale /Teleop prim specs from the root layer if present."""
        root = stage.GetRootLayer()
        teleop_spec = root.GetPrimAtPath("/Teleop")
        if teleop_spec:
            del root.rootPrims["Teleop"]
            print("[Teleop][Markers] Cleaned up stale /Teleop specs from root layer.")

    def _remove_layer(self) -> None:
        """Removes the anonymous layer from the session, deleting all teleop prims."""
        if self._layer is None:
            return

        stage = get_current_stage()
        if stage:
            session = stage.GetSessionLayer()
            ident = self._layer.identifier
            if ident in session.subLayerPaths:
                session.subLayerPaths.remove(ident)

        self._layer = None

    @contextmanager
    def _edit_ctx(self):
        """Context manager that directs all USD writes to the anonymous layer.

        Yields the stage for convenience.  If no layer exists yet (markers
        not created), yields ``None`` so callers can bail out.
        """
        stage = get_current_stage()
        if stage and self._layer is not None:
            with Usd.EditContext(stage, self._layer):
                yield stage
        else:
            yield None

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    @property
    def has_active_markers(self) -> bool:
        """True if any tracking marker (left, right, or head) is active."""
        return bool(self._markers)

    @property
    def frame_scale(self) -> float:
        """Current uniform scale factor for frame markers."""
        return self._frame_scale

    @classmethod
    def get_default_marker_pose(cls, name: str) -> tuple[tuple[float, float, float], tuple[float, float, float, float]]:
        """Returns the default pose for a marker."""
        return cls.DEFAULT_MARKER_POSES.get(name, cls.DEFAULT_MARKER_POSES["origin"])

    def get_marker_world_pose(
        self, name: str
    ) -> tuple[tuple[float, float, float], tuple[float, float, float, float]] | None:
        """Returns the world-space (position, orientation) of a marker.

        Args:
            name: Marker identifier (e.g. ``"left"``, ``"right"``).

        Returns:
            ``((x, y, z), (qx, qy, qz, qw))`` or ``None`` if the
            marker is not active.
        """
        xform = self._markers.get(name)
        if xform is None:
            return None
        positions, orientations = xform.get_world_poses()
        p = positions.numpy()[0]
        o = orientations.numpy()[0]  # (w, x, y, z) from XformPrim
        return (float(p[0]), float(p[1]), float(p[2])), (float(o[1]), float(o[2]), float(o[3]), float(o[0]))

    def clear_cached_state(self) -> None:
        """Invalidates all cached XformPrim handles and removes the layer.

        Must be called when the USD stage is about to close so that stale
        prim references are not kept.
        """
        self._markers.clear()
        self._remove_layer()

    # ------------------------------------------------------------------
    # Scale
    # ------------------------------------------------------------------

    def set_frame_scale(self, scale: float) -> None:
        """Sets the frame visual scale and applies it to all existing markers.

        Scale is applied to each marker's ``FramePrim`` child, not to the
        marker Xform itself, so that child marker translations are not
        affected by the parent's scale.

        Args:
            scale: Uniform scale factor (e.g. 0.05).
        """
        self._frame_scale = max(0.001, scale)
        s = self._frame_scale
        with self._edit_ctx() as stage:
            if stage is None:
                return
            for name, xform in self._markers.items():
                path = self.MARKER_PATHS.get(name)
                if not path:
                    continue
                child_path = f"{path}/{self.FRAME_CHILD_NAME}"
                if stage.GetPrimAtPath(child_path).IsValid():
                    frame_xform = XformPrim(child_path, reset_xform_op_properties=True)
                    frame_xform.set_local_scales([[s, s, s]])

    # ------------------------------------------------------------------
    # Tracking-space helpers
    # ------------------------------------------------------------------

    def move_tracking_space_to(self, source_prim_path: str) -> bool:
        """Copies the world transform of the given prim to the tracking-space marker.

        This repositions the VR workspace so that the VR zero maps to the
        source prim's location in the scene.

        Args:
            source_prim_path: USD prim path whose world pose is copied.

        Returns:
            True if successful.
        """
        origin = self._markers.get("origin")
        if not origin:
            print("[Teleop][Markers] Tracking Space marker not active - create markers first.")
            return False

        stage = get_current_stage()
        if not stage:
            return False

        source = stage.GetPrimAtPath(source_prim_path)
        if not source or not source.IsValid():
            print(f"[Teleop][Markers] Source prim not found at '{source_prim_path}'.")
            return False

        src = XformPrim(source_prim_path)
        positions, orientations = src.get_world_poses()
        with self._edit_ctx() as stage:
            if stage is None:
                return False
            origin.set_world_poses(positions, orientations)
        print(f"[Teleop][Markers] Tracking Space marker moved to '{source_prim_path}'.")
        return True

    # ------------------------------------------------------------------
    # Marker lifecycle
    # ------------------------------------------------------------------

    def ensure_marker(self, name: str) -> tuple[bool, str]:
        """Creates a frame marker by name in the anonymous session layer.

        Child markers (left, right, head) automatically ensure their
        parent origin marker exists first.  Scale is applied to the
        ``FramePrim`` child so that the marker Xform keeps identity
        scale, avoiding transform-chain pollution for child markers.

        Args:
            name: Marker identifier (e.g. "left", "right", "origin").

        Returns:
            (success, message) tuple.
        """
        if name in self._markers:
            return True, f"Marker '{name}' already active"

        path = self.MARKER_PATHS.get(name)
        if not path:
            return False, f"Unknown marker name: '{name}'"

        if name != "origin" and "origin" not in self._markers:
            ok, msg = self.ensure_marker("origin")
            if not ok:
                return False, f"Cannot create '{name}': origin marker failed — {msg}"

        stage = get_current_stage()
        if not stage:
            return False, "No USD stage available"

        layer = self._ensure_layer(stage)

        with Usd.EditContext(stage, layer):
            stage.DefinePrim(path, "Xform")
            child_path = f"{path}/{self.FRAME_CHILD_NAME}"
            if not self._add_frame_reference(child_path):
                return False, f"Failed to create frame reference for '{name}'"

            xform = XformPrim(path, reset_xform_op_properties=True)
            frame_xform = XformPrim(child_path, reset_xform_op_properties=True)
            s = self._frame_scale
            frame_xform.set_local_scales([[s, s, s]])
            default_position, default_orientation = self.get_default_marker_pose(name)
            xform.set_local_poses(
                translations=[list(default_position)],
                orientations=[[default_orientation[3], *default_orientation[:3]]],
            )

        self._markers[name] = xform
        print(f"[Teleop][Markers] Created '{name}' marker at '{path}' (scale={self._frame_scale}).")
        return True, f"Created '{name}' marker"

    def remove_marker(self, name: str) -> bool:
        """Removes a single marker by name.

        Removing the origin also removes all child markers (left, right,
        head) since they are USD children of the origin prim.

        Args:
            name: Marker identifier (e.g. "left", "right", "origin").

        Returns:
            True if removed successfully.
        """
        path = self.MARKER_PATHS.get(name)
        if not path:
            return False

        self._clear_teleop_selection()

        if self._layer:
            spec = self._layer.GetPrimAtPath(path)
            if spec and spec.nameParent:
                del spec.nameParent.nameChildren[spec.name]
        else:
            stage = get_current_stage()
            if stage:
                stage.RemovePrim(path)

        self._markers.pop(name, None)
        if name == "origin":
            for child in ("left", "right", "head"):
                self._markers.pop(child, None)
        print(f"[Teleop][Markers] Removed '{name}' marker.")
        return True

    def remove_all_markers(self) -> bool:
        """Removes all markers by dropping the anonymous layer.

        This is faster and cleaner than deleting individual prims -
        removing the layer from the session stack instantly removes all
        teleop prims from the composed stage.

        Returns:
            True if removed successfully.
        """
        self._clear_teleop_selection()
        self._markers.clear()
        self._remove_layer()
        print("[Teleop][Markers] Removed all markers (layer dropped).")
        return True

    # ------------------------------------------------------------------
    # Per-frame transform updates
    # ------------------------------------------------------------------

    def update_marker_transform(
        self,
        name: str,
        position: tuple[float, float, float] | None = None,
        orientation: tuple[float, float, float, float] | None = None,
    ) -> None:
        """Updates a single marker's local pose.

        For the origin marker this is a world pose; for child markers
        (left, right, head) this is origin-local.

        Args:
            name: Marker identifier.
            position: (x, y, z) local position, or None to skip.
            orientation: (x, y, z, w) local quaternion, or None.
        """
        xform = self._markers.get(name)
        if not xform:
            return

        pos = position if position is not None else (0.0, 0.0, 0.0)

        with self._edit_ctx() as stage:
            if stage is None:
                return
            if orientation is not None:
                xform.set_local_poses(
                    translations=[list(pos)],
                    orientations=[[orientation[3], orientation[0], orientation[1], orientation[2]]],
                )
            else:
                xform.set_local_poses(translations=[list(pos)])

    def update_marker_transforms(
        self,
        left_position: tuple[float, float, float] | None = None,
        left_orientation: tuple[float, float, float, float] | None = None,
        right_position: tuple[float, float, float] | None = None,
        right_orientation: tuple[float, float, float, float] | None = None,
        head_position: tuple[float, float, float] | None = None,
        head_orientation: tuple[float, float, float, float] | None = None,
        origin_position: tuple[float, float, float] | None = None,
        origin_orientation: tuple[float, float, float, float] | None = None,
    ) -> None:
        """Updates all markers in one call.

        Origin receives a **world** pose; left/right/head receive
        **origin-local** poses.  USD composes the final world transforms
        through the parent-child hierarchy.  Origin is set first so that
        child world poses are immediately correct.
        """
        with self._edit_ctx() as stage:
            if stage is None:
                return
            if origin_position is not None:
                self._set_pose("origin", origin_position, origin_orientation)
            self._set_pose("left", left_position, left_orientation)
            self._set_pose("right", right_position, right_orientation)
            self._set_pose("head", head_position, head_orientation)

    def reset_marker_transform(self, name: str) -> None:
        """Resets a single marker to its default pose."""
        with self._edit_ctx() as stage:
            if stage is None:
                return
            self._set_default_pose(name)

    def reset_marker_transforms(self) -> None:
        """Resets all tracked markers to their default poses."""
        with self._edit_ctx() as stage:
            if stage is None:
                return
            for name in ("left", "right", "head"):
                self._set_default_pose(name)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clear_teleop_selection() -> None:
        """Clears the USD selection if any ``/Teleop`` prim (or descendant) is selected.

        This prevents Kit's Property panel from inspecting prims that are
        about to be removed, which would trigger async ``_delayed_dirty_handler``
        errors on the now-invalid prim references.
        """
        usd_ctx = omni.usd.get_context()
        if not usd_ctx:
            return
        selection = usd_ctx.get_selection()
        if not selection:
            return
        selected = selection.get_selected_prim_paths()
        if any(p.startswith("/Teleop") for p in selected):
            selection.clear_selected_prim_paths()

    def _set_pose(
        self,
        name: str,
        position: tuple[float, float, float] | None,
        orientation: tuple[float, float, float, float] | None,
    ) -> None:
        """Sets pose on a marker.  Must be called inside ``_edit_ctx``."""
        xform = self._markers.get(name)
        if not xform:
            return
        pos = position if position is not None else (0.0, 0.0, 0.0)
        if orientation is not None:
            xform.set_local_poses(
                translations=[list(pos)],
                orientations=[[orientation[3], orientation[0], orientation[1], orientation[2]]],
            )
        else:
            xform.set_local_poses(translations=[list(pos)])

    def _set_default_pose(self, name: str) -> None:
        """Sets a marker to its default pose. Must be called inside ``_edit_ctx``."""
        position, orientation = self.get_default_marker_pose(name)
        self._set_pose(name, position, orientation)

    def _add_frame_reference(self, path: str) -> bool:
        """Adds a frame_prim.usd reference at the given path.

        Must be called inside a ``Usd.EditContext`` targeting the anonymous
        layer so the reference is authored there, not on the root layer.

        Args:
            path: Prim path for the reference.

        Returns:
            True if the reference was added successfully.
        """
        if self._assets_root_path is None:
            self._assets_root_path = get_assets_root_path()

        if not self._assets_root_path:
            print("[Teleop][Markers] Could not resolve Isaac assets root path.")
            return False

        asset_path = self._assets_root_path + self.FRAME_ASSET_PATH
        prim = add_reference_to_stage(asset_path, path)
        if not prim or not prim.IsValid():
            print(f"[Teleop][Markers] Failed to add frame reference at '{path}'.")
            return False
        return True
