"""Click a menu item by path with retry logic.

Uses isaacsim.test.utils.menu_utils.menu_click_with_retry which navigates
the menu hierarchy step-by-step with polling at each level.

Injected globals (via isaacsim_send.py --arg):
    menu_path: str — Slash-separated menu path (e.g. "File/New", "Create/Mesh/Cube").
    window_name: str — Optional window name to wait for after clicking (default: None).
    delays: str — Comma-separated delay values in frames (default: "5,10,20").
"""

# Defaults
if "menu_path" not in dir():
    raise ValueError("menu_path is required (e.g. --arg menu_path=File/New)")
if "window_name" not in dir():
    window_name = None  # noqa: F841
if "delays" not in dir():
    delays = "5,10,20"  # noqa: F841


async def _click():
    from isaacsim.test.utils.menu_utils import menu_click_with_retry

    delay_list = [int(d.strip()) for d in delays.split(",")]

    wn = window_name if window_name and window_name.lower() != "none" else None
    result = await menu_click_with_retry(menu_path, delays=delay_list, window_name=wn)

    if wn:
        if result is not None:
            print(f"Menu '{menu_path}' clicked, window '{wn}' found")
        else:
            print(f"Menu '{menu_path}' clicked, but window '{wn}' NOT found")
    else:
        print(f"Menu '{menu_path}' clicked")


await _click()
