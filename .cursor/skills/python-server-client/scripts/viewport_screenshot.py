"""Capture a viewport screenshot and save it to disk.

Injected globals (via isaacsim_send.py --arg):
    output_path: str — File path for the output PNG (default: /tmp/viewport_capture.png)
"""

# Defaults (overridden by injected globals)
if "output_path" not in dir():
    output_path = "/tmp/viewport_capture.png"  # noqa: F841


async def _capture():
    from isaacsim.test.utils.image_capture import capture_viewport_screenshot_async

    await capture_viewport_screenshot_async(output_path)


await _capture()
