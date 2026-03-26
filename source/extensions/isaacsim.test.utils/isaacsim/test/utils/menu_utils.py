# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Utilities for navigating and testing UI menus in Isaac Sim."""


import carb
import omni.kit.app
import omni.kit.ui_test as ui_test
from omni import ui
from omni.kit.ui_test import Vec2, emulate_mouse_move, get_menubar, wait_n_updates

# Maximum number of frames to poll when waiting for a widget to become
# findable, enabled, or for a submenu to become visible after clicking.
_DEFAULT_MAX_WAIT_FRAMES = 100


async def find_widget_with_retry(query: str, max_frames: int = _DEFAULT_MAX_WAIT_FRAMES, parent=None):
    """Poll ``ui_test.find`` until the widget is found or *max_frames* is exceeded.

    This is useful when a UI element may not be immediately available after a
    menu click or navigation action.  Instead of a fixed ``human_delay``, this
    function actively polls each frame so the test proceeds as soon as the
    widget appears.

    Args:
        query: The widget query string (same syntax as ``omni.kit.ui_test.find``).
        max_frames: Maximum number of app-update frames to wait before giving up.
        parent: Optional parent widget to search within.  When provided,
            ``parent.find(query)`` is used instead of ``ui_test.find(query)``.

    Returns:
        The found widget reference.

    Raises:
        TimeoutError: If the widget is not found within *max_frames*.
    """
    for frame in range(max_frames):
        result = parent.find(query) if parent is not None else ui_test.find(query)
        if result is not None:
            if frame > 0:
                carb.log_info(f"[find_widget_with_retry] find('{query}') succeeded after {frame} extra frame(s)")
            return result
        await omni.kit.app.get_app().next_update_async()

    raise TimeoutError(f"Widget '{query}' not found after {max_frames} frames")


async def wait_for_widget_enabled(widget, max_frames: int = _DEFAULT_MAX_WAIT_FRAMES) -> bool:
    """Poll until ``widget.widget.enabled`` becomes True.

    Args:
        widget: A ``WidgetRef`` returned by ``ui_test.find`` or
            :func:`find_widget_with_retry`.
        max_frames: Maximum number of app-update frames to wait.

    Returns:
        True if the widget became enabled within *max_frames*, False otherwise.
    """
    for frame in range(max_frames):
        if widget.widget.enabled:
            if frame > 0:
                carb.log_info(f"[wait_for_widget_enabled] widget became enabled after {frame} extra frame(s)")
            return True
        await omni.kit.app.get_app().next_update_async()
    return False


async def find_enabled_widget_with_retry(query: str, max_frames: int = _DEFAULT_MAX_WAIT_FRAMES, parent=None):
    """Poll ``ui_test.find`` until the widget is found **and** enabled.

    Combines :func:`find_widget_with_retry` with an enabled check in a single
    polling loop.  This avoids the common two-step pattern of finding a widget
    and then waiting for it to become enabled in a separate loop.

    Args:
        query: The widget query string (same syntax as ``omni.kit.ui_test.find``).
        max_frames: Maximum number of app-update frames to wait before giving up.
        parent: Optional parent widget to search within.

    Returns:
        The found and enabled widget reference.

    Raises:
        TimeoutError: If the widget is not found and enabled within *max_frames*.
    """
    for frame in range(max_frames):
        result = parent.find(query) if parent is not None else ui_test.find(query)
        if result is not None and result.widget.enabled:
            if frame > 0:
                carb.log_info(
                    f"[find_enabled_widget_with_retry] find('{query}') succeeded after {frame} extra frame(s)"
                )
            return result
        await omni.kit.app.get_app().next_update_async()

    raise TimeoutError(f"Widget '{query}' not found or not enabled after {max_frames} frames")


