# Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
r"""
In order to run this script make sure it is in the _build/windows-x86/release/scripts
directory (or whatever platform/config you are running) and call it.

To use async loading use (recommended):
.\omniverse-kit.exe --exec "screenshot.py -s omniverse://localhost/NVIDIA/Samples/Astronaut/Astro_USD.usd -o C:\Work\out_bbb.png --res_x 1024 --res_y 1024"

To use non-async loading use:
.\omniverse-kit.exe --/rtx/materialDb/syncLoads=true --/omni.kit.plugin/syncUsdLoads=true --exec "screenshot.py -s omniverse://localhost/NVIDIA/Samples/Astronaut/Astro_USD.usd -o C:\Work\out_bbb.png --res_x 1024 --res_y 1024"

The syncLoads and syncUsdLoads are absolutely required for Sync Mode! If you omit them,
you should pass the script --num_assets_loaded N, where N is however many
ASSETS_LOADED will be generated (you can set it to 99 and watch the console
output to find the correct number), that N is different for different types of scenes.

The default amount of ASSETS_LOADED for scenes with MDL is 2.

Discussions about ASSETS_LOADED are tracked in OM-13225

NOTE: For --camera_position and --camera_target, if the first component of the vector3 passed
is negative, you must use the --camera_position=x,y,z syntax rather than --camera_position x,y,z
syntax, otherwise you will get an error like error: argument -ct/--camera_target: expected one argument
"""

import argparse
import asyncio
import json
import os
import time
import urllib
from pathlib import Path

import carb
import omni

original_persistent_settings = {}
settings_interface = None
event_map = {}
for _val in dir(omni.usd.StageEventType):
    if _val.isupper():
        event_map[int(getattr(omni.usd.StageEventType, _val))] = _val


def omni_url_parser(url: str):
    res = urllib.parse.urlparse(url)

    username = os.getenv("OMNI_USER", default="test")
    password = os.getenv("OMNI_PASS", default=username)

    return res.netloc, username, password, res.path


def set_persistent_setting(name, value, type):
    global original_persistent_settings, settings_interface

    _orig = settings_interface.get(name)  # noqa
    original_persistent_settings[name] = {"value": _orig, "type": type}

    _set_settings_value(name, value, type)


def restore_persistent_settings():
    for name, _dict in original_persistent_settings.items():
        _set_settings_value(name, _dict["value"], _dict["type"])


def _set_settings_value(name, value, type):
    global settings_interface

    if type == "float":
        settings_interface.set_float(name, float(value))  # noqa
    elif type == "bool":
        settings_interface.set_bool(name, value)  # noqa


async def capture_next_frame(app, capture_file_path: str):
    """
    capture that works with old (editor-based) capture and new Kit 2.0 approach also
    """

    _editor = None
    _renderer = None
    _viewport_interface = None
    try:
        import omni.kit.editor

        _editor = omni.kit.editor.get_editor_interface()
    except ImportError as ie:

        try:
            import omni.kit.viewport_legacy
            import omni.renderer_capture
        except ImportError as ie:
            carb.log_error(f"*** screenshot: capture_next_frame: can't load {ie}")

        _renderer = omni.renderer_capture.acquire_renderer_capture_interface()
        _viewport_interface = omni.kit.viewport_legacy.acquire_viewport_interface()

    if _editor:
        _editor.capture_next_frame(capture_file_path)
        await app.next_update_async()
    else:
        viewport_ldr_rp = _viewport_interface.get_viewport_window(None).get_drawable_ldr_resource()
        _renderer.capture_next_frame_rp_resource(capture_file_path, viewport_ldr_rp)
        await app.next_update_async()
        _renderer.wait_async_capture()


