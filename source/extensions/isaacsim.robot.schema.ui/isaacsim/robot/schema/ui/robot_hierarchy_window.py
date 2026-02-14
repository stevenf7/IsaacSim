# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
"""Robot hierarchy window for joint tree visualization."""

__all__ = ["RobotHierarchyWindow"]

from typing import Any

import carb.eventdispatcher
import carb.settings
import omni.ui as ui
import omni.usd
from omni.kit.widget.stage import StageWidget
from pxr import Tf, Usd
from usd.schema.isaac import robot_schema

from .hierarchy_stage_delegate import HierarchyStageDelegate
from .scene import ConnectionInstance
from .selection_watch import SelectionWatch
from .utils import generate_robot_hierarchy_stage


class RobotHierarchyWindow(ui.Window):
    """Window displaying the robot joint hierarchy as a tree view.

    Provides a hierarchical view of robot joints where parent-child
    relationships are represented by the tree structure rather than
    USD prim hierarchy. Synchronizes selection with the main stage.

    Args:
        usd_context_name: Name of the USD context. Empty string uses the default.
    """

    def __init__(self, usd_context_name: str = "") -> None:
        self._usd_context = omni.usd.get_context(usd_context_name)
        self._visibility_changed_listener: Any | None = None
        self._selection_watch: SelectionWatch | None = None
        self._joint_connections: list[Any] = []
        self._original_stage_id = None
        self._current_joints: set[str] = set()
        self._tracked_robot_prim_paths: set[str] = set()
        self._stage_listener: Any | None = None

        super().__init__(
            "Robot Hierarchy",
            width=600,
            height=800,
            flags=ui.WINDOW_FLAGS_NO_SCROLLBAR,
            dockPreference=ui.DockPreference.RIGHT_TOP,
        )

        self.set_visibility_changed_fn(self._on_visibility_changed)
        self.deferred_dock_in("Stage", ui.DockPolicy.CURRENT_WINDOW_IS_ACTIVE)
        self.dock_order = 0

        self._settings = carb.settings.get_settings()
        self._columns: list[Any] = []
        self._columns_changed_subscription = None
        self._stage_widget: StageWidget | None = None

        with self.frame:
            self._stage_widget = StageWidget(
                None, columns_enabled=self._columns, stage_delegate=HierarchyStageDelegate()
            )

        self._stage_subscriptions: list[Any] | None = self._create_stage_subscriptions()
        self._selection_watch = SelectionWatch(usd_context=self._usd_context)
        self._stage_widget.set_selection_watch(self._selection_watch)
        self._on_stage_opened()

    def _create_stage_subscriptions(self) -> list[Any]:
        """Create event subscriptions for stage lifecycle events.

        Returns:
            List of event subscription handles.
        """
        return [
            carb.eventdispatcher.get_eventdispatcher().observe_event(
                observer_name="isaacsim.robot.schema.ui",
                event_name=self._usd_context.stage_event_name(event),
                on_event=handler,
            )
            for event, handler in (
                (omni.usd.StageEventType.OPENED, lambda _: self._on_stage_opened()),
                (omni.usd.StageEventType.CLOSING, lambda _: self._on_stage_closing()),
            )
        ]

    def _on_visibility_changed(self, visible: bool) -> None:
        """Handle window visibility changes.

        Args:
            visible: True if window became visible, False if hidden.
        """
        if self._visibility_changed_listener:
            self._visibility_changed_listener(visible)

        if not visible:
            self._destroy_selection_watch()
        else:
            self._selection_watch = SelectionWatch(usd_context=self._usd_context)

        if self._stage_widget:
            self._stage_widget.set_selection_watch(self._selection_watch)

    def _destroy_selection_watch(self) -> None:
        """Destroy the selection watch and clean up references."""
        if self._selection_watch:
            self._selection_watch.destroy()
            self._selection_watch = None

    def _destroy_stage_listener(self) -> None:
        """Destroy the stage listener for prim changes."""
        if self._stage_listener:
            self._stage_listener.Revoke()
            self._stage_listener = None

    def _create_stage_listener(self, stage: Usd.Stage | None) -> None:
        """Create a listener for stage prim changes.

        Args:
            stage: The USD stage to listen to.
        """
        self._destroy_stage_listener()
        if stage:
            self._stage_listener = Tf.Notice.Register(Usd.Notice.ObjectsChanged, self._on_objects_changed, stage)

    def _on_objects_changed(self, notice: Any, stage: Any) -> None:
        """Handle USD stage objects changed notice.

        Triggers a refresh when:
        - Prims are added or removed (resync)
        - Robot relationships change (links/joints)

        Does NOT trigger on camera, selection, or transform changes.

        Args:
            notice: The USD change notice.
            stage: The USD stage that changed.
        """
        resync_paths = notice.GetResyncedPaths()
        if resync_paths:
            current_robot_paths = self._collect_robot_prim_paths(stage)
            if current_robot_paths != self._tracked_robot_prim_paths:
                self._tracked_robot_prim_paths = current_robot_paths
                self.refresh_ui()
                return

        changed_paths = notice.GetChangedInfoOnlyPaths()
        if not changed_paths:
            return

        for changed_path in changed_paths:
            if self._is_robot_structure_change(changed_path):
                self.refresh_ui()
                return

    def _is_robot_structure_change(self, changed_path: Any) -> bool:
        """Check if a USD change affects robot hierarchy structure.

        Args:
            changed_path: The USD path change to inspect.

        Returns:
            True if the change affects robot relationships.
        """
        if not changed_path.IsPropertyPath():
            return False
        prim_path_str = str(changed_path.GetPrimPath())
        if prim_path_str not in self._tracked_robot_prim_paths:
            return False
        path_string = str(changed_path)
        if "." not in path_string:
            return False
        property_name = path_string.rsplit(".", 1)[-1]
        property_base = property_name.split(":", 1)[0]
        return property_base in {
            robot_schema.Relations.ROBOT_LINKS.name,
            robot_schema.Relations.ROBOT_JOINTS.name,
        }

    def _collect_robot_prim_paths(self, stage: Usd.Stage | None) -> set[str]:
        """Collect all robot-related prim paths from the stage.

        Args:
            stage: The USD stage to scan.

        Returns:
            Set of prim path strings for all robots and their links/joints.
        """
        if not stage:
            return set()

        paths = set()
        root_prim = stage.GetPrimAtPath("/")
        for prim in Usd.PrimRange(root_prim):
            if prim.HasAPI(robot_schema.Classes.ROBOT_API.value):
                paths.add(str(prim.GetPath()))
                robot_links_rel = prim.GetRelationship(robot_schema.Relations.ROBOT_LINKS.name)
                if robot_links_rel:
                    for target in robot_links_rel.GetTargets():
                        paths.add(str(target))
                robot_joints_rel = prim.GetRelationship(robot_schema.Relations.ROBOT_JOINTS.name)
                if robot_joints_rel:
                    for target in robot_joints_rel.GetTargets():
                        paths.add(str(target))
        return paths

    def set_visibility_changed_listener(self, listener: Any | None) -> None:
        """Set a callback for visibility changes.

        Args:
            listener: Callback function receiving visibility state as argument.

        Example:

        .. code-block:: python

            window.set_visibility_changed_listener(lambda visible: None)
        """
        self._visibility_changed_listener = listener

    def destroy(self) -> None:
        """Clean up resources before window destruction.

        Releases all subscriptions and references for proper hot reloading.

        Example:

        .. code-block:: python

            window.destroy()
        """
        self._visibility_changed_listener = None
        self._destroy_stage_listener()
        if self._selection_watch:
            self._selection_watch._tree_view = None
            self._selection_watch._events = None
            self._selection_watch._stage_event_sub = None
            self._selection_watch = None
        if self._stage_widget:
            self._stage_widget.destroy()
            self._stage_widget = None
        self._stage_subscriptions = None
        self._settings = None
        self._columns_changed_subscription = None
        super().destroy()

    def refresh_ui(self) -> None:
        """Refresh the hierarchy view from the current stage.

        Regenerates the hierarchy stage and updates the widget.
        Skips update if joints haven't changed to avoid redundant work.

        Example:

        .. code-block:: python

            window.refresh_ui()
        """
        hierarchy_stage, path_map, joint_connections = generate_robot_hierarchy_stage()

        current_joints = self._extract_joint_paths(joint_connections)
        if current_joints and self._current_joints == current_joints:
            return

        self._current_joints = current_joints
        if self._stage_widget is None:
            return
        self._stage_widget.open_stage(hierarchy_stage)
        if self._selection_watch:
            self._selection_watch.update_path_map(path_map)
        ConnectionInstance.get_instance().set_joint_connections(joint_connections)

    def _extract_joint_paths(self, joint_connections: list[Any]) -> set[str]:
        """Extract joint paths as a set for comparison.

        Args:
            joint_connections: List of connection items.

        Returns:
            Set of joint prim path strings.
        """
        return {joint.joint_prim.GetPath().pathString for joint in joint_connections}

    def _on_stage_opened(self) -> None:
        """Handle stage open event.

        Creates the stage listener and refreshes the hierarchy UI.
        """
        stage = self._usd_context.get_stage()
        self._original_stage_id = self._usd_context.get_stage_id()
        self._tracked_robot_prim_paths = self._collect_robot_prim_paths(stage)
        self._create_stage_listener(stage)
        self.refresh_ui()

    def _on_stage_closing(self) -> None:
        """Handle stage closing event.

        Clears the hierarchy view, resets connections, and removes the stage listener.
        """
        self._destroy_stage_listener()
        self._tracked_robot_prim_paths.clear()
        self._current_joints.clear()
        if self._stage_widget:
            self._stage_widget.open_stage(None)
        if self._selection_watch:
            self._selection_watch.update_path_map(None)
        ConnectionInstance.get_instance().set_joint_connections([])

    def get_widget(self) -> StageWidget | None:
        """Get the underlying stage widget.

        Returns:
            The widget instance used by this window.

        Example:

        .. code-block:: python

            stage_widget = window.get_widget()
        """
        return self._stage_widget