async def perform_widget_action(
    query: str,
    action: str = "click",
    text: str = "",
    max_frames: int = _DEFAULT_MAX_WAIT_FRAMES,
) -> dict:
    """Find a UI widget and perform an action on it.

    Combines :func:`find_widget_with_retry` with action dispatch so callers
    do not need to handle the find/act pattern themselves.

    Args:
        query: Widget query string (same syntax as ``omni.kit.ui_test.find``).
        action: Action to perform — one of ``click``, ``double_click``,
            ``right_click``, ``type``, ``read``.
        text: Text to type; only used when *action* is ``"type"``.
        max_frames: Maximum frames to poll for the widget to appear.

    Returns:
        For ``action="read"``: dict of widget properties (type, visible,
        enabled, width, height, and optionally text/value).
        For all other actions: empty dict.

    Raises:
        TimeoutError: If the widget is not found within *max_frames*.
        ValueError: If *action* is not one of the supported values.

    Example:

    .. code-block:: python

        >>> from isaacsim.test.utils import perform_widget_action
        >>>
        >>> await perform_widget_action("Load")
        >>> await perform_widget_action("Search", action="type", text="franka")
        >>> info = await perform_widget_action("Play", action="read")
        >>> print(info)
        {'type': 'Button', 'visible': True, 'enabled': True, ...}
    """
    widget = await find_widget_with_retry(query, max_frames=max_frames)

    if action == "click":
        await widget.click()
    elif action == "double_click":
        await widget.double_click()
    elif action == "right_click":
        await widget.right_click()
    elif action == "type":
        await widget.input(text)
    elif action == "read":
        w = widget.widget
        info: dict = {
            "type": type(w).__name__,
            "visible": getattr(w, "visible", None),
            "enabled": getattr(w, "enabled", None),
            "width": getattr(w, "width", None),
            "height": getattr(w, "height", None),
        }
        if hasattr(w, "text"):
            info["text"] = w.text
        if hasattr(w, "model") and w.model:
            try:
                info["value"] = w.model.get_value_as_string()
            except Exception:
                pass
        return info
    else:
        raise ValueError(f"Unknown action '{action}'. Use: click, double_click, right_click, type, read")

    return {}


async def _wait_for_menu_item(parent_widget, menu_name: str, max_frames: int = _DEFAULT_MAX_WAIT_FRAMES):
    """Poll until ``parent_widget.find_menu(menu_name)`` returns a non-None result.

    Args:
        parent_widget: The parent ``MenuRef`` to search within.
        menu_name: The menu item text to search for.
        max_frames: Maximum frames to poll before giving up.

    Returns:
        The found ``MenuRef``, or ``None`` if not found within *max_frames*.
    """
    for frame in range(max_frames):
        result = parent_widget.find_menu(menu_name)
        if result is not None:
            if frame > 0:
                carb.log_info(
                    f"[menu_click_with_retry] find_menu('{menu_name}') " f"succeeded after {frame} extra frame(s)"
                )
            return result
        await omni.kit.app.get_app().next_update_async()
    return None


async def _wait_for_shown(menu_widget, menu_name: str, max_frames: int = _DEFAULT_MAX_WAIT_FRAMES) -> bool:
    """Poll until ``menu_widget.widget.shown`` becomes True.

    Args:
        menu_widget: The ``MenuRef`` whose ``shown`` state to check.
        menu_name: Menu name (used for logging).
        max_frames: Maximum frames to poll before giving up.

    Returns:
        True if the menu became shown, False if timed out.
    """
    for frame in range(max_frames):
        if menu_widget.widget.shown:
            if frame > 0:
                carb.log_info(f"[menu_click_with_retry] '{menu_name}' became shown " f"after {frame} extra frame(s)")
            return True
        await omni.kit.app.get_app().next_update_async()
    return False


async def _navigate_menu(menu_path: str, human_delay_speed: int = 10) -> bool:
    """Navigate through a menu hierarchy step-by-step with polling.

    Unlike ``omni.kit.ui_test.menu_click``, this function polls at each step
    rather than waiting a fixed number of frames.  This avoids both the
    ``AttributeError`` (from ``find_menu`` returning ``None``) and the
    ``carb.log_error`` (from a submenu not becoming visible in time).

    Args:
        menu_path: Full menu path separated by ``/``.
        human_delay_speed: Frames to wait between mouse interactions for
            natural-feeling timing.

    Returns:
        True if the full path was navigated and clicked successfully,
        False otherwise.
    """
    import omni.appwindow

    menu_widget = get_menubar()
    app_win = omni.appwindow.get_default_app_window()

    # Move mouse away from menus first (mirrors menu_click behaviour).
    await emulate_mouse_move(Vec2(app_win.get_size().x - 10, app_win.get_size().y - 10))
    await wait_n_updates(human_delay_speed)

    segments = menu_path.split("/")
    for idx, menu_name in enumerate(segments):
        # Poll until the menu item is findable in the widget tree.
        child = await _wait_for_menu_item(menu_widget, menu_name)
        if child is None:
            carb.log_info(f"[menu_click_with_retry] could not find menu item " f"'{menu_name}' in '{menu_path}'")
            return False

        menu_widget = child

        # Move mouse to the menu item.
        menu_pos = menu_widget.center
        if idx == 0:
            menu_pos += Vec2(10 * ui.Workspace.get_dpi_scale(), 5 * ui.Workspace.get_dpi_scale())
        await emulate_mouse_move(menu_pos)
        await wait_n_updates(human_delay_speed)

        # If this is a submenu (ui.Menu), click to open and poll for shown.
        if isinstance(menu_widget.widget, ui.Menu):
            if not menu_widget.widget.shown:
                await menu_widget.click()
            elif menu_widget.widget.has_triggered_fn():
                menu_widget.widget.call_triggered_fn()

            if not await _wait_for_shown(menu_widget, menu_name):
                carb.log_info(
                    f"[menu_click_with_retry] submenu '{menu_name}' did " f"not become shown in '{menu_path}'"
                )
                return False
        else:
            # Leaf menu item -- click it.
            await menu_widget.click()
            await wait_n_updates(human_delay_speed)

    await wait_n_updates(human_delay_speed)
    return True