async def main(args):
    global settings_interface

    app = omni.kit.app.get_app()
    settings_interface = carb.settings.get_settings()

    # set various settings that we require
    carb.log_info("*** screenshot.py: Setting app/renderer settings")
    settings_interface.set_float("/app/renderer/resolution/width", float(args.res_x))
    settings_interface.set_float("/app/renderer/resolution/height", float(args.res_y))
    set_persistent_setting("/persistent/app/captureFrame/viewport", not args.capture_app, "bool")
    if args.viewport_gizmos:
        set_persistent_setting("/persistent/app/viewport/displayOptions", 4095, "float")
    else:
        set_persistent_setting("/persistent/app/viewport/displayOptions", 0, "float")
    if args.hdr:
        settings_interface.set_bool("/app/captureFrame/hdr", True)
    await asyncio.sleep(1)

    # set search paths
    if args.mdl_path:
        current_sps = settings_interface.get("/renderer/mdl/searchPaths/local")
        settings_interface.set_string("/renderer/mdl/searchPaths/local", args.mdl_path + ";" + current_sps)

    syncloads = settings_interface.get("/rtx/materialDb/syncLoads") and settings_interface.get(
        "/omni.kit.plugin/syncUsdLoads"
    )

    _stage = args.stage
    if not os.path.exists(_stage):
        # in >=2020.2 there is no explicit connect call, so lets stat a file
        # to force the connection if it is a remote file
        res = await omni.client.stat_async(_stage)
        if res[0] != omni.client.Result.OK:
            carb.log_error(f"*** screenshot: Error calling stat on stage path, result: {res[0]}")
            # reset what we persisted
            restore_persistent_settings()
            app.post_quit()

    # setup asyncio.wait_for arg
    _timeout = None if not args.timeout else args.timeout

    carb.log_info(f"*** screenshot.py: Loading {args.stage}")
    try:
        load_time = await asyncio.wait_for(load_stage(_stage, syncloads, args.num_assets_loaded), _timeout)
    except RuntimeError as e:
        carb.log_error(f"*** screenshot.py: Stage load failure: {e}")
        # reset what we persisted
        restore_persistent_settings()
        app.post_quit()
        return
    except SystemExit as e:
        carb.log_error(f"*** screenshot.py: Stage load aborted: {e}")
        restore_persistent_settings()
        return
    except asyncio.TimeoutError:
        carb.log_error(f"*** screenshot.py: Timed out when waiting {_timeout} for the stage to load")
        restore_persistent_settings()
        app.post_quit()
        return
    carb.log_info(f"*** screenshot.py: scene loaded in {load_time}s")

    # 2020.3 (at some point)+
    viewport_window = omni.kit.viewport_legacy.get_default_viewport_window()

    if args.camera:
        viewport_window.set_active_camera(args.camera)

    if args.camera_position:
        viewport_window.set_active_camera("/OmniverseKit_Persp")
        _ = args.camera_position
        viewport_window.set_camera_position("/OmniverseKit_Persp", _[0], _[1], _[2], True)

    if args.camera_target:
        viewport_window.set_active_camera("/OmniverseKit_Persp")
        _ = args.camera_target
        viewport_window.set_camera_target("/OmniverseKit_Persp", _[0], _[1], _[2], True)

    # set the tonemapper, it gets reset on stage load so we have to set it here
    settings_interface.set_float("/rtx/post/tonemap/op", float(args.tonemapper))

    # sleep some user-defined seconds just to let the scene settle
    carb.log_info(f"*** screenshot.py: waiting {args.wait_after_load}s for the scene to settle")
    await asyncio.sleep(args.wait_after_load)

    await capture_next_frame(app, args.output)

    # need to wait a second or two for the screenshot to get written
    # await asyncio.sleep(1)
    carb.log_info(f"*** screenshot.py: screenshot captured to: {args.output}")

    # if we should measure FPS, lets do it now
    idle_fps = -1
    if args.measure_fps > 0:
        elapsed_time = 0
        frames = 0
        while True:
            dt = await app.next_update_async()
            elapsed_time += dt
            frames += 1
            if elapsed_time >= args.measure_fps:
                break
        idle_fps = frames / elapsed_time

    # measure the hot stage re-open time?
    hot_load_time = None
    if args.add_hot_load:
        carb.log_info(f"*** screenshot.py: Hot Loading {args.stage}")
        try:
            hot_load_time = await load_stage(_stage, syncloads, args.num_assets_loaded)
            carb.log_info(f"*** screenshot.py: scene loaded in {hot_load_time}s")
            await asyncio.sleep(1)
        except RuntimeError as e:
            carb.log_error(f"*** screenshot.py: Stage hot load failure: {e}")
            hot_load_time = -1

    # reset what we persisted
    restore_persistent_settings()

    if args.stats_file:
        stats_file = Path(args.stats_file)
        if stats_file.is_dir():
            carb.log_error(f"*** screenshot.py: stats_file must be a file, not a directory: {stats_file}")
        else:
            stats = {"load_time": load_time}
            if idle_fps >= 0:
                stats["idle_fps"] = idle_fps
            if hot_load_time:
                stats["hot_load_time"] = hot_load_time
            carb.log_info(f"*** screenshot.py: stats contents: {json.dumps(stats)}")
            stats_file.write_text(json.dumps(stats))
            carb.log_info(f"*** screenshot.py: wrote stats to: {stats_file}")

    # exit this guy
    app.post_quit()


