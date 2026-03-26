"""Capture a full-application screenshot (entire window including UI) and save to disk.

Uses omni.kit.renderer.capture swapchain capture. Works in both --no-window headless
and windowed modes.

Injected globals (via isaacsim_send.py --arg):
    output_path: str — File path for the output PNG (default: /tmp/app_capture.png).
"""

# Defaults
if "output_path" not in dir():
    output_path = "/tmp/app_capture.png"  # noqa: F841


async def _capture():
    from isaacsim.test.utils.image_capture import capture_app_screenshot_async

    await capture_app_screenshot_async(output_path)


await _capture()