async def menu_click_with_retry(
    menu_path: str, delays: list[int] = None, window_name: str = None, wait_n_frames: int = 10
):
    """Click a menu item with retry at different delay speeds.

    First attempts a direct programmatic click via ``omni.kit.ui_test.menu_click``
    which works in both windowed and headless (``--no-window``) modes.  If that
    fails (e.g. due to slow submenus), falls back to step-by-step mouse-emulation
    navigation via :func:`_navigate_menu` with increasing delays.

    Args:
        menu_path: The menu path to click (e.g., "Create/Sensors/Contact Sensor").
        delays: List of delay values (in frames) to use for ``human_delay_speed``
            on each fallback attempt.
        window_name: Optional window name to check for after clicking.
            If provided, the function returns early when the window is found
            and returns the window widget.
        wait_n_frames: Number of frames to wait after a successful click when
            ``window_name`` is not provided.

    Returns:
        The found window widget if window_name is provided and found, else None.

    Example:

    .. code-block:: python

        >>> from isaacsim.test.utils import menu_click_with_retry
        >>>
        >>> # Simple menu click
        >>> await menu_click_with_retry("Create/Sensors/Contact Sensor")
        >>>
        >>> # Menu click that waits for a window to appear
        >>> window = await menu_click_with_retry(
        ...     "Tools/Robotics/OmniGraph Controllers/Differential Controller",
        ...     window_name="Differential Controller"
        ... )
    """
    delays = delays or [5, 10, 20]

    carb.log_info(
        f"[menu_click_with_retry] starting: menu_path='{menu_path}', " f"window_name={window_name!r}, delays={delays}"
    )

    # --- Primary path: direct programmatic menu click (works headless) ---
    try:
        await ui_test.menu_click(menu_path, human_delay_speed=3)
        for _ in range(wait_n_frames):
            await omni.kit.app.get_app().next_update_async()

        if window_name:
            if (window := ui_test.find(window_name)) is not None:
                carb.log_info(f"[menu_click_with_retry] window '{window_name}' found via ui_test.menu_click")
                return window
            carb.log_info(
                f"[menu_click_with_retry] ui_test.menu_click succeeded but window '{window_name}' not found, "
                f"falling back to _navigate_menu"
            )
        else:
            carb.log_info(f"[menu_click_with_retry] succeeded via ui_test.menu_click for '{menu_path}'")
            return None
    except Exception as e:
        carb.log_info(f"[menu_click_with_retry] ui_test.menu_click failed for '{menu_path}': {e}")

    # --- Fallback: step-by-step mouse-emulation navigation ---
    for i, delay in enumerate(delays):
        carb.log_info(
            f"[menu_click_with_retry] fallback attempt {i + 1}/{len(delays)} "
            f"(human_delay_speed={delay}) for '{menu_path}'"
        )

        success = await _navigate_menu(menu_path, human_delay_speed=delay)

        if not success:
            carb.log_info(
                f"[menu_click_with_retry] navigation failed on attempt " f"{i + 1}/{len(delays)} for '{menu_path}'"
            )
            continue

        if window_name:
            if (window := ui_test.find(window_name)) is not None:
                carb.log_info(
                    f"[menu_click_with_retry] window '{window_name}' found " f"on attempt {i + 1}/{len(delays)}"
                )
                return window
            carb.log_info(
                f"[menu_click_with_retry] window '{window_name}' not found " f"on attempt {i + 1}/{len(delays)}"
            )
        else:
            carb.log_info(f"[menu_click_with_retry] succeeded on attempt " f"{i + 1}/{len(delays)} for '{menu_path}'")
            for _ in range(wait_n_frames):
                await omni.kit.app.get_app().next_update_async()
            return None

    carb.log_info(f"[menu_click_with_retry] all attempts exhausted for '{menu_path}'")
    return None