async def stage_event_compat() -> int:
    """Calls `kit.stage_event` in a compatible way between versions"""
    # at some point in 2020.3 the APIs changed again
    usd_context = omni.usd.get_context()
    if hasattr(usd_context, "next_stage_event_async"):
        stage_event_fn = omni.usd.get_context().next_stage_event_async
    else:
        stage_event_fn = omni.kit.asyncapi.stage_event

    result = await stage_event_fn()
    # Old behaviour
    if isinstance(result, int):
        carb.log_info(f"*** screenshot.py: stage_event() -> {event_map[result]}")
        return result

    # New behaviour somewhere in 2020.3
    event, _ = result
    event = int(event)
    carb.log_info(f"*** screenshot.py: stage_event() -> ({event_map[event]}, {_})")
    return event


async def load_stage(stage_path: str, syncloads: bool, num_assets_loaded: int = 2):
    # at some point in 2020.3 the APIs changed again
    usd_context = omni.usd.get_context()
    if hasattr(usd_context, "open_stage_async"):
        open_stage_fn = omni.usd.get_context().open_stage_async
    else:
        open_stage_fn = omni.kit.asyncapi.open_stage

    # open_stage(_async) will wait for the stage to open, but will return
    # without waiting for MDLs to be loaded!
    start = time.time()

    success, explanation = await open_stage_fn(stage_path)
    carb.log_info(f"*** screenshot.py: Initial stage load success: {success}")
    if not success:
        raise RuntimeError(explanation)

    # we'll try to track all the ASSETS_LOADED events to figure out when the MDLs
    # are complete
    assets_loaded_count = 0
    required_assets_loaded = 1
    if not syncloads:
        required_assets_loaded = int(num_assets_loaded)

    if required_assets_loaded == 0:
        load_time = time.time() - start
        carb.log_info("*** screenshot.py: Not waiting for ASSETS LOADED at all, stage load complete.")
        return load_time

    carb.log_info(f"*** screenshot.py: Waiting for {required_assets_loaded} ASSETS LOADED event(s)")

    while True:
        event = await stage_event_compat()

        # TODO: compare to actual enum value when Kit fixes its return types
        if event == int(omni.usd.StageEventType.ASSETS_LOADED):
            assets_loaded_count += 1
            carb.log_info(f"*** screenshot.py: Received ASSETS_LOADED #{assets_loaded_count}")
            # The user can specify how many assets_loaded to wait for in async mode
            if assets_loaded_count < required_assets_loaded:
                continue
            carb.log_info(f"*** screenshot.py: Met threshold of {required_assets_loaded}, all assets loaded")
            break
        # error that something went wrong
        elif event == int(omni.usd.StageEventType.OPEN_FAILED):
            raise RuntimeError("Received OPEN_FAILED")
        elif event == int(omni.usd.StageEventType.ASSETS_LOAD_ABORTED):
            raise RuntimeError("Received ASSETS_LOAD_ABORTED")
        elif event == int(omni.usd.StageEventType.CLOSING):
            raise SystemExit("Received CLOSING")
        elif event == int(omni.usd.StageEventType.CLOSED):
            raise SystemExit("Received CLOSED")

    load_time = time.time() - start
    return load_time


