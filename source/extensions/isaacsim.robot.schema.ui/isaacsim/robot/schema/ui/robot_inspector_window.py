# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
"""Robot Inspector window for joint tree visualization and component masking."""

__all__ = ["RobotInspectorWindow"]

import asyncio
from pathlib import Path
from typing import Any

import carb.eventdispatcher
import carb.settings
import omni.kit.app
import omni.ui as ui
import omni.usd
from omni.kit.widget.stage import StageWidget
from pxr import Sdf, Tf, Usd
from usd.schema.isaac import robot_schema

from .inspector_stage_delegate import InspectorStageDelegate
from .masking_state import MaskingState
from .scene import ConnectionInstance
from .selection_watch import SelectionWatch
from .utils import HierarchyMode, PathMap, generate_robot_hierarchy_stage


class RobotInspectorWindow(ui.Window):
    """Robot Inspector window: robot structure view with component inspection and masking.

    Provides a configurable view of the robot's links and joints (flat, linked,
    or MuJoCo-style tree), with per-component deactivation and bypass controls.
    Synchronizes selection with the main stage.

    Args:
        usd_context_name: Name of the USD context. Empty string uses the default.
    """

    SETTING_HIERARCHY_MODE = "/persistent/exts/isaacsim.robot.schema.ui/hierarchyMode"

    _MODE_LABELS = ("Flat", "Tree", "MuJoCo")
    _MODE_VALUES = (HierarchyMode.FLAT, HierarchyMode.LINKED, HierarchyMode.MUJOCO)
    _MODE_IDENTIFIERS = (
        "robot_inspector_mode_flat",
        "robot_inspector_mode_tree",
        "robot_inspector_mode_mujoco",
    )
    _MODE_TOOLTIPS = (
        "Flat List: all links under a Links scope, all joints under a Joints scope",
        "Tree: parent link → joint → child link chain",
        "MuJoCo: link-rooted tree with joint-to-parent as last child of each link",
    )

    _MODE_NAME_MAP = {m.name: m for m in HierarchyMode}

    def __init__(self, usd_context_name: str = "") -> None:
        self._usd_context = omni.usd.get_context(usd_context_name)
        self._visibility_changed_listener: Any | None = None
        self._selection_watch: SelectionWatch | None = None
        self._joint_connections: list[Any] = []
        self._original_stage_id = None
        self._current_joints: set[str] = set()
        self._current_hierarchy_mode: HierarchyMode | None = None
        self._tracked_robot_prim_paths: set[str] = set()
        self._stage_listener: Any | None = None
        self._hierarchy_stage: Usd.Stage | None = None
        self._path_map: PathMap | None = None
        self._hierarchy_mode: HierarchyMode = self._load_mode_preference()
        self._view_mode_collection: Any = None
        self._option_hovered: list[bool] = []
        self._option_frames: list[Any] = []
        self._deferred_sync_task: asyncio.Task | None = None

        super().__init__(
            "Robot Inspector",
            width=600,
            height=800,
            flags=ui.WINDOW_FLAGS_NO_SCROLLBAR,
            dockPreference=ui.DockPreference.RIGHT_TOP,
        )

        self.set_visibility_changed_fn(self._on_visibility_changed)
        self.deferred_dock_in("Stage", ui.DockPolicy.CURRENT_WINDOW_IS_ACTIVE)
        self.dock_order = 0

        self._settings = carb.settings.get_settings()
        self._columns_changed_subscription = None
        self._stage_widget: StageWidget | None = None

        with self.frame:
            with ui.VStack(spacing=0):
                self._build_mode_toolbar()
                self._stage_widget = StageWidget(
                    None,
                    columns_enabled=["Deactivate", "Bypass", "Anchor"],
                    stage_delegate=InspectorStageDelegate(),
                )

        self._stage_subscriptions: list[Any] | None = self._create_stage_subscriptions()
        self._selection_watch = SelectionWatch(usd_context=self._usd_context)
        self._stage_widget.set_selection_watch(self._selection_watch)

        self._masking_state: MaskingState | None = MaskingState.get_instance()
        self._masking_state.subscribe_changed(self._on_masking_changed)

        self._on_stage_opened()

    def _get_schema_ui_icons_dir(self) -> str:
        """Resolve this extension's data/icons directory for view-mode radio icons.

        Returns:
            Absolute path string to the icons directory, or an empty string on failure.
        """
        try:
            ext_mgr = omni.kit.app.get_app().get_extension_manager()
            ext_path = ext_mgr.get_extension_path_by_module("isaacsim.robot.schema.ui")
            if ext_path:
                return str(Path(ext_path) / "data" / "icons")
        except Exception:
            pass
        return ""

    def _build_mode_toolbar(self) -> None:
        """Build the view-mode radio group (Flat / Tree / MuJoCo) above the stage widget.

        Each option is a Frame (row) with build_fn so the radio icon reflects both
        selection and hover over the entire row (same hitbox for click and hover).
        """
        icons_dir = self._get_schema_ui_icons_dir()
        off_url = f"{icons_dir}/radio_off.svg" if icons_dir else ""
        on_url = f"{icons_dir}/radio_on.svg" if icons_dir else ""
        on_hover_url = f"{icons_dir}/radio_on_hover.svg" if icons_dir else ""

        self._view_mode_collection = ui.RadioCollection()
        initial_index = self._MODE_VALUES.index(self._hierarchy_mode)
        self._view_mode_collection.model.set_value(initial_index)
        self._option_hovered = [False, False, False]
        self._option_frames = []
        self._option_hover_overlays: list[ui.Image | None] = []

        with ui.HStack(height=26, spacing=2, identifier="robot_inspector_mode_toolbar"):
            ui.Label(
                "Show Robot View:",
                width=0,
                style={"margin_width": 4},
                tooltip="How to display the robot hierarchy: Flat list, Tree (link–joint–link), or MuJoCo-style.",
                identifier="robot_inspector_view_label",
            )
            with ui.HStack():
                for i, (label, tooltip, frame_id) in enumerate(
                    zip(self._MODE_LABELS, self._MODE_TOOLTIPS, self._MODE_IDENTIFIERS)
                ):
                    frame = ui.Frame(
                        width=0,
                        height=26,
                        mouse_pressed_fn=lambda x, y, m, w, idx=i: self._on_view_mode_option_clicked(idx),
                        mouse_hovered_fn=lambda hovered, idx=i: self._on_view_mode_option_hovered(idx, hovered),
                        tooltip=tooltip,
                        identifier=frame_id,
                    )
                    ui.Spacer(width=12)
                    frame.set_build_fn(
                        lambda idx=i, lbl=label, tp=tooltip, fid=frame_id: self._build_view_mode_option(
                            idx, lbl, tp, off_url, on_url, on_hover_url, fid
                        )
                    )
                    self._option_frames.append(frame)
            ui.Spacer()

        self._view_mode_collection.model.add_value_changed_fn(self._on_view_mode_changed)

    def _build_view_mode_option(
        self, index: int, label: str, tooltip: str, off_url: str, on_url: str, on_hover_url: str, identifier: str = ""
    ) -> None:
        """Build one option row: ZStack with base icon+label and a hover overlay (visibility only, no rebuild).

        Args:
            index: Zero-based index of this option in the radio collection.
            label: Display text for the option.
            tooltip: Tooltip string shown on hover.
            off_url: URL of the unselected radio icon.
            on_url: URL of the selected radio icon.
            on_hover_url: URL of the hover-state radio icon.
            identifier: UI identifier prefix for the widgets in this option.
        """
        selected = (
            self._view_mode_collection is not None and self._view_mode_collection.model.get_value_as_int() == index
        )
        hovered = index < len(self._option_hovered) and self._option_hovered[index]
        base_icon_url = on_url if selected else off_url
        show_hover_overlay = hovered and not selected

        with ui.ZStack():
            with ui.HStack(width=0, spacing=4):
                with ui.VStack():
                    ui.Spacer()
                    ui.Image(
                        base_icon_url or "",
                        width=20,
                        height=20,
                        identifier=f"{identifier}_icon" if identifier else "",
                    )
                    ui.Spacer()
                with ui.VStack(height=26):
                    ui.Spacer()
                    ui.Label(
                        label,
                        width=0,
                        height=26,
                        tooltip=tooltip if tooltip else None,
                        identifier=f"{identifier}_label" if identifier else "",
                    )
                    ui.Spacer()
            with ui.HStack(width=0, spacing=4):
                with ui.VStack(height=26):
                    ui.Spacer()
                    hover_img = ui.Image(on_hover_url or "", width=20, height=20)
                    ui.Spacer()
                ui.Spacer(width=4)
            while len(self._option_hover_overlays) <= index:
                self._option_hover_overlays.append(None)
            self._option_hover_overlays[index] = hover_img
            hover_img.visible = show_hover_overlay

    def _on_view_mode_option_hovered(self, index: int, hovered: bool) -> None:
        """Show/hide the hover overlay for the option row (no rebuild).

        Args:
            index: Zero-based index of the option being hovered.
            hovered: True when the pointer enters the row, False when it leaves.
        """
        if index >= len(self._option_hovered) or self._option_hovered[index] == hovered:
            return
        self._option_hovered[index] = hovered
        overlay = self._option_hover_overlays[index] if index < len(self._option_hover_overlays) else None
        if overlay is not None:
            selected = (
                self._view_mode_collection is not None and self._view_mode_collection.model.get_value_as_int() == index
            )
            overlay.visible = hovered and not selected

    def _on_view_mode_option_clicked(self, index: int) -> None:
        """Sync radio selection when user clicks anywhere on the option (radio + label area).

        Args:
            index: Zero-based index of the clicked option.
        """
        if self._view_mode_collection and self._view_mode_collection.model.get_value_as_int() != index:
            self._view_mode_collection.model.set_value(index)

    def _on_view_mode_changed(self, model: Any) -> None:
        """Apply the selected view mode when the radio collection changes.

        Args:
            model: The radio collection model that fired the change event.
        """
        index = model.get_value_as_int()
        if 0 <= index < len(self._MODE_VALUES):
            self._set_hierarchy_mode(self._MODE_VALUES[index])
        for frame in self._option_frames:
            if frame is not None:
                frame.rebuild()

    def _load_mode_preference(self) -> HierarchyMode:
        """Read the persisted hierarchy mode from Carbonite settings.

        Returns:
            Stored `HierarchyMode` value, or `HierarchyMode.LINKED` if the
            setting is absent or unrecognized.
        """
        stored = carb.settings.get_settings().get(self.SETTING_HIERARCHY_MODE)
        if stored and stored in self._MODE_NAME_MAP:
            return self._MODE_NAME_MAP[stored]
        return HierarchyMode.LINKED

    def _save_mode_preference(self) -> None:
        """Write the current hierarchy mode to Carbonite persistent settings."""
        carb.settings.get_settings().set(self.SETTING_HIERARCHY_MODE, self._hierarchy_mode.name)

    def _set_hierarchy_mode(self, mode: HierarchyMode) -> None:
        """Switch the hierarchy display mode and refresh the panel.

        Args:
            mode: The new display mode to activate.
        """
        if mode == self._hierarchy_mode:
            return
        self._hierarchy_mode = mode
        self._save_mode_preference()
        if self._view_mode_collection:
            idx = self._MODE_VALUES.index(mode)
            if self._view_mode_collection.model.get_value_as_int() != idx:
                self._view_mode_collection.model.set_value(idx)
        self._current_joints = set()
        self.refresh_ui()

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
        """Check if a USD change affects robot structure (links/joints).

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
        return property_name in {
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
        if self._deferred_sync_task and not self._deferred_sync_task.done():
            self._deferred_sync_task.cancel()
        self._deferred_sync_task = None
        self._visibility_changed_listener = None
        self._view_mode_collection = None
        self._option_hovered = []
        self._option_frames = []
        self._option_hover_overlays = []
        self._destroy_stage_listener()
        if self._masking_state:
            self._masking_state.unsubscribe_changed(self._on_masking_changed)
            self._masking_state.path_map = None
        self._masking_state = None
        self._hierarchy_stage = None
        self._path_map = None
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
        """Refresh the inspector view from the current stage.

        Regenerates the hierarchy stage and updates the widget.
        Skips update if joints haven't changed to avoid redundant work.
        Re-applies masking icons after regeneration.

        Example:

        .. code-block:: python

            window.refresh_ui()
        """
        hierarchy_stage, path_map, joint_connections = generate_robot_hierarchy_stage(self._hierarchy_mode)

        current_joints = self._extract_joint_paths(joint_connections)
        mode_unchanged = self._hierarchy_mode == self._current_hierarchy_mode
        if current_joints and self._current_joints == current_joints and mode_unchanged:
            return

        self._current_joints = current_joints
        self._current_hierarchy_mode = self._hierarchy_mode
        self._hierarchy_stage = hierarchy_stage
        self._path_map = path_map
        if self._masking_state:
            self._masking_state.path_map = path_map

        if self._stage_widget is None:
            return

        # Preserve current selection before opening new stage; open_stage clears the tree
        # and the widget pushes empty selection to USD, wiping the selection.
        usd_context = omni.usd.get_context()
        preserved_paths = list(usd_context.get_selection().get_selected_prim_paths())

        self._apply_masking_icons()
        self._stage_widget.open_stage(hierarchy_stage)

        if self._selection_watch:
            self._selection_watch.update_path_map(path_map)

            async def _deferred_sync() -> None:
                await omni.kit.app.get_app().next_update_async()
                if self._selection_watch is None:
                    return
                if preserved_paths and usd_context:
                    usd_context.get_selection().set_selected_prim_paths(preserved_paths, True)
                if self._selection_watch:
                    self._selection_watch.sync_from_stage()

            self._deferred_sync_task = asyncio.ensure_future(_deferred_sync())
        ConnectionInstance.get_instance().set_joint_connections(joint_connections)

    def _extract_joint_paths(self, joint_connections: list[Any]) -> set[str]:
        """Extract joint paths as a set for comparison.

        Args:
            joint_connections: List of connection items.

        Returns:
            Set of joint prim path strings.
        """
        return {joint.joint_prim.GetPath().pathString for joint in joint_connections}

    def _apply_masking_icons(self) -> None:
        """Set customData on hierarchy prims to signal deactivation state.

        The ``isaacsim:deactivated`` custom data key is read by the icon
        override callback registered in the extension to swap the prim icon
        to its disabled variant.
        """
        if not self._hierarchy_stage or not self._path_map or not self._masking_state:
            return

        deactivated = self._masking_state.get_deactivated_paths()

        root_prim = self._hierarchy_stage.GetPrimAtPath("/")
        if not root_prim:
            return

        for prim in Usd.PrimRange(root_prim):
            original_path = self._path_map.get_original_path(prim.GetPath())
            if not original_path:
                continue

            is_deactivated = original_path.pathString in deactivated
            prim.SetCustomDataByKey("isaacsim:deactivated", is_deactivated)

    def _on_masking_changed(self) -> None:
        """Handle masking state changes from the MaskingState singleton.

        Sets customData on hierarchy prims and forces the tree view to
        rebuild every cached item so both the Name column icons and the
        Deactivate column reflect the new state. Uses ``refresh_item_names``
        which calls ``_item_changed(item)`` per item, preserving expansion.

        Selection is blocked during the refresh because ``refresh_item_names``
        may trigger transient widget-selection callbacks that would push a
        stale selection to USD.  After the refresh the tree is re-synced from
        the (unchanged) USD selection.
        """
        self._apply_masking_icons()
        if self._stage_widget:
            model = self._stage_widget.get_model()
            if model:
                if self._selection_watch:
                    self._selection_watch._is_in_selection = True
                try:
                    model.refresh_item_names()
                finally:
                    if self._selection_watch:
                        self._selection_watch._is_in_selection = False
                        self._selection_watch.sync_from_stage()

    def _on_stage_opened(self) -> None:
        """Handle stage open event.

        Creates the stage listener and refreshes the inspector UI.
        """
        stage = self._usd_context.get_stage()
        self._original_stage_id = self._usd_context.get_stage_id()
        self._tracked_robot_prim_paths = self._collect_robot_prim_paths(stage)
        self._create_stage_listener(stage)
        self.refresh_ui()

    def _on_stage_closing(self) -> None:
        """Handle stage closing event.

        Clears the inspector view, resets connections, masking state, and removes
        the stage listener.
        """
        self._destroy_stage_listener()
        self._tracked_robot_prim_paths.clear()
        self._current_joints.clear()
        self._hierarchy_stage = None
        self._path_map = None
        if self._masking_state:
            self._masking_state.clear()
            self._masking_state.path_map = None
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