def list_menu_paths(max_depth: int = 3) -> list[str]:
    """Return all menu item paths from the live menubar up to *max_depth* levels.

    Walks the widget tree without opening any menus.  Returns slash-separated
    paths suitable for use with :func:`menu_click_with_retry`.

    Args:
        max_depth: Maximum recursion depth (1 = top-level names only,
            2 = one level of submenus, etc.).

    Returns:
        Sorted list of all discoverable menu paths.

    Example:

    .. code-block:: python

        >>> from isaacsim.test.utils import list_menu_paths
        >>>
        >>> paths = list_menu_paths()
        >>> for p in paths:
        ...     print(p)
        Create/Lights/Cylinder Light
        Create/Mesh/Capsule
        File/New
        File/Open
        ...
    """
    try:
        menubar = get_menubar()
    except Exception:
        return []
    if menubar is None:
        return []

    paths: list[str] = []

    def _walk(widget_ref, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        for child in widget_ref.find_all("*"):
            name = getattr(child.widget, "text", None)
            if not name:
                continue
            path = f"{prefix}/{name}" if prefix else name
            children = child.find_all("*")
            if children:
                _walk(child, path, depth + 1)
            else:
                paths.append(path)

    _walk(menubar, "", 1)
    return sorted(paths)


def get_all_menu_paths(menu_dict: dict, current_path: str = "", root_path: str = "") -> list[str]:
    """Extract all leaf menu paths from a menu dictionary structure.

    This function recursively traverses a menu dictionary (as returned by
    `omni.kit.ui_test.get_context_menu()`) and extracts all leaf menu item paths.

    Args:
        menu_dict: The menu dictionary structure from get_context_menu.
        current_path: The current path prefix (used for recursion).
        root_path: Optional prefix to prepend to all returned paths.

    Returns:
        A list of all menu paths as strings joined by forward slashes.

    Example:

    .. code-block:: python

        >>> from isaacsim.test.utils import get_all_menu_paths
        >>>
        >>> menu_dict = {"Lidar": {"_": ["Sensor A", "Sensor B"]}}
        >>> paths = get_all_menu_paths(menu_dict, root_path="Create/Sensors")
        >>> paths
        ['Create/Sensors/Lidar/Sensor A', 'Create/Sensors/Lidar/Sensor B']
    """
    paths = []
    for key, value in menu_dict.items():
        # The "_" key contains leaf items at the current level
        if key == "_":
            if isinstance(value, list):
                for item in value:
                    path = f"{current_path}/{item}" if current_path else item
                    paths.append(f"{root_path}/{path}" if root_path else path)
            elif isinstance(value, str):
                path = f"{current_path}/{value}" if current_path else value
                paths.append(f"{root_path}/{path}" if root_path else path)
        elif isinstance(value, dict):
            new_path = f"{current_path}/{key}" if current_path else key
            paths.extend(get_all_menu_paths(value, new_path, root_path))
        elif isinstance(value, list):
            for item in value:
                path = f"{current_path}/{key}/{item}" if current_path else f"{key}/{item}"
                paths.append(f"{root_path}/{path}" if root_path else path)
        elif isinstance(value, str):
            path = f"{current_path}/{key}/{value}" if current_path else f"{key}/{value}"
            paths.append(f"{root_path}/{path}" if root_path else path)
    return paths


def count_menu_items(menu_dict: dict) -> int:
    """Recursively count the total number of leaf items in a menu dictionary.

    Args:
        menu_dict: The menu dictionary structure from get_context_menu.

    Returns:
        The total number of leaf menu items.

    Example:

    .. code-block:: python

        >>> from isaacsim.test.utils import count_menu_items
        >>>
        >>> menu_dict = {"Sensors": {"_": ["Contact", "IMU"]}, "Robots": {"_": ["Franka"]}}
        >>> count_menu_items(menu_dict)
        3
    """
    count = 0
    for key, item in menu_dict.items():
        if isinstance(item, dict):
            count += count_menu_items(item)
        elif isinstance(item, list):
            count += len(item)
    return count