async def safely_quit():
    # kit crashes if you quit too soon /shrug
    await asyncio.sleep(5)
    omni.kit.app.get_app_interface().post_quit()


if __name__ == "__main__":
    # how i love argparse, quick hack to support a --quit to just exit
    quit_parser = argparse.ArgumentParser()
    quit_parser.add_argument("-q", "--quit", action="store_true", required=False)
    quit_args = quit_parser.parse_known_args()
    if quit_args[0].quit:
        asyncio.ensure_future(safely_quit())
        exit()

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--stage", help="Full path to USD stage to render", required=True)
    parser.add_argument("-p", "--mdl_path", help="Additional MDL search paths if required")
    parser.add_argument("-x", "--res_x", help="Output image width", type=int, default=1024)
    parser.add_argument("-y", "--res_y", help="Output image height", type=int, default=1024)
    parser.add_argument("-o", "--output", help="Full path to the Output image", required=True)
    parser.add_argument("-c", "--camera", help="Optional SDF Path to Camera for rendering")
    parser.add_argument(
        "-cp",
        "--camera_position",
        help="Optional x,y,z string to set the " "Perspective Camera Position (takes precedence over --camera)",
        type=lambda s: [float(x) for x in s.split(",")],
    )
    parser.add_argument(
        "-ct",
        "--camera_target",
        help="Optional x,y,z string to set the Perspective Camera " "Target (takes precedence over --camera)",
        type=lambda s: [float(x) for x in s.split(",")],
    )
    parser.add_argument("--stats_file", help="Optional path to a JSON serialized stats file")
    parser.add_argument(
        "--num_assets_loaded",
        help="Optional amount of ASSETS_LOADED events for this stage (only for async mode)",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--wait_after_load",
        help="Amount of seconds to wait after the scene loads to let rendering settle",
        type=float,
        default=5,
    )
    parser.add_argument(
        "--hdr", help="Enable HDR output (output extension must be .exr)", required=False, action="store_true"
    )
    parser.add_argument(
        "--capture_app", help="Enable entire app output (just viewport by default)", required=False, action="store_true"
    )
    parser.add_argument(
        "--viewport_gizmos", help="Enable viewport gizmos (hidden by default)", required=False, action="store_true"
    )
    parser.add_argument(
        "--tonemapper",
        help="Optional index of tonemapper to use (1=Linear, 6=ACES, check Renderer "
        "settings for more values, defaults to ACES)",
        type=int,
        default=6,
    )
    parser.add_argument(
        "--measure_fps",
        help="Measure idle FPS after screenshot for N seconds (0=off, 0 by default)",
        type=float,
        default=0,
    )
    parser.add_argument(
        "--add_hot_load",
        help="Add hot load at the end of measurements (just re-open the stage immediately)",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "--timeout", help="Close Kit if the stage isn't loaded in this time", required=False, type=float, default=0
    )
    args = parser.parse_args()

    if args.camera_position:
        if len(args.camera_position) != 3:
            carb.log_error(
                f"*** screenshot.py: You must pass a string in the form x,y,z "
                f"for --camera_position (no spaces!) (you passed: {args.camera_position})"
            )
            omni.kit.app.get_app_interface().post_quit()

    if args.camera_target:
        if len(args.camera_target) != 3:
            carb.log_error(
                f"*** screenshot.py: You must pass a string in the form x,y,z "
                f"for --camera_target (no spaces!) (you passed: {args.camera_target})"
            )
            omni.kit.app.get_app_interface().post_quit()

    if args.hdr and not args.output.endswith(".exr"):
        carb.log_error(
            f"*** screenshot.py: You must use a .exr for the target " f"output in HDR mode (you passed: {args.output})"
        )
        omni.kit.app.get_app_interface().post_quit()

    else:
        asyncio.ensure_future(main(args))
