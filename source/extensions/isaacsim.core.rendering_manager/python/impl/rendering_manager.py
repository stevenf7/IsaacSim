# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from __future__ import annotations

import asyncio
import re
import time
import weakref

import carb
import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import omni.kit.app
import omni.kit.loop._loop as kit_loop
import omni.kit.viewport.utility
import omni.kit.viewport.window
import omni.timeline
import omni.usd
from pxr import Gf, Sdf, Usd, UsdGeom, UsdRender

_SETTING_PLAY_SIMULATION = "/app/player/playSimulations"
_SETTING_RATE_LIMIT_ENABLED = "/app/runLoops/main/rateLimitEnabled"
_SETTING_RATE_LIMIT_FREQUENCY = "/app/runLoops/main/rateLimitFrequency"

from enum import Enum


class RenderingEvent(Enum):
    """Rendering event types."""

    NEW_FRAME = "isaacsim.rendering.new_frame"
    """Event triggered when a new frame is rendered."""


class RenderingManager:
    """Core class that provides APIs for managing viewports and controlling rendering."""

    _app = omni.kit.app.get_app()
    _callbacks = dict()
    _callback_registry = 0
    _carb_settings = carb.settings.get_settings()
    _event_dispatcher = carb.eventdispatcher.get_eventdispatcher()
    _loop_runner = kit_loop.acquire_loop_interface()
    _timeline = omni.timeline.get_timeline_interface()

    @classmethod
    def render(cls) -> None:
        """Render the stage.

        This method performs an app update without stepping the simulation or physics.

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>>
            >>> RenderingManager.render()
        """
        play_simulation = cls._carb_settings.get_as_bool(_SETTING_PLAY_SIMULATION)
        if play_simulation:
            cls._carb_settings.set_bool(_SETTING_PLAY_SIMULATION, False)
        cls._app.update()
        if play_simulation:
            cls._carb_settings.set_bool(_SETTING_PLAY_SIMULATION, True)

    @classmethod
    async def render_async(cls) -> None:
        """Render the stage.

        This method is the asynchronous version of :py:meth:`render`.
        """
        play_simulation = cls._carb_settings.get_as_bool(_SETTING_PLAY_SIMULATION)
        if play_simulation:
            cls._carb_settings.set_bool(_SETTING_PLAY_SIMULATION, False)
        await cls._app.next_update_async()
        if play_simulation:
            cls._carb_settings.set_bool(_SETTING_PLAY_SIMULATION, True)

    @classmethod
    def set_dt(cls, dt: float) -> None:
        """Set the rendering dt.

        Args:
            dt: Rendering dt.

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>>
            >>> RenderingManager.set_dt(1 / 120.0)  # 120 Hz
        """

        def _set_rate_limit_frequency(frequency):
            cls._carb_settings.set_bool(_SETTING_RATE_LIMIT_ENABLED, True)
            cls._carb_settings.set_float(_SETTING_RATE_LIMIT_FREQUENCY, frequency)
            cls._timeline.set_target_framerate(frequency)

        frequency = 1.0 / dt
        # Set the rate limit only if it is enabled.
        # Otherwise, run the app as fast as possible without specifying a target rate
        if cls._carb_settings.get_as_bool(_SETTING_RATE_LIMIT_ENABLED):
            _set_rate_limit_frequency(frequency)
        # Set the stage's `timeCodesPerSecond` value
        stage = stage_utils.get_current_stage(backend="usd")
        with Usd.EditContext(stage, stage.GetRootLayer()):
            stage.SetTimeCodesPerSecond(frequency)
        cls._timeline.set_time_codes_per_second(frequency)
        # Set Isaac Sim's loop runner-specific configuration. If it is not available, fall back to the app settings
        if hasattr(cls._loop_runner, "set_manual_step_size") and hasattr(cls._loop_runner, "set_manual_mode"):
            cls._loop_runner.set_manual_step_size(dt)
            cls._loop_runner.set_manual_mode(True)
        else:
            carb.log_warn(f"Isaac Sim's loop runner not found. Setting a rate limit instead ({frequency} Hz)")
            _set_rate_limit_frequency(frequency)

    @classmethod
    def get_dt(cls) -> float:
        """Get the rendering dt.

        Returns:
            Rendering dt.

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>>
            >>> RenderingManager.get_dt()
            0.0166666...
        """

        def _get_rate_limit_dt():
            frequency = cls._carb_settings.get_as_float(_SETTING_RATE_LIMIT_FREQUENCY)
            return 1.0 / frequency if frequency else 0.0

        # Read from the app settings only if the rate limit is enabled in the first instance
        if cls._carb_settings.get_as_bool(_SETTING_RATE_LIMIT_ENABLED):
            return _get_rate_limit_dt()
        # Read from Isaac Sim's loop runner-specific configuration. If it is not available, fall back to the app settings
        if hasattr(cls._loop_runner, "get_manual_step_size") and hasattr(cls._loop_runner, "get_manual_mode"):
            if cls._loop_runner.get_manual_mode():
                return cls._loop_runner.get_manual_step_size()
        return _get_rate_limit_dt()

    @classmethod
    def register_callback(cls, event: RenderingEvent, *, callback: callable, order: int = 0) -> int:
        """Register/subscribe a callback to be triggered when a specific rendering event occurs.

        Args:
            event: The rendering event to subscribe to.
            callback: The callback function.
            order: The subscription order.
                Callbacks registered within the same order will be triggered in the order they were registered.

        Returns:
            The unique identifier of the callback subscription.

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingEvent, RenderingManager
            >>>
            >>> def callback(event, *args, **kwargs):
            ...     print(event)
            ...
            >>> # subscribe to the NEW_FRAME event
            >>> callback_id = RenderingManager.register_callback(RenderingEvent.NEW_FRAME, callback=callback)
            >>> callback_id
            0
            >>> # perform a rendering step in order to trigger the callback and print the event
            >>> RenderingManager.render()  # doctest: +NO_CHECK
            <carb.eventdispatcher._eventdispatcher.Event object at 0x...>
            >>>
            >>> # deregister all callbacks
            >>> RenderingManager.deregister_all_callbacks()
        """
        if event not in RenderingEvent:
            raise ValueError(f"Invalid rendering event: {event}. Supported events are: {list(RenderingEvent)}")
        # check for weak reference support (when the callback is a method of a class)
        if hasattr(callback, "__self__"):
            on_event = lambda event, obj=weakref.proxy(callback.__self__): getattr(obj, callback.__name__)(event)
        else:
            on_event = callback
        # get a unique id for the callback
        uid = cls._callback_registry
        cls._callback_registry += 1
        # register the callback
        if event in [RenderingEvent.NEW_FRAME]:
            cls._callbacks[uid] = cls._event_dispatcher.observe_event(
                observer_name=f"isaacsim.core.rendering_manager:callback.{event.value}.{uid}",
                event_name=omni.usd.get_context().stage_rendering_event_name(
                    omni.usd.StageRenderingEventType.NEW_FRAME, True
                ),
                on_event=on_event,
                order=order,
            )
        else:
            raise RuntimeError(f"Unable to register callback for event '{event}' with uid '{uid}'")
        return uid

    @classmethod
    def deregister_callback(cls, uid: int) -> None:
        """Deregister a callback registered via :py:meth:`register_callback`.

        Args:
            uid: The unique identifier of the callback to deregister. If the unique identifier does not exist
                or has already been deregistered, a warning is logged and the method does nothing.

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>>
            >>> # deregister the callback with the unique identifier 0
            >>> RenderingManager.deregister_callback(0)
        """
        if uid not in cls._callbacks:
            carb.log_warn(f"Unable to deregister callback with uid '{uid}'. It might have been already deregistered")
            return
        del cls._callbacks[uid]

    @classmethod
    def deregister_all_callbacks(cls) -> None:
        """Deregister all callbacks registered via :py:meth:`register_callback`.

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>>
            >>> RenderingManager.deregister_all_callbacks()
        """
        cls._callbacks.clear()

    @classmethod
    def wait_for_viewport(
        cls, *, viewport: str | "ViewportAPI" | None = None, max_frames: int = 60, sleep_time: float = 0.02
    ) -> tuple[bool, int]:
        """Wait for the viewport to be ready.

        Calling this method ensures that a new frame is rendered by the viewport during an app update (or rendering step).

        Args:
            viewport: The viewport to wait for. If not provided, the active viewport is used.
                See :py:meth:`get_viewport_api` for supported viewport sources.
            max_frames: The maximum number of frames to wait for.
            sleep_time: Time, in seconds, to sleep between frames.
                Setting a positive value reduces the number of frames required for the viewport to be ready.

        Returns:
            A tuple containing a boolean indicating whether the viewport is ready and the number of frames waited for.

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>>
            >>> RenderingManager.wait_for_viewport()
            (True, 0)
        """
        viewport = cls.get_viewport_api(viewport)
        if not viewport:
            return False, 0
        is_viewport_ready = lambda: viewport.frame_info.get("viewport_handle") is not None
        for i in range(max_frames):
            if is_viewport_ready():
                return True, i
            cls.render()
            if sleep_time > 0:
                time.sleep(sleep_time)
        return is_viewport_ready(), max_frames

    @classmethod
    async def wait_for_viewport_async(
        cls, *, viewport: str | "ViewportAPI" | None = None, max_frames: int = 60, sleep_time: float = 0.02
    ) -> tuple[bool, int]:
        """Wait for the viewport to be ready.

        This method is the asynchronous version of :py:meth:`wait_for_viewport`.

        Args:
            viewport: The viewport to wait for. If not provided, the active viewport is used.
                See :py:meth:`get_viewport_api` for supported viewport sources.
            max_frames: The maximum number of frames to wait for.
            sleep_time: Time, in seconds, to sleep between frames.
                Setting a positive value reduces the number of frames required for the viewport to be ready.

        Returns:
            A tuple containing a boolean indicating whether the viewport is ready and the number of frames waited for.
        """
        viewport = cls.get_viewport_api(viewport)
        if not viewport:
            return False, 0
        is_viewport_ready = lambda: viewport.frame_info.get("viewport_handle") is not None
        for i in range(max_frames):
            if is_viewport_ready():
                return True, i
            await cls.render_async()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        return is_viewport_ready(), max_frames

    @classmethod
    def set_camera(
        cls,
        camera: str | Usd.Prim | UsdGeom.Camera,
        *,
        render_product_or_viewport: str | Usd.Prim | UsdRender.Product | "ViewportAPI" | None = None,
    ) -> None:
        """Set a render product or viewport's camera.

        .. list-table:: Available Omniverse Kit cameras:
            :header-rows: 1
            * - Camera view
              - USD path (on session layer)
            * - Perspective view
              - ``/OmniverseKit_Persp``
            * - Top view
              - ``/OmniverseKit_Top``
            * - Front view
              - ``/OmniverseKit_Front``
            * - Right view
              - ``/OmniverseKit_Right``

        Args:
            camera: The camera to set.
            render_product_or_viewport: The render product or viewport to set the camera for.
                If not provided, the active viewport is used.
                See :py:meth:`get_viewport_api` or :py:meth:`get_render_product` for supported sources.

        Raises:
            ValueError: Invalid camera.
            ValueError: Invalid render product or viewport.

        Example:

        .. code-block:: python

            >>> import isaacsim.core.experimental.utils.stage as stage_utils
            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>>
            >>> # set the active viewport's camera to the top view
            >>> RenderingManager.set_camera("/OmniverseKit_Top")
            >>>
            >>> # set the active viewport's camera to a custom camera
            >>> camera = stage_utils.define_prim("/Camera", "Camera")
            >>> RenderingManager.set_camera(camera)
        """
        prim = prim_utils.get_prim_at_path(camera)
        if not prim.IsValid() or not prim.IsA(UsdGeom.Camera):
            raise ValueError(f"The camera ({camera}) is not a valid USD Camera prim")
        path = prim_utils.get_prim_path(prim)
        viewport = cls.get_viewport_api(render_product_or_viewport)
        if viewport is not None:
            viewport.camera_path = path
            return
        render_product = cls.get_render_product(render_product_or_viewport)
        if render_product is not None:
            stage = stage_utils.get_current_stage(backend="usd")
            with Usd.EditContext(stage, stage.GetSessionLayer()):
                render_product.GetCameraRel().SetTargets([path])
            return
        raise ValueError(
            f"Unable to set camera: unknown render product or viewport '{render_product_or_viewport}' ({type(render_product_or_viewport)})"
        )

    @classmethod
    def get_camera(
        cls, render_product_or_viewport: str | Usd.Prim | UsdRender.Product | "ViewportAPI" | None = None
    ) -> UsdGeom.Camera:
        """Get a render product or viewport's camera.

        Args:
            render_product_or_viewport: The render product or viewport to get the camera from.
                If not provided, the active viewport is used.

        Returns:
            USD Camera prim.

        Raises:
            ValueError: Invalid render product or viewport.
            ValueError: No camera prim target found for a given render product.

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>>
            >>> # get the camera of the active viewport
            >>> RenderingManager.get_camera()
            UsdGeom.Camera(Usd.Prim(</OmniverseKit_Persp>))
        """
        viewport = cls.get_viewport_api(render_product_or_viewport)
        if viewport is not None:
            return UsdGeom.Camera(prim_utils.get_prim_at_path(viewport.camera_path))
        render_product = cls.get_render_product(render_product_or_viewport)
        if render_product is not None:
            target = render_product.GetCameraRel().GetTargets()
            if not len(target):
                raise ValueError(f"Unable to get camera: no camera targets found for render product {render_product}")
            return UsdGeom.Camera(prim_utils.get_prim_at_path(target[0]))
        raise ValueError(
            f"Unable to get camera: unknown render product or viewport '{render_product_or_viewport}' ({type(render_product_or_viewport)})"
        )

    @classmethod
    def get_viewport_api(
        cls, render_product_or_viewport: str | Usd.Prim | UsdRender.Product | "ViewportAPI" | None = None
    ) -> "ViewportAPI" | None:
        """Get a viewport API (also identified as viewport) instance.

        Supported sources are:

        .. list-table::
            :header-rows: 1

            * - Source
              - Return value
            * - Unspecified (default)
              - The active viewport window's viewport API instance
            * - ``ViewportAPI`` instance
              - The given viewport API instance
            * - Viewport window title (name)
              - The given viewport window's viewport API instance

        Args:
            render_product_or_viewport: The render product or viewport to get the viewport API from.
                If not provided, the active viewport window is used.

        Returns:
            Viewport API instance (as a proxy), or None if no viewport API is found.

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>>
            >>> # get viewport API from the active viewport window
            >>> RenderingManager.get_viewport_api()
            <weakproxy at 0x... to ViewportAPI at 0x...>
            >>>
            >>> # get viewport API from a viewport window
            >>> RenderingManager.get_viewport_api("Viewport")
            <weakproxy at 0x... to ViewportAPI at 0x...>
        """
        # unspecified source
        if render_product_or_viewport is None:
            return omni.kit.viewport.utility.get_active_viewport()
        # viewport API
        elif "ViewportAPI" in render_product_or_viewport.__class__.__name__:
            return render_product_or_viewport
        # USD prim
        elif isinstance(render_product_or_viewport, Usd.Prim):
            return cls.get_viewport_api(render_product_or_viewport.GetPath().pathString)
        # Usd RenderProduct prim
        elif isinstance(render_product_or_viewport, UsdRender.Product):
            # TODO: get the viewport from the render product prim
            return None
        # str
        elif isinstance(render_product_or_viewport, (str, Sdf.Path)):
            render_product_or_viewport = (
                render_product_or_viewport.pathString
                if isinstance(render_product_or_viewport, Sdf.Path)
                else render_product_or_viewport
            )
            prim = prim_utils.get_prim_at_path(render_product_or_viewport)
            # valid USD prim
            if prim.IsValid():
                # render product
                if prim.IsA(UsdRender.Product):
                    render_product = UsdRender.Product(prim)
                    # TODO: get the viewport from the render product prim
                    return None
            # viewport name
            viewport_window = omni.kit.viewport.utility.get_active_viewport_window(render_product_or_viewport)
            if viewport_window is not None:
                return viewport_window.viewport_api
        return None

    @classmethod
    def get_render_product(
        cls, render_product_or_viewport: str | Usd.Prim | UsdRender.Product | "ViewportAPI" | None = None
    ) -> UsdRender.Product | None:
        """Get an USD RenderProduct prim that describes an artifact produced by a render.

        Supported sources are:

        .. list-table::
            :header-rows: 1

            * - Source
              - Return value
            * - Unspecified (default)
              - The active viewport's render product
            * - ``ViewportAPI`` instance
              - The given viewport's render product
            * - ``UsdRender.Product`` prim instance
              - The given prim instance
            * - USD RenderProduct prim path
              - The ``UsdRender.Product`` prim at the given path
            * - Viewport window title (name)
              - The given viewport window's render product

        Args:
            render_product_or_viewport: The render product or viewport to get the USD RenderProduct prim from.
                If not provided, the active viewport is used.

        Returns:
            USD RenderProduct prim, or None if no render product is found.

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>>
            >>> # get render product from the active viewport
            >>> RenderingManager.get_render_product()
            UsdRender.Product(Usd.Prim(</Render/OmniverseKit/HydraTextures/omni_kit_widget_viewport_ViewportTexture_0>))
            >>>
            >>> # get render product from a viewport API
            >>> viewport_api = RenderingManager.get_viewport_api()
            >>> RenderingManager.get_render_product(viewport_api)
            UsdRender.Product(Usd.Prim(</Render/OmniverseKit/HydraTextures/omni_kit_widget_viewport_ViewportTexture_0>))
            >>>
            >>> # get render product from a USD RenderProduct prim path
            >>> path = "/Render/OmniverseKit/HydraTextures/omni_kit_widget_viewport_ViewportTexture_0"
            >>> RenderingManager.get_render_product(path)
            UsdRender.Product(Usd.Prim(</Render/OmniverseKit/HydraTextures/omni_kit_widget_viewport_ViewportTexture_0>))
            >>>
            >>> # get render product from a viewport window
            >>> RenderingManager.get_render_product("Viewport")
            UsdRender.Product(Usd.Prim(</Render/OmniverseKit/HydraTextures/omni_kit_widget_viewport_ViewportTexture_0>))
        """
        # unspecified source
        if render_product_or_viewport is None:
            viewport = omni.kit.viewport.utility.get_active_viewport()
            if viewport is not None:
                return cls.get_render_product(viewport.render_product_path)
        # viewport
        elif "ViewportAPI" in render_product_or_viewport.__class__.__name__:
            return cls.get_render_product(render_product_or_viewport.render_product_path)
        # USD prim
        elif isinstance(render_product_or_viewport, Usd.Prim):
            return cls.get_render_product(render_product_or_viewport.GetPath().pathString)
        # Usd RenderProduct prim
        elif isinstance(render_product_or_viewport, UsdRender.Product):
            return render_product_or_viewport
        # str
        elif isinstance(render_product_or_viewport, (str, Sdf.Path)):
            render_product_or_viewport = (
                render_product_or_viewport.pathString
                if isinstance(render_product_or_viewport, Sdf.Path)
                else render_product_or_viewport
            )
            prim = prim_utils.get_prim_at_path(render_product_or_viewport)
            # valid USD prim
            if prim.IsValid():
                # render product
                if prim.IsA(UsdRender.Product):
                    return UsdRender.Product(prim)
            # viewport name
            viewport_window = omni.kit.viewport.utility.get_active_viewport_window(render_product_or_viewport)
            if viewport_window is not None and viewport_window.viewport_api is not None:
                return cls.get_render_product(viewport_window.viewport_api.render_product_path)
        return None

    @classmethod
    def get_resolution(
        cls, render_product_or_viewport: str | Usd.Prim | UsdRender.Product | "ViewportAPI" | None = None
    ) -> tuple[int, int]:
        """Get a render product or viewport's resolution: width x height.

        Args:
            render_product_or_viewport: The render product or viewport to get the resolution from.
                If not provided, the active viewport is used.
                See :py:meth:`get_viewport_api` or :py:meth:`get_render_product` for supported sources.

        Returns:
            Resolution as a tuple of width and height.

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>>
            >>> RenderingManager.get_resolution()
            (1280, 720)
        """
        viewport = cls.get_viewport_api(render_product_or_viewport)
        if viewport is not None:
            return viewport.resolution
        render_product = cls.get_render_product(render_product_or_viewport)
        if render_product is not None:
            return tuple(render_product.GetResolutionAttr().Get())
        raise ValueError(
            f"Unable to get resolution: unknown render product or viewport '{render_product_or_viewport}' ({type(render_product_or_viewport)})"
        )

    @classmethod
    def set_resolution(
        cls,
        resolution: tuple[int, int] | str,
        *,
        render_product_or_viewport: str | Usd.Prim | UsdRender.Product | "ViewportAPI" | None = None,
    ) -> None:
        """Set a render product or viewport's resolution: width x height.

        Args:
            resolution: The resolution as a tuple of width and height.
            render_product_or_viewport: The render product or viewport to set the resolution for.
                If not provided, the active viewport is used.
                See :py:meth:`get_viewport_api` or :py:meth:`get_render_product` for supported sources.

        Raises:
            ValueError: Invalid render product or viewport.

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>>
            >>> # set the active viewport's resolution to (640, 480)
            >>> RenderingManager.set_resolution((640, 480))
            >>>
            >>> # check the resolution
            >>> RenderingManager.get_resolution()
            (640, 480)
            >>> RenderingManager.get_viewport_api().resolution
            (640, 480)
        """
        viewport = cls.get_viewport_api(render_product_or_viewport)
        if viewport is not None:
            viewport.resolution = resolution
            return
        render_product = cls.get_render_product(render_product_or_viewport)
        if render_product is not None:
            stage = stage_utils.get_current_stage(backend="usd")
            with Usd.EditContext(stage, stage.GetSessionLayer()):
                render_product.GetResolutionAttr().Set(Gf.Vec2i(*resolution))
            return
        raise ValueError(
            f"Unable to set resolution: unknown render product or viewport '{render_product_or_viewport}' ({type(render_product_or_viewport)})"
        )

    @classmethod
    def create_viewport_window(
        cls,
        *,
        camera: str | Usd.Prim | UsdGeom.Camera = "/OmniverseKit_Persp",
        title: str | None = None,
        resolution: tuple[int, int] = (1280, 720),
    ) -> "ViewportWindow":
        """Create a viewport window.

        Args:
            camera: The camera to use for the viewport. If not provided, the default (perspective) camera is used.
            title: The viewport window title (name). If not provided, a default title is generated.
            resolution: The viewport window resolution: (width, height).

        Returns:
            The viewport window (as a proxy).

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>> import isaacsim.core.experimental.utils.stage as stage_utils
            >>>
            >>> # create a viewport window with the default camera and resolution
            >>> window = RenderingManager.create_viewport_window()
            >>> window.title
            'Viewport 1'
            >>> window.viewport_api.camera_path
            Sdf.Path('/OmniverseKit_Persp')
            >>>
            >>> # create a viewport window with a custom camera and resolution
            >>> camera = stage_utils.define_prim("/Camera", "Camera")
            >>> window = RenderingManager.create_viewport_window(
            ...     camera=camera,
            ...     resolution=(640, 480),
            ...     title="Custom Viewport",
            ... )
            >>> window.title
            'Custom Viewport'
            >>> window.viewport_api.camera_path
            Sdf.Path('/Camera')
            >>> window.viewport_api.resolution
            (640, 480)
        """
        if not title:
            title = f"Viewport {len(list(omni.kit.viewport.window.get_viewport_window_instances()))}"
        window = omni.kit.viewport.window.ViewportWindow(
            name=title, usd_context_name="", width=resolution[0], height=resolution[1]
        )
        cls.set_camera(camera, render_product_or_viewport=window.viewport_api)
        cls.set_resolution(resolution, render_product_or_viewport=window.viewport_api)
        return window

    @classmethod
    def get_viewport_windows(cls, *, include: list[str] = [".*"], exclude: list[str] = []) -> list:
        """Get viewport windows.

        Args:
            include: Viewport window titles (names) to get. If not provided, all viewport windows will be included.
                Regular expressions are supported.
            exclude: Viewport window titles (names) to exclude from getting. Excluded names take precedence over
                included names. Regular expressions are supported.

        Returns:
            List of viewport windows (as proxies).

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>>
            >>> # get all viewport windows
            >>> windows = RenderingManager.get_viewport_windows()
            >>> windows
            [<weakproxy at 0x... to ViewportWindow at 0x...>]
            >>> windows[0].title
            'Viewport'
            >>> windows[0].viewport_api.camera_path
            Sdf.Path('/OmniverseKit_Persp')
            >>> windows[0].viewport_api.resolution
            (1280, 720)
        """
        windows = []
        for window in omni.kit.viewport.window.get_viewport_window_instances():
            if window:
                title = window.title
                if any(re.fullmatch(pattern, title) for pattern in exclude):
                    continue
                if not any(re.fullmatch(pattern, title) for pattern in include):
                    continue
                windows.append(window)
        return windows

    @classmethod
    def destroy_viewport_windows(cls, *, include: list[str] = [".*"], exclude: list[str] = []) -> list[str]:
        """Destroy viewport windows.

        Args:
            include: Viewport window titles (names) to destroy. If not provided, all viewport windows will be destroyed.
                Regular expressions are supported.
            exclude: Viewport window titles (names) to exclude from destruction. Excluded names take precedence
                over included names. Regular expressions are supported.

        Returns:
            List of destroyed viewport window titles (names).

        Example:

        .. code-block:: python

            >>> from isaacsim.core.rendering_manager import RenderingManager
            >>>
            >>> # given the following viewport windows: "Viewport", "Viewport 1", and "Custom Viewport",
            >>> # destroy all viewport windows except the default one: "Viewport"
            >>> RenderingManager.destroy_viewport_windows(exclude=["Viewport"])
            ['Viewport 1', 'Custom Viewport']
        """
        destroyed_windows = []
        for window in cls.get_viewport_windows(include=include, exclude=exclude):
            destroyed_windows.append(window.title)
            window.destroy()
        return destroyed_windows
